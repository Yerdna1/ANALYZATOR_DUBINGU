# Project Brief: Analyzátor Dabingových Scenárov

## Overview
A Streamlit application for analyzing dubbing scripts (.docx files) that:
1. Converts and chunks documents
2. Identifies speakers, timecodes, dialogues, scene markers
3. Generates speaker-segment matrices
4. Provides Excel exports

## Core Requirements
- Process DOCX files with Slovak dubbing scripts
- Extract structured data (speakers, segments, timecodes)
- Generate speaker-segment matrices
- Export data to Excel format
- User authentication system

## Key Features
- File upload and processing
- Data visualization tables
- Speaker-segment matrix generation
- Excel export functionality
- Login/logout system

## Technical Stack
- Python 3.11
- Streamlit (frontend)
- docx2txt (document conversion)
- pandas (data processing)
- openpyxl (Excel export)
