import re

# Column Headers - Define here for consistency
COLUMN_HEADERS = ["Segment", "Speaker", "Timecode", "Text", "Scene Marker", "Segment Marker"]

# --- Regular Expression Patterns ---
P_SEGMENT_MARKER_FIND = re.compile(r"[-–—]{5,}")
P_TIMECODE_FIND = re.compile(r"((?:A\s*)?\b\d{2}:\d{2}(?::\d{2})?(?:-\s*\d{2}:\d{2}(?::\d{2})?)?\b)")
P_SCENE_KEYWORD_FIND = re.compile(r"(INT\.|EXT\.|TITULOK)\s*")
P_PARENS_MARKER_FIND = re.compile(r"(\(.*?\))")
P_SPEAKER_MARKER_IN_TEXT = re.compile(r"^\s*(\(.*\))\s*")
P_COMMA_SEPARATOR = re.compile(r"\s*,\s*")
P_SCRIPT_START_MARKER = re.compile(r"^\d{2}:\d{2}|^-{5,}|^A\s*\d{2}:\d{2}")
P_LIKELY_DIALOGUE_SEP = re.compile(r"\t|\s{2,}")

# -- Speaker Patterns --
SPEAKER_BASE = r"(?:[A-ZÁČĎÉÍĹĽŇÓŔŠŤÚÝŽ]{2,}[A-ZÁČĎÉÍĹĽŇÓŔŠŤÚÝŽa-záčďéíĺľňóŕšťúýž]*\s*)+\d?"
SPEAKER_PATTERN = rf"({SPEAKER_BASE}):*"

# -- Fallback Speaker Patterns (Used when NO list is extracted OR list match fails) --
SPEAKER_BASE_FALLBACK = r"(?:[A-ZÁČĎÉÍĹĽŇÓŔŠŤÚÝŽ]{2,}[A-ZÁČĎÉÍĹĽŇÓŔŠŤÚÝŽa-záčďéíĺľňóŕšťúýž]*\s*)+\d?"
SPEAKER_PATTERN_FALLBACK = rf"({SPEAKER_BASE_FALLBACK}):*"
# 1. Fallback Multi-speaker comma list followed by whitespace/tab and text
P_MULTI_SPEAKER_TEXT_FALLBACK = re.compile(rf"^({SPEAKER_PATTERN_FALLBACK}(?:,\s*{SPEAKER_PATTERN_FALLBACK})+)\s+(.*)")
# 2. Fallback Single speaker with (MARKER) followed by tab and text
P_SPEAKER_MARKER_FALLBACK = re.compile(rf"^{SPEAKER_PATTERN_FALLBACK}\s*(\(.*\))\s*\t(.*)")
# 3. Fallback Single speaker followed by dash/em-dash and text
P_SPEAKER_DASH_FALLBACK = re.compile(rf"^{SPEAKER_PATTERN_FALLBACK}\s*[-–—]\s*(.*)")
# 4. Fallback Single speaker followed by colon and text
P_SPEAKER_COLON_FALLBACK = re.compile(rf"^{SPEAKER_PATTERN_FALLBACK}:\s+(.*)")
# 5. Fallback Single speaker followed by whitespace/tab and text
P_SPEAKER_SIMPLE_FALLBACK = re.compile(rf"^{SPEAKER_PATTERN_FALLBACK}(\s+)(.*)")
