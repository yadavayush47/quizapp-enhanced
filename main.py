import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import json

# --- 1. SETTING UP THE PAGE ---
st.set_page_config(page_title="AI Quiz Master", layout="centered")

st.title("📚 AI PDF Quiz Generator")
st.write("Upload your notes, and I'll create a practice quiz for you!")

# --- 2. GEMINI API SETUP ---
# Replace the text below with your actual API Key from Google AI Studio
API_KEY = st.secrets["GEMINI_API_KEY"] 
genai.configure(API_KEY = st.secrets["GEMINI_API_KEY"]")
model = genai.GenerativeModel('gemini-2.5-flash')

# --- 3. THE "MEMORY" (SESSION STATE) ---
# This tells the app not to forget the quiz when you click a button
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

    if generate_button:
        if uploaded_file is not None:
            with st.spinner("Reading PDF and generating questions..."):
                # A. Extract the text
                pdf_text = extract_text_from_pdf(uploaded_file)
                
                # B. Create the instructions for Gemini
                prompt = f"""
                You are a professor. Based on the following text, create {num_q} multiple choice questions.
                Return ONLY a JSON list of objects. Each object must have:
                "question": The question text
                "options": A list of 4 possible answers
                "answer": The correct answer (exactly as it appears in the options)
                
                Text: {pdf_text[:15000]}
                """
                
                # C. Call Gemini
                response = model.generate_content(prompt)
                
                # D. Clean the response and save it to memory
                try:
                    clean_json = response.text.replace("```json", "").replace("```", "").strip()
                    st.session_state.quiz_data = json.loads(clean_json)
                    st.success("Quiz Generated! Look at the main screen.")
                except Exception as e:
                    st.error("There was a formatting error. Please try generating again.")
        else:
            st.warning("Please upload a PDF file first!")

# --- 6. THE MAIN SCREEN (QUIZ DISPLAY) ---
if st.session_state.quiz_data:
    st.write("---")
    for i, item in enumerate(st.session_state.quiz_data):
        st.subheader(f"Question {i+1}")
        st.write(item['question'])
        
        # Display multiple choice options
        user_choice = st.radio(
            "Select your answer:", 
            item['options'], 
            key=f"user_choice_{i}"
        )
        
        # Check Answer Button for each question
        if st.button(f"Check Answer for Q{i+1}", key=f"check_{i}"):
            if user_choice == item['answer']:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Incorrect. The correct answer is: {item['answer']}")
else:
    st.info("👈 Upload a PDF and click 'Generate' in the sidebar to begin!")
