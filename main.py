import streamlit as st
import fitz  # PyMuPDF
from google import genai
import json

# --- 1. SETTING UP THE PAGE ---
st.set_page_config(page_title="AI Quiz Master", layout="centered")

# --- 2. CUSTOM CSS (Designing the "Inches") ---
st.markdown("""
    <style>
    /* 1. Center the main title and give it some 'weight' */
    .main-title {
        font-size: 42px;
        font-weight: 800;
        text-align: center;
        color: #4B5320;
        margin-bottom: 5px;
    }
    
    /* 2. Style the Question Cards to look like field notes */
    div[data-testid="stVerticalBlock"] > div:has(div.stRadio) {
        background-color: #E0E0D1; 
        padding: 25px;
        border-radius: 10px;
        border-left: 8px solid #4B5320;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
        margin-bottom: 20px;
    }

    /* 3. Make buttons look more industrial/tactical */
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #4B5320;
        color: white;
        border: none;
        text-transform: uppercase;
        font-weight: bold;
        letter-spacing: 1.2px;
    }
    
    /* 4. Improve the sidebar look */
    section[data-testid="stSidebar"] {
        border-right: 1px solid #4B5320;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NEW GEMINI 2026 SETUP ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MODEL_ID = "gemini-2.5-flash" 
except Exception as e:
    st.error("Check your Streamlit Secrets for the API Key.")

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

# --- 4. HELPER FUNCTIONS ---
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# --- 5. THE SIDEBAR (Command Center) ---
with st.sidebar:
    st.header("🎯 Mission Settings")
    uploaded_file = st.file_uploader("Upload Engineering PDF", type="pdf")
    num_q = st.slider("Number of Targets (Questions)", 3, 15, 5)
    generate_button = st.button("🚀 Generate Quiz")

# --- 6. LANDING PAGE (When no quiz exists) ---
if not st.session_state.quiz_data:
    st.markdown('<p class="main-title">📚 AI PDF Quiz Generator</p>', unsafe_allow_html=True)
    st.write("<p style='text-align: center;'>Precision-engineered study tool for mechanical engineering students.</p>", unsafe_allow_html=True)
    st.info("👈 To begin, upload your PDF notes in the sidebar and set your target question count.")

# --- 7. GENERATION LOGIC ---
if generate_button and uploaded_file:
    with st.spinner("Analyzing Intelligence..."):
        try:
            pdf_text = extract_text_from_pdf(uploaded_file)
            prompt = f"Create {num_q} MCQ from this text. Return ONLY JSON list with keys: 'question', 'options', 'answer'. Text: {pdf_text[:15000]}"
            
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            raw_text = response.text
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            
            st.session_state.quiz_data = json.loads(raw_text.strip())
            st.rerun() # Refresh to show the quiz
        except Exception as e:
            st.error(f"Error: {e}")

# --- 8. DISPLAY (The Quiz Board) ---
if st.session_state.quiz_data:
    st.markdown('<p class="main-title">📝 Your Practice Quiz</p>', unsafe_allow_html=True)
    
    for i, item in enumerate(st.session_state.quiz_data):
        q_text = item.get('question', '...')
        options = item.get('options', [])
        correct_ans = item.get('answer', '')

        st.subheader(f"Q{i+1}: {q_text}")
        user_choice = st.radio("Select Option:", options, key=f"q_{i}")
        
        if st.button(f"Check Answer {i+1}", key=f"btn_{i}"):
            if user_choice == correct_ans:
                st.success("✅ MISSION ACCOMPLISHED: CORRECT!")
            else:
                st.error(f"❌ INCORRECT. Intelligence suggests: {correct_ans}")

    # Download Button at the end
    st.write("---")
    quiz_text = "AI GENERATED QUIZ\n" + "="*20 + "\n"
    for i, item in enumerate(st.session_state.quiz_data):
        quiz_text += f"Q{i+1}: {item.get('question')}\nAns: {item.get('answer')}\n\n"
    
    st.download_button("📥 DOWNLOAD MISSION REPORT", data=quiz_text, file_name="Quiz.txt")
