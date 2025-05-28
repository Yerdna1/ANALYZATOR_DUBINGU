# Analyzátor Dabingových Scenárov

Streamlit application for analyzing Slovak dubbing scripts (.docx files) that:
- Extracts structured data (speakers, timecodes, dialogues)
- Generates speaker-segment matrices
- Provides Excel exports
- **Estimates segment durations based on speaker count**
- **Generates optimal recording schedules considering speaker availability and global studio slots**
- **Provides a calendar view of availability**
- **Allows JSON export/import for availability configurations**

## Features
- Processes DOCX files with Slovak dubbing scripts
- Identifies speakers, timecodes, and scene markers
- Generates speaker participation statistics
- Exports data to Excel format
- **Configurable nominal segment durations based on speaker count**
- **Input fields for speaker availability and global recording times**
- **Calculates and displays proposed optimal recording schedule**
- **Summarizes recording schedule by speaker (total scheduled time, segments, idle time)**
- **Interactive calendar view of speaker and recording availability**
- **JSON export and import for availability settings**

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
2. Log in with the provided credentials.
3. Upload a DOCX script file.
4. View parsed data and statistics.
5. Configure nominal segment durations, speaker availability, and global recording times.
6. Calculate and view the optimal recording schedule.
7. Export data to Excel or availability configurations to JSON when ready.

## Requirements
- Python 3.11+
- See requirements.txt for dependencies

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
│   └── scheduler/     # Optimal scheduling logic
│       ├── __init__.py
│       ├── calendar.py
│       ├── core.py
│       ├── summary.py
│       └── utils.py
├── app.py             # Streamlit application entry point
├── requirements.txt   # Python dependencies
├── memory-bank/       # Project documentation
│   ├── .clinerules
│   ├── activeContext.md
│   ├── productContext.md
│   ├── progress.md
│   ├── projectbrief.md
│   ├── systemPatterns.md
│   ├── techContext.md
│   └── user-guide-sk.md # New user guide in Slovak
├── components/        # Reusable UI components
│   └── ui_components.py
├── utils/             # Utility functions
│   ├── auth.py
│   ├── excel_export.py
│   └── session_state_manager.py
└── tests/             # Unit tests
