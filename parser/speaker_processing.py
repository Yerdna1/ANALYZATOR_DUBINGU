import logging
from .constants import (
    COLUMN_HEADERS,
    P_SCRIPT_START_MARKER,
    P_LIKELY_DIALOGUE_SEP,
    SPEAKER_BASE_FALLBACK,
    SPEAKER_PATTERN_FALLBACK,
    P_MULTI_SPEAKER_TEXT_FALLBACK,
    P_SPEAKER_MARKER_FALLBACK,
    P_SPEAKER_DASH_FALLBACK,
    P_SPEAKER_COLON_FALLBACK,
    P_SPEAKER_SIMPLE_FALLBACK
)

_log = logging.getLogger(__name__)

def clean_speaker_name(name: str) -> str:
    """Validates and cleans speaker names according to rules:
    - Removes trailing colons
    - Requires minimum 2 capital letters per word
    - Excludes scene markers
    - Handles single-letter suffixes
    """
    name = name.strip()
    
    # Remove trailing colons
    if name.endswith("::"):
        name = name[:-2].strip()
    elif name.endswith(":"):
        name = name[:-1].strip()
    
    # Skip scene markers
    if name in ["INT", "EXT", "TITULOK"]:
        return ""
        
    # Handle single-letter suffixes (e.g. "JAN V" becomes "JAN")
    if ' ' in name:
        parts = name.split()
        if len(parts[-1]) == 1 and parts[-1].isupper():
            name = ' '.join(parts[:-1])
    
    # Validate name meets requirements
    words = name.split()
    for word in words:
        # Count capital letters (including accented)
        capitals = sum(1 for c in word if c.isupper() or c in "ÁČĎÉÍĹĽŇÓŔŠŤÚÝŽ")
        if capitals < 2:
            return ""
    
    return name if len(name) >= 3 else ""


def extract_speaker_list(chunks: list[str]) -> list[str]:
    """
    Extracts speaker list from 'Postavy:' section. Ignores empty lines within list.
    Stops only when a script start marker is found or max lines reached.
    """
    speakers = []
    in_postavy_section = False
    lines_checked = 0
    max_lines_to_check = 500

    for chunk in chunks:
        lines = chunk.splitlines()
        for line in lines:
            lines_checked += 1
            line_strip = line.strip()

            if not in_postavy_section and "Postavy:" in line:
                in_postavy_section = True
                _log.info("Found 'Postavy:' section.")
                continue

            if in_postavy_section:
                if P_SCRIPT_START_MARKER.match(line_strip):
                    _log.info(f"End of 'Postavy:' section detected (script start marker). Found {len(speakers)} speakers.")
                    unique_speakers = sorted(list(set(s.strip() for s in speakers if s.strip())), key=len, reverse=True)
                    _log.info(f"Final extracted speaker list (sorted): {unique_speakers}")
                    return unique_speakers

                if line_strip:
                    if line_strip[0].isupper() and not P_LIKELY_DIALOGUE_SEP.search(line_strip):
                        cleaned_name = line_strip.rstrip(':').strip()
                        # Split at first space if followed by single letter
                        if ' ' in cleaned_name:
                            parts = cleaned_name.split(' ', 1)
                            if len(parts[1]) == 1:  # Single letter suffix
                                cleaned_name = parts[0]  # Take only base name

                        if cleaned_name and len(cleaned_name) > 2 and len(cleaned_name) < 50:
                            speakers.append(cleaned_name)
                            _log.info(f"Added potential speaker: {cleaned_name}")
                        else:
                             _log.debug(f"Skipping potential speaker line (too long or empty after clean): {repr(line_strip)}")
                    else:
                        _log.debug(f"Skipping potential speaker line (doesn't look like name): {repr(line_strip)}")

            if lines_checked > max_lines_to_check:
                _log.warning(f"Stopped searching for 'Postavy:' after {max_lines_to_check} lines.")
                unique_speakers = sorted(list(set(s.strip() for s in speakers if s.strip())), key=len, reverse=True)
                _log.info(f"Final extracted speaker list (sorted): {unique_speakers}")
                return unique_speakers

    if in_postavy_section:
         _log.warning("'Postavy:' section found but end marker not detected before EOF/limit.")
    else:
         _log.warning("'Postavy:' section not found.")

    unique_speakers = sorted(list(set(s.strip() for s in speakers if s.strip())), key=len, reverse=True)
    _log.info(f"Final extracted speaker list (sorted): {unique_speakers}")
    return unique_speakers
