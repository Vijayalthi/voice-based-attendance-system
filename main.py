# voice_attendance_app.py
from gtts import gTTS
import streamlit as st
import pyttsx3
import speech_recognition as sr
import pandas as pd
from fuzzywuzzy import fuzz
from fpdf import FPDF
import datetime
import time
import os
import uuid

WAKE_WORDS = ["present", "yes", "here", "i am here", "yessir", "yep", "yup", "hai sir"]

# Function to speak text using pyttsx3
def speak(text):
    tts = gTTS(text)
    filename = f"temp_{uuid.uuid4().hex}.mp3"
    tts.save(filename)
    audio_file = open(filename, "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')
    audio_file.close()
    os.remove(filename)

# Function to listen and convert speech to text
def listen():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source, duration=0.3)
        print("🎧 Listening...")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=4)
            response = recognizer.recognize_google(audio)
            print(f"✅ Heard: {response}")
            return response.lower()
        except sr.WaitTimeoutError:
            print("⏳ No response (timeout)")
        except sr.UnknownValueError:
            print("❓ Could not understand audio")
        except sr.RequestError:
            print("⚠ Could not connect to speech recognition service")
        return ""

# Detect if wake word is in response
def detect_wake_word(text):
    text = text.lower()
    for word in WAKE_WORDS:
        if word in text or fuzz.partial_ratio(word, text) > 85:
            return True
    return False

# Generate PDF attendance report
def generate_pdf(df, subject, date):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, f"Attendance Report for {subject} - {date}", ln=True, align='C')
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(40, 10, "Roll No.", 1)
    pdf.cell(80, 10, "Name", 1)
    pdf.cell(40, 10, "Status", 1)
    pdf.ln()

    pdf.set_font("Arial", '', 12)
    for index, row in df.iterrows():
        pdf.cell(40, 10, str(row["roll_no"]), 1)
        pdf.cell(80, 10, row["name"], 1)
        pdf.cell(40, 10, row["status"], 1)
        pdf.ln()

    filename = f"Attendance_{subject}_{date}.pdf".replace(" ", "")
    filepath = os.path.join("generated_reports", filename)
    os.makedirs("generated_reports", exist_ok=True)
    pdf.output(filepath)
    return filepath

# Streamlit UI
st.title("🎙 Voice-Based Attendance System")

# Upload CSV
uploaded_file = st.file_uploader("Upload student list CSV (with roll_no, name columns)", type=["csv"])
if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        if "roll_no" not in df.columns or "name" not in df.columns:
            st.error("CSV must contain 'roll_no' and 'name' columns")
            st.stop()
        df["status"] = "Absent"
    except Exception as e:
        st.error(f"❌ Error reading uploaded CSV: {e}")
        st.stop()
else:
    st.warning("Please upload a student list CSV file to begin.")
    st.stop()

# Inputs
subject = st.text_input("📘 Enter subject name:", "")
date_input = st.text_input("📅 Enter date (YYYY-MM-DD):", "")
today_str = datetime.date.today().strftime("%Y-%m-%d")
date = date_input.strip() if date_input.strip() else today_str

if st.button("Start Attendance"):
    if not subject.strip():
        st.error("Please enter a subject name.")
        st.stop()

    # Announce attendance
    announce = f"Attention students. The attendance for subject {subject} is being taken. Respond when you hear your name."
    speak(announce)

    st.write("📚 Attendance in progress... (check terminal for audio interaction)")

    placeholder = st.empty()  # UI placeholder to show current roll number being called

    for index, row in df.iterrows():
        roll = row["roll_no"]
        name = row["name"]

        placeholder.markdown(f"### 🎙 Calling Roll Number {roll}, {name}...")
        speak(f"Roll number {roll}, {name}, are you present?")
        response = listen()

        if detect_wake_word(response):
            df.at[index, "status"] = "Present"
            speak("Marked present.")
        else:
            speak("Marked absent.")

        time.sleep(0.5)
        placeholder.empty()

    # Generate PDF
    filepath = generate_pdf(df, subject, date)

    # Summary
    present = df[df["status"] == "Present"]
    absent = df[df["status"] == "Absent"]

    st.success("✅ Attendance Completed!")
    st.write(f"Present: {len(present)}")
    st.write(f"Absent: {len(absent)}")

    if not absent.empty:
        st.markdown("### 🚫 Absentees:")
        st.table(absent[["roll_no", "name"]])

    with open(filepath, "rb") as f:
        st.download_button("📄 Download Attendance PDF", f, file_name=os.path.basename(filepath), mime="application/pdf")