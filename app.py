import gradio as gr
import pyttsx3
import speech_recognition as sr
import pandas as pd
from fuzzywuzzy import fuzz
from fpdf import FPDF
import datetime
import time
import os

WAKE_WORDS = ["present", "yes", "here", "i am here", "yessir", "yep", "yup", "hai sir"]

def speak_blocking(text):
    engine = pyttsx3.init()
    engine.say(text)
    engine.runAndWait()
    time.sleep(0.3)

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
        except (sr.WaitTimeoutError, sr.UnknownValueError, sr.RequestError) as e:
            print(f"⚠ Listening error: {e}")
            return ""

def detect_wake_word(text):
    text = text.lower()
    for word in WAKE_WORDS:
        if word in text or fuzz.partial_ratio(word, text) > 85:
            return True
    return False

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

def start_attendance(csv_file, subject, date_input):
    if csv_file is None:
        return "❌ Please upload a CSV file.", None, None, None, None

    try:
        df = pd.read_csv(csv_file.name)
        if "roll_no" not in df.columns or "name" not in df.columns:
            return "❌ CSV must contain 'roll_no' and 'name' columns.", None, None, None, None
        df["status"] = "Absent"
    except Exception as e:
        return f"❌ Error reading uploaded CSV: {e}", None, None, None, None

    if not subject.strip():
        return "❌ Please enter a subject name.", None, None, None, None

    date = date_input.strip() or datetime.date.today().strftime("%Y-%m-%d")
    speak_blocking(f"Attention students. The attendance for subject {subject} is being taken. Respond when you hear your name.")
    
    for index, row in df.iterrows():
        roll = row["roll_no"]
        name = row["name"]
        speak_blocking(f"Roll number {roll}, {name}, are you present?")
        response = listen()
        if detect_wake_word(response):
            df.at[index, "status"] = "Present"
            speak_blocking("Marked present.")
        else:
            speak_blocking("Marked absent.")
        time.sleep(0.5)

    filepath = generate_pdf(df, subject, date)

    present_df = df[df["status"] == "Present"]
    absent_df = df[df["status"] == "Absent"]

    return (
        "✅ Attendance Completed!",
        present_df,
        absent_df,
        f"Present: {len(present_df)} | Absent: {len(absent_df)}",
        filepath,
    )

with gr.Blocks() as demo:
    gr.Markdown("## 🎙 Voice-Based Attendance System (Gradio Version)")
    with gr.Row():
        csv_input = gr.File(label="Upload CSV (with roll_no and name)", file_types=[".csv"])
        subject_input = gr.Textbox(label="Subject")
        date_input = gr.Textbox(label="Date (YYYY-MM-DD)", placeholder="Leave blank for today")

    submit_btn = gr.Button("📢 Start Attendance")
    status_output = gr.Markdown()
    present_table = gr.Dataframe()
    absent_table = gr.Dataframe()
    summary_text = gr.Textbox(label="Summary")
    pdf_output = gr.File(label="📄 Download PDF")

    submit_btn.click(
        fn=start_attendance,
        inputs=[csv_input, subject_input, date_input],
        outputs=[status_output, present_table, absent_table, summary_text, pdf_output],
    )

if __name__ == "__main__":
    demo.launch()
