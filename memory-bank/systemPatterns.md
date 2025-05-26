# System Patterns: Analyzátor Dabingových Scenárov

## Core Architectural Patterns
1. Document Processing Pipeline:
   - File Upload → Text Extraction → Structure Parsing → Data Analysis
   - Each stage implemented as separate, testable components

2. Data Processing:
   - Pandas DataFrames for structured data storage
   - Matrix operations for speaker-segment analysis
   - Decorator pattern for adding processing steps

3. Error Handling:
   - Context managers for file operations
   - Custom exceptions for parsing errors
   - Retry logic for transient failures

## Parser Implementation
- Regular expressions for:
  - Speaker identification (e.g., "SPEAKER:")
  - Timecode extraction (e.g., "00:01:23:14")
  - Scene marker detection (e.g., "SCENE 1")
- State machine for tracking document sections

## Data Structures
- Primary DataFrame columns:
  - speaker
  - dialogue  
  - timecode_in
  - timecode_out
  - scene_marker
- Speaker-segment matrix:
  - Rows: Speakers
  - Columns: Scene segments
  - Values: Participation flags
