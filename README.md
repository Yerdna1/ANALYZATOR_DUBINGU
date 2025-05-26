# Analyzátor Dabingových Scenárov

Streamlit application for analyzing Slovak dubbing scripts (.docx files) that:
- Extracts structured data (speakers, timecodes, dialogues)
- Generates speaker-segment matrices
- Provides Excel exports

## Features
- Processes DOCX files with Slovak dubbing scripts
- Identifies speakers, timecodes, and scene markers
- Generates speaker participation statistics
- Exports data to Excel format

## Installation
1. Clone the repository
2. Create virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate  # Windows
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. Run the Streamlit app:
   ```bash
   streamlit run app.py
   ```
2. Upload a DOCX script file
3. View parsed data and statistics
4. Export to Excel when ready

## Requirements
- Python 3.11+
- See requirements.txt for dependencies

## Project Structure
```
ANALYZATOR_DUBINGU/
├── parser.py          # Main document parsing logic
├── app.py             # Streamlit application
├── requirements.txt   # Python dependencies
├── memory-bank/       # Project documentation
└── tests/             # Unit tests
