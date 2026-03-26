import streamlit as st
import fitz  # PyMuPDF
from google import genai
import json

# --- 1. SETTING UP THE PAGE ---
st.set_page_config(page_title="AI Quiz Master", layout="centered")

st.title("📚 AI PDF Quiz Generator")
st.write("Upload your notes, and I'll create a practice quiz!")

# --- 2. NEW GEMINI 2026 SETUP ---
try:
    # The new SDK uses a Client object
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    # gemini-2.5-flash is the stable workhorse for 2026
    MODEL_ID = "gemini-2.5-flash" 
except Exception as e:
    st.error("Check your Streamlit Secrets for the API Key.")

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

# --- 3. HELPER FUNCTIONS ---
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# --- 4. THE SIDEBAR ---
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload PDF", type="pdf")
    num_q = st.slider("Questions", 3, 15, 5)
    generate_button = st.button("Generate Quiz")

# --- 5. GENERATION LOGIC ---
if generate_button and uploaded_file:
    with st.spinner("Generating..."):
        try:
            pdf_text = extract_text_from_pdf(uploaded_file)
            prompt = f"Create {num_q} multiple choice questions from this text. Return ONLY JSON. Text: {pdf_text[:15000]}"
            
            # The new 2026 method call
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt
            )
            
            raw_text = response.text
            # Simple cleaning for JSON
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            
            st.session_state.quiz_data = json.loads(raw_text.strip())
            st.success("Ready!")
        except Exception as e:
            st.error(f"Error: {e}")

# --- 6. DISPLAY ---
if st.session_state.quiz_data:
    for i, item in enumerate(st.session_state.quiz_data):
        st.subheader(f"Q{i+1}: {item['question']}")
        user_choice = st.radio("Choose:", item['options'], key=f"q_{i}")
        if st.button(f"Check Q{i+1}", key=f"btn_{i}"):
            if user_choice == item['answer']:
                st.success("Correct!")
            else:
                st.error(f"Wrong. Answer: {item['answer']}")
