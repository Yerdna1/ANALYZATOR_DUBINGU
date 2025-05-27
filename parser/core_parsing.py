import logging
import re
from .constants import (
    COLUMN_HEADERS,
    P_SEGMENT_MARKER_FIND,
    P_TIMECODE_FIND,
    P_SCENE_KEYWORD_FIND,
    P_PARENS_MARKER_FIND,
    P_SPEAKER_MARKER_IN_TEXT,
    P_COMMA_SEPARATOR,
    P_SCRIPT_START_MARKER,
    P_LIKELY_DIALOGUE_SEP,
    SPEAKER_BASE,
    SPEAKER_PATTERN,
    SPEAKER_BASE_FALLBACK,
    SPEAKER_PATTERN_FALLBACK,
    P_MULTI_SPEAKER_TEXT_FALLBACK,
    P_SPEAKER_MARKER_FALLBACK,
    P_SPEAKER_DASH_FALLBACK,
    P_SPEAKER_COLON_FALLBACK,
    P_SPEAKER_SIMPLE_FALLBACK
)
from .speaker_processing import clean_speaker_name, extract_speaker_list

_log = logging.getLogger(__name__)

def parse_chunks_to_structured_data(chunks: list[str]) -> list[dict[str, str]]:
    """
    Parses lines using hybrid speaker detection (list prioritized, pattern fallback).
    Includes fallback for multi-speaker lines not in list.

    Args:
        chunks: A list of text chunks.

    Returns:
        A list of dictionaries representing rows.
    """
    parsed_rows = []
    segment_marker_count = 0
    current_segment = 0
    speaker_list = extract_speaker_list(chunks)
    use_speaker_list = bool(speaker_list)

    P_MULTI_SPEAKER_PREFIX_LIST = None
    P_SPEAKER_FIND_LIST = None # Define pattern for single speaker list search
    if use_speaker_list:
        _log.info(f"Using speaker list for detection (priority): {speaker_list}")
        speaker_pattern_str = "|".join(re.escape(s) for s in speaker_list)
        P_SPEAKER_FIND_LIST_PART = rf"({speaker_pattern_str}):*"
        P_MULTI_SPEAKER_PREFIX_LIST = re.compile(rf"^({P_SPEAKER_FIND_LIST_PART}(?:,\s*{P_SPEAKER_FIND_LIST_PART})+)\s+(.*)")
        # Compile single speaker pattern from list here
        P_SPEAKER_FIND_LIST = re.compile(rf"(?<!\w)({speaker_pattern_str}):*\b")
    else:
        _log.error("Could not extract speaker list. Relying on fallback patterns.")


    for chunk_idx, chunk in enumerate(chunks):
        _log.debug(f"--- Parsing Chunk {chunk_idx} ---")
        lines = chunk.splitlines()
        for line_idx, line in enumerate(lines):
            original_line = line.strip()
            if not original_line: continue

            is_segment_marker_line = False
            if P_SEGMENT_MARKER_FIND.search(original_line):
                segment_marker_count += 1
                current_segment = segment_marker_count
                is_segment_marker_line = True
                _log.info(f"Line {line_idx}: Found segment marker sequence. Incrementing segment count to: {current_segment}")

            row_data = {header: "" for header in COLUMN_HEADERS}
            row_data["Segment"] = str(current_segment)
            if is_segment_marker_line: row_data["Segment Marker"] = str(current_segment)

            remaining_text = original_line
            found_spans = []
            speakers_found_on_line = []
            speaker_detection_method = "None"
            speaker_span = None
            text_after_speaker = remaining_text

            # 1. Timecodes
            timecodes = []
            for match in P_TIMECODE_FIND.finditer(remaining_text):
                timecodes.append(match.group(1))
                found_spans.append((*match.span(), "Timecode"))
            if timecodes: row_data["Timecode"] = " ".join(timecodes)

            # --- Speaker Detection ---
            text_for_speaker_search = remaining_text
            for start, end, type in sorted(found_spans, key=lambda x: x[0]):
                 if type == "Timecode": text_for_speaker_search = text_for_speaker_search.replace(remaining_text[start:end], " " * (end - start), 1)
            text_for_speaker_search = text_for_speaker_search.lstrip()
            start_offset = len(remaining_text) - len(text_for_speaker_search)

            # 2a. Try List - Multi-speaker
            multi_match_list = None
            if use_speaker_list and P_MULTI_SPEAKER_PREFIX_LIST:
                 multi_match_list = P_MULTI_SPEAKER_PREFIX_LIST.match(text_for_speaker_search)

            if multi_match_list:
                 speaker_list_str = multi_match_list.group(1)
                 text_after_speaker = multi_match_list.group(multi_match_list.lastindex)
                 # Use findall with the specific list pattern to extract speakers accurately
                 if P_SPEAKER_FIND_LIST: # Check if pattern was compiled
                     speakers_found_on_line = [clean_speaker_name(match.group(1)) for match in P_SPEAKER_FIND_LIST.finditer(speaker_list_str)]
                 else: # Fallback split if pattern failed (shouldn't happen)
                     speakers_found_on_line = [clean_speaker_name(s) for s in speaker_list_str.split(',')]

                 speaker_detection_method = "List-Multi"
                 speaker_span = (start_offset, multi_match_list.end(1) + start_offset)
                 _log.debug(f"Line {line_idx}: Found MULTIPLE speakers (List): {speakers_found_on_line}")

            # 2b. Try List - Single Speaker
            elif use_speaker_list:
                 for known_speaker in speaker_list:
                      if text_for_speaker_search.startswith(known_speaker):
                           end_pos = len(known_speaker)
                           if end_pos == len(text_for_speaker_search) or not text_for_speaker_search[end_pos].isalnum():
                                speakers_found_on_line.append(clean_speaker_name(known_speaker)) # Clean name here
                                speaker_detection_method = "List-Single"
                                speaker_span = (start_offset, end_pos + start_offset)
                                text_after_speaker = text_for_speaker_search[end_pos:].lstrip()
                                _log.debug(f"Line {line_idx}: Found SINGLE speaker (List): {known_speaker}")
                                break

            # 2c. Fallback - Multi-speaker Pattern
            if not speakers_found_on_line:
                 multi_match_fallback = P_MULTI_SPEAKER_TEXT_FALLBACK.match(text_for_speaker_search)
                 if multi_match_fallback:
                      speaker_list_str = multi_match_fallback.group(1)
                      text_after_speaker = multi_match_fallback.group(multi_match_fallback.lastindex)
                      temp_speaker_pattern = re.compile(rf"({SPEAKER_BASE_FALLBACK}):*")
                      speakers_found_on_line = [clean_speaker_name(match.group(1)) for match in temp_speaker_pattern.finditer(speaker_list_str)]
                      speaker_detection_method = "Pattern-Multi-Fallback"
                      speaker_span = (start_offset, multi_match_fallback.end(1) + start_offset)
                      _log.debug(f"Line {line_idx}: Found MULTIPLE speakers (Fallback Pattern): {speakers_found_on_line}")

            # 2d. Fallback - Single Speaker Patterns
            if not speakers_found_on_line:
                 single_match = P_SPEAKER_MARKER_FALLBACK.match(text_for_speaker_search)
                 if single_match: speaker_detection_method = "Pattern-Marker"
                 if not single_match:
                      single_match = P_SPEAKER_DASH_FALLBACK.match(text_for_speaker_search)
                      if single_match: speaker_detection_method = "Pattern-Dash"
                 if not single_match:
                      single_match = P_SPEAKER_COLON_FALLBACK.match(text_for_speaker_search)
                      if single_match: speaker_detection_method = "Pattern-Colon"
                 if not single_match:
                      single_match = P_SPEAKER_SIMPLE_FALLBACK.match(text_for_speaker_search)
                      if single_match: speaker_detection_method = "Pattern-Simple"

                 if single_match:
                      speaker_raw = single_match.group(1)
                      text_after_speaker = single_match.group(single_match.lastindex)
                      # *** Call clean_speaker_name ***
                      speaker_name = clean_speaker_name(speaker_raw)
                      if len(speaker_name) < 50 and speaker_name not in ["INT.", "EXT.", "TITULOK"]:
                           speakers_found_on_line.append(speaker_name)
                           speaker_span = (single_match.start(1) + start_offset, single_match.end(1) + start_offset)
                           _log.debug(f"Line {line_idx}: Found SINGLE speaker ({speaker_detection_method}): {speaker_name}")
                      else:
                           speaker_detection_method = "None"
                           text_after_speaker = text_for_speaker_search
                           speaker_span = None

            if speaker_span: found_spans.append((*speaker_span, "Speaker"))

            remaining_text = text_after_speaker.strip()

            # 3. Scene Markers
            scene_markers = []
            temp_text_for_scene = remaining_text
            keyword_match = P_SCENE_KEYWORD_FIND.search(temp_text_for_scene)
            if keyword_match:
                 original_start = original_line.find(keyword_match.group(0))
                 if original_start != -1:
                      overlaps_speaker = any(max(span[0], original_start) < min(span[1], len(original_line)) and span[2] == "Speaker" for span in found_spans)
                      if not overlaps_speaker:
                           marker_text = original_line[original_start:]
                           scene_markers.append(marker_text.strip())
                           found_spans.append((original_start, len(original_line), "Scene Marker"))
                           _log.debug(f"Line {line_idx}: Found Scene Keyword Marker: {marker_text.strip()}")

            for match in P_PARENS_MARKER_FIND.finditer(original_line):
                 is_covered = any(span[0] <= match.start() and span[1] >= match.end() for span in found_spans if span != match.span())
                 if not is_covered:
                      scene_markers.append(match.group(1))
                      found_spans.append((*match.span(), "Scene Marker"))
                      _log.debug(f"Line {line_idx}: Found Parenthetical Marker: {match.group(1)}")

            if scene_markers: row_data["Scene Marker"] = " ".join(sorted(list(set(scene_markers)), key=original_line.find))

            # --- Determine Final Remaining Text ---
            final_text = remaining_text
            if row_data["Scene Marker"]:
                 for marker in scene_markers:
                      if marker.startswith("(") and marker.endswith(")"): final_text = final_text.replace(marker, "")
                 if keyword_match:
                      if final_text.strip() == scene_markers[0]: final_text = ""

            marker_match = P_SPEAKER_MARKER_IN_TEXT.match(final_text.strip())
            if marker_match: final_text = final_text.replace(marker_match.group(1), '', 1).strip()

            row_data["Text"] = final_text.strip()
            _log.debug(f"Line {line_idx}: Assigned Final Text: {repr(row_data['Text'])}")

            # --- Handle Row Output ---
            if len(speakers_found_on_line) > 1:
                 for sp in speakers_found_on_line:
                      multi_row = row_data.copy(); multi_row["Speaker"] = sp; multi_row["Text"] = row_data["Text"]; parsed_rows.append(multi_row)
                 _log.debug(f"Line {line_idx}: Created {len(speakers_found_on_line)} rows for multiple speakers ({speaker_detection_method}).")
            elif len(speakers_found_on_line) == 1:
                 row_data["Speaker"] = speakers_found_on_line[0]
                 if not (is_segment_marker_line and not row_data["Speaker"] and not row_data["Timecode"] and not row_data["Text"] and not row_data["Scene Marker"]): parsed_rows.append(row_data)
            else: # No speaker found
                 if not (is_segment_marker_line and not row_data["Speaker"] and not row_data["Timecode"] and not row_data["Text"] and not row_data["Scene Marker"]): parsed_rows.append(row_data)

    return parsed_rows
