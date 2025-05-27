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
- **numpy (for numerical operations, implicitly used by pandas)**

## Project Structure
```
ANALYZATOR_DUBINGU/
├── parser/            # Document parsing logic
│   ├── __init__.py
│   ├── constants.py
│   ├── core_parsing.py
│   └── speaker_processing.py
├── analyzer/          # Data analysis and scheduling logic
│   ├── __init__.py
│   ├── calculations.py
│   ├── data_processing.py
│   └── scheduler.py
├── app.py             # Streamlit application entry point
├── requirements.txt   # Python dependencies
├── memory-bank/       # Project documentation
│   ├── .clinerules
│   ├── activeContext.md
│   ├── productContext.md
│   ├── progress.md
│   ├── projectbrief.md
│   ├── systemPatterns.md
│   └── techContext.md
├── components/        # Reusable UI components (if any)
└── tests/             # Unit tests
```

## Configuration
- No external configuration files needed
- All settings managed through Streamlit's session state
- Excel export format configured in app.py
- **Nominal segment durations configured via Streamlit UI and stored in session state**
- **Speaker availability and global recording slots configured via Streamlit UI and stored in session state**

## Testing
- pytest for unit tests
- Test cases cover:
  - Document parsing
  - Data structure generation
  - Matrix calculations
  - Excel export formatting
  - **Nominal duration calculation**
  - **Speaker availability parsing**
  - **Optimal schedule generation**
  - **Calendar view generation**
