# Technical Context: Analyzátor Dabingových Scenárov

## Development Environment
- Python 3.11
- Virtual environment (recommended)
- VSCode (recommended IDE)
- Git for version control

## Core Dependencies
- Streamlit==1.45.1 (web interface)
- pandas==2.2.1 (data processing)
- openpyxl==3.1.2 (Excel export)
- docx2txt==0.9 (DOCX parsing)
- python-docx==1.1.2 (DOCX manipulation)

## Project Structure
```
ANALYZATOR_DUBINGU/
├── parser.py          # Main document parsing logic
├── app.py             # Streamlit application entry point
├── requirements.txt   # Python dependencies
├── memory-bank/       # Project documentation
└── tests/             # Unit tests
```

## Configuration
- No external configuration files needed
- All settings managed through Streamlit's session state
- Excel export format configured in app.py

## Testing
- pytest for unit tests
- Test cases cover:
  - Document parsing
  - Data structure generation
  - Matrix calculations
  - Excel export formatting
