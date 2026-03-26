import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import json

# --- 1. SETTING UP THE PAGE ---
st.set_page_config(page_title="AI Quiz Master", layout="centered")

st.title("📚 AI PDF Quiz Generator")
st.write("Upload your notes, and I'll create a practice quiz for you!")

# --- 2. GEMINI API SETUP ---
# Securely fetching the API key from Streamlit Secrets
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # Using the most stable model version for 2026
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error("API Key not found or configured incorrectly in Secrets.")

# --- 3. THE "MEMORY" (SESSION STATE) ---
if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

# --- 4. HELPER FUNCTIONS ---
def extract_text_from_pdf(pdf_file):
    """Reads the PDF file and turns it into text."""
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    return full_text

# --- 5. THE SIDEBAR (CONTROLS) ---
with st.sidebar:
    st.header("Settings")
    uploaded_file = st.file_uploader("Upload your PDF here", type="pdf")
    num_q = st.slider("How many questions?", min_value=3, max_value=15, value=5)
    
    generate_button = st.button("Generate Quiz")

# --- 6. GENERATION LOGIC ---
if generate_button:
    if uploaded_file is not None:
        with st.spinner("Analyzing your engineering notes..."):
            try:
                # A. Extract the text
                pdf_text = extract_text_from_pdf(uploaded_file)
                
                # B. Create the instructions for Gemini
                prompt = f"""
                You are an expert professor. Based on the following text, create {num_q} multiple choice questions.
                Return ONLY a JSON list of objects. Do not include any intro text.
                Format:
                [
                  {{"question": "...", "options": ["A", "B", "C", "D"], "answer": "..."}},
                  ...
                ]
                
                Text: {pdf_text[:15000]}
                """
                
                # C. Call Gemini
                response = model.generate_content(prompt)
                
                # D. Clean the response (Removing markdown code blocks if present)
                raw_text = response.text
                if "```json" in raw_text:
                    raw_text = raw_text.split("```json")[1].split("```")[0]
                elif "```" in raw_text:
                    raw_text = raw_text.split("```")[1].split("```")[0]
                
                st.session_state.quiz_data = json.loads(raw_text.strip())
                st.success("Quiz Generated!")
            except Exception as e:
                st.error(f"Error: {str(e)}")
    else:
        st.warning("Please upload a PDF file first!")

# --- 7. THE MAIN SCREEN (QUIZ DISPLAY) ---
if st.session_state.quiz_data:
    st.write("---")
    for i, item in enumerate(st.session_state.quiz_data):
        st.subheader(f"Question {i+1}")
        st.write(item['question'])
        
        user_choice = st.radio(
            "Select your answer:", 
            item['options'], 
            key=f"user_choice_{i}"
        )
        
        if st.button(f"Check Answer for Q{i+1}", key=f"check_{i}"):
            if user_choice == item['answer']:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Incorrect. The correct answer is: {item['answer']}")
else:
    st.info("👈 Upload a PDF in the sidebar and click 'Generate' to begin!")
