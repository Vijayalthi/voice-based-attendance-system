# 🎙️ Voice-Based Attendance System

This is a voice-interactive attendance system built with Python and Streamlit. The app calls out roll numbers, listens for voice responses (e.g., “present”, “yes”), marks attendance based on fuzzy matching, and generates a downloadable PDF report.

---

## 🚀 Features

- 🔊 Calls out student roll numbers using Text-to-Speech
- 🎤 Listens for responses using microphone and marks attendance
- 🧠 Uses fuzzy string matching to detect wake words like "present", "yes", "here"
- 📄 Generates attendance report as a downloadable PDF
- 📁 Allows dynamic upload of different student lists via CSV

---

## 📝 CSV Format

Upload a `.csv` file with the following columns:

```csv
roll_no,name
1,Alice
2,Bob
3,Charlie
...
```
