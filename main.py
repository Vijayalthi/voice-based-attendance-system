import streamlit as st
import pandas as pd
from gtts import gTTS
import speech_recognition as sr
from fuzzywuzzy import fuzz
import time
import os
import uuid
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO

# Set Streamlit page config
st.set_page_config(page_title="Voice-Based Attendance", layout="centered")

# Define wake words
WAKE_WORDS = ["present", "yes", "here", "i am here", "yes sir"]

# Function to speak using gTTS and play in Streamlit
def speak(text):
    tts = gTTS(text)
    filename = f"temp_{uuid.uuid4().hex}.mp3"
    tts.save(filename)
    audio_file = open(filename, "rb")
    audio_bytes = audio_file.read()
    st.audio(audio_bytes, format='audio/mp3')
    audio_file.close()
    os.remove(filename)

# Speech recognition function
def recognize_speech(timeout=3):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        try:
            audio = recognizer.listen(source, timeout=timeout)
            response = recognizer.recognize_google(audio).lower()
            return response
        except (sr.UnknownValueError, sr.WaitTimeoutError, sr.RequestError):
            return ""

# Attendance-taking function
def take_attendance(df, subject_name, date_input):
    speak("Attention students! The roll call is about to begin. Please respond with Present.")
    time.sleep(1)

    for index, row in df.iterrows():
        roll = row["roll"]
        name = row["name"]
        text_to_speak = f"Roll number {roll}: {name}"
        st.markdown(f"### 🔊 {text_to_speak}")
        speak(text_to_speak)

        response = recognize_speech(timeout=3)
        matched = any(fuzz.ratio(response, wake) > 80 for wake in WAKE_WORDS)

        if matched:
            df.at[index, "status"] = "Present"
        else:
            df.at[index, "status"] = "Absent"

        time.sleep(0.5)

    speak("Attendance completed.")
    return df

# PDF generator
def generate_pdf(df, subject, date):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 40, "Attendance Report")
    c.setFont("Helvetica", 12)
    c.drawString(50, height - 70, f"Subject: {subject}")
    c.drawString(350, height - 70, f"Date: {date}")

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, height - 100, "Roll")
    c.drawString(150, height - 100, "Name")
    c.drawString(400, height - 100, "Status")

    y = height - 120
    for _, row in df.iterrows():
        c.setFont("Helvetica", 12)
        c.drawString(50, y, str(row["roll"]))
        c.drawString(150, y, row["name"])
        c.drawString(400, y, row["status"])
        y -= 20
        if y < 50:
            c.showPage()
            y = height - 50

    c.save()
    buffer.seek(0)
    return buffer

# Streamlit UI
st.title("🎤 Voice-Based Attendance System")

uploaded_file = st.file_uploader("Upload student list CSV", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    if "status" not in df.columns:
        df["status"] = "Absent"

    subject = st.text_input("Enter Subject Name")
    date_input = st.date_input("Select Date")

    if st.button("📣 Start Attendance"):
        updated_df = take_attendance(df.copy(), subject, date_input)
        st.success("✅ Attendance complete!")

        # Show updated table
        st.dataframe(updated_df)

        # Generate and offer PDF download
        pdf_data = generate_pdf(updated_df, subject, str(date_input))
        st.download_button("📄 Download Attendance PDF", data=pdf_data, file_name="attendance.pdf", mime="application/pdf")
