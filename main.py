import streamlit as st
import fitz  # PyMuPDF
from google import genai
import json
import time

# --- 1. SETTING UP THE PAGE ---
st.set_page_config(page_title="AI Quiz Master | Tactical Edition", layout="centered")

# --- 2. THE DARK TACTICAL CSS (Designing Every Inch) ---
st.markdown("""
    <style>
    /* Main App Background */
    .stApp {
        background-color: #3B3F30;
    }
    
    /* Centered High-Contrast Title */
    .main-title {
        font-size: 48px;
        font-weight: 800;
        text-align: center;
        color: #F5F5DC;
        text-shadow: 3px 3px 6px rgba(0,0,0,0.6);
        margin-bottom: 10px;
    }

    /* Subtitle styling */
    .sub-title {
        text-align: center;
        color: #A2AD91;
        font-style: italic;
        margin-bottom: 40px;
    }

    /* Question Cards (Darker Green with Border) */
    div[data-testid="stVerticalBlock"] > div:has(div.stRadio) {
        background-color: #2E3226; 
        padding: 30px;
        border-radius: 10px;
        border: 1px solid #4B5320;
        border-left: 10px solid #A2AD91; /* Tactical Stripe */
        margin-bottom: 25px;
        box-shadow: 5px 5px 15px rgba(0,0,0,0.3);
    }

    /* Ensuring Radio Button Text is Cream/Visible */
    .stRadio label {
        color: #F5F5DC !important;
        font-size: 18px !important;
    }

    /* Tactical Black Buttons */
    .stButton>button {
        width: 100%;
        background-color: #1A1C14 !important;
        color: #F5F5DC !important;
        border: 1px solid #4B5320 !important;
        font-weight: bold;
        text-transform: uppercase;
        letter-spacing: 2px;
        padding: 10px;
        transition: 0.3s;
    }
    
    .stButton>button:hover {
        background-color: #4B5320 !important;
        border-color: #A2AD91 !important;
        color: #FFFFFF !important;
    }

    /* Custom Success/Error boxes */
    .stSuccess, .stError {
        background-color: #1A1C14 !important;
        border-radius: 5px !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. NEW GEMINI 2026 SETUP ---
try:
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    MODEL_ID = "gemini-2.5-flash" 
except Exception as e:
    st.error("Credential Error: Check Streamlit Secrets.")

if "quiz_data" not in st.session_state:
    st.session_state.quiz_data = None

# --- 4. HELPER FUNCTIONS ---
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    return "".join([page.get_text() for page in doc])

# --- 5. THE SIDEBAR (Command Center) ---
with st.sidebar:
    st.markdown("<h2 style='color: #F5F5DC;'>🎯 Mission Control</h2>", unsafe_allow_html=True)
    uploaded_file = st.file_uploader("Upload PDF Intelligence", type="pdf")
    num_q = st.slider("Target Questions", 3, 15, 5)
    
    # Simple rate-limit safety
    generate_button = st.button("🚀 INITIATE GENERATION")

# --- 6. LANDING VIEW ---
if not st.session_state.quiz_data:
    st.markdown('<p class="main-title">AI QUIZ MASTER</p>', unsafe_allow_html=True)
    st.markdown('<p class="sub-title">Extracting knowledge from engineering blueprints... one PDF at a time.</p>', unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("Awaiting PDF upload in Mission Control (Sidebar) to begin.")

# --- 7. GENERATION LOGIC ---
if generate_button and uploaded_file:
    with st.spinner("Processing Intelligence..."):
        try:
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            prompt = f"""
            Act as an Engineering Professor. Create {num_q} MCQ from this text. 
            Return ONLY a JSON list of objects with keys: "question", "options", "answer". 
            Text: {pdf_text[:15000]}
            """
            
            response = client.models.generate_content(model=MODEL_ID, contents=prompt)
            raw_text = response.text
            
            # JSON Cleaning
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]
            
            st.session_state.quiz_data = json.loads(raw_text.strip())
            st.success("INTELLIGENCE EXTRACTED SUCCESSFULLY.")
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"SYSTEM ERROR: {e}")

# --- 8. THE QUIZ DISPLAY ---
if st.session_state.quiz_data:
    st.markdown('<p class="main-title">🎖️ KNOWLEDGE CHECK</p>', unsafe_allow_html=True)
    
    for i, item in enumerate(st.session_state.quiz_data):
        # Bulletproof data retrieval
        q_text = item.get('question', 'Missing Question Data')
        options = item.get('options', ['A', 'B', 'C', 'D'])
        correct_ans = item.get('answer', 'N/A')

        st.subheader(f"Q{i+1}: {q_text}")
        user_choice = st.radio("SELECT OPTION:", options, key=f"q_{i}")
        
        if st.button(f"VERIFY Q{i+1}", key=f"btn_{i}"):
            if user_choice == correct_ans:
                st.success(f"✅ SECTOR CLEAR: Correct Answer is {correct_ans}")
            else:
                st.error(f"❌ COMPROMISED: Correct Answer is {correct_ans}")

    # Final Download Section
    st.write("---")
    quiz_report = "MISSION REPORT: AI QUIZ\n" + "="*30 + "\n"
    for i, item in enumerate(st.session_state.quiz_data):
        quiz_report += f"Q{i+1}: {item.get('question')}\nAnswer: {item.get('answer')}\n\n"
    
    st.download_button("📥 DOWNLOAD MISSION REPORT", data=quiz_report, file_name="Quiz_Report.txt")
