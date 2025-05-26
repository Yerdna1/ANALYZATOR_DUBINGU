# Product Context: Analyzátor Dabingových Scenárov

## Purpose
Automate analysis of Slovak dubbing scripts to:
- Track speaker participation across segments
- Identify scene transitions and markers
- Calculate timecode distributions
- Generate reports for dubbing directors

## User Workflow
1. Upload .docx script file
2. System parses and structures the content
3. User reviews extracted data
4. User generates speaker-segment matrix
5. User exports data to Excel

## Key Components
1. Document Parser (parser.py)
   - Extracts speakers, timecodes, dialogues
   - Identifies scene markers and segments
2. Data Processor
   - Creates speaker-segment matrices
   - Calculates statistics
3. Streamlit UI
   - File upload interface
   - Data visualization
   - Export controls

## Technical Dependencies
- docx2txt for document conversion
- pandas for data manipulation
- openpyxl for Excel export
- Streamlit for web interface
