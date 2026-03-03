# WhatsApp Chat Analyser

A Streamlit app to analyze exported WhatsApp chat text files.

## Features
- Total messages, media, words, and links
- Most active users with message and word percentage table
- Daily, monthly, yearly, and hourly timelines
- Interactive Plotly charts (line/bar/pie)
- Most common words (stop words removed)
- Word cloud (WordCloud library)
- Most used emojis table + chart

## Setup
### Linux/macOS
```bash
chmod +x setup.sh
./setup.sh
```

### Windows (PowerShell)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt
```

## Run
```bash
streamlit run app.py
```

or on Windows:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py --server.port 8503
```

## Input format
Export chat from WhatsApp as `.txt` and upload it in the sidebar.

## Deploy
### Streamlit Community Cloud (Recommended)
1. Push this project to a GitHub repository.
2. Go to [https://share.streamlit.io](https://share.streamlit.io) and sign in.
3. Click **New app** and select your repository.
4. Set:
   - Main file path: `app.py`
   - Python dependencies: auto-detected from `requirements.txt`
5. Click **Deploy**.

### Render
1. Push this project to GitHub.
2. In Render, create a new **Web Service** from the repo.
3. Render will auto-detect `render.yaml`.
4. Deploy.

## Local update after dependency changes
```bash
python -m pip install -r requirements.txt
```
