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
    client = genai.Client(api_key=st.secrets["GEMINI_API_KEY"])
    # gemini-2.5-flash-lite is great for higher request limits
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
    with st.spinner("Analyzing PDF and generating quiz..."):
        try:
            pdf_text = extract_text_from_pdf(uploaded_file)
            
            # Strict prompt to ensure keys match
            prompt = f"""
            Based on the text below, create {num_q} multiple choice questions.
            Return ONLY a JSON list of objects.
            Each object MUST have exactly these keys: "question", "options", "answer".
            "options" must be a list of 4 strings.
            Text: {pdf_text[:15000]}
            """
            
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=prompt
            )
            
            raw_text = response.text
            if "```json" in raw_text:
                raw_text = raw_text.split("```json")[1].split("```")[0]
            elif "```" in raw_text:
                raw_text = raw_text.split("```")[1].split("```")[0]
            
            st.session_state.quiz_data = json.loads(raw_text.strip())
            st.success("Ready!")
        except Exception as e:
            st.error(f"Error during generation: {e}")

# --- 6. DISPLAY ---
if st.session_state.quiz_data:
    for i, item in enumerate(st.session_state.quiz_data):
        # Use .get() to prevent crashes if a key is missing
        q_text = item.get('question', 'Question text missing')
        options = item.get('options', ['A', 'B', 'C', 'D'])
        correct_ans = item.get('answer', 'Not specified')

        st.subheader(f"Q{i+1}: {q_text}")
        user_choice = st.radio("Choose:", options, key=f"q_{i}")
        
        if st.button(f"Check Q{i+1}", key=f"btn_{i}"):
            if user_choice == correct_ans:
                st.success("✅ Correct!")
            else:
                st.error(f"❌ Wrong. Answer: {correct_ans}")

# --- 8. DOWNLOAD BUTTON (SAFE VERSION) ---
if st.session_state.quiz_data:
    st.write("---")
    
    quiz_text = "📝 AI GENERATED QUIZ REPORT\n"
    quiz_text += "="*30 + "\n\n"
    
    for i, item in enumerate(st.session_state.quiz_data):
        # Bulletproof data extraction
        q_text = item.get('question', 'N/A')
        opts = item.get('options', [])
        ans = item.get('answer', 'N/A')

        quiz_text += f"Q{i+1}: {q_text}\n"
        for idx, opt in enumerate(opts):
            quiz_text += f"   {chr(65+idx)}) {opt}\n"
        
        quiz_text += f"\n✅ Correct Answer: {ans}\n"
        quiz_text += "-"*20 + "\n\n"

    st.download_button(
        label="📥 Download Quiz as Text File",
        data=quiz_text,
        file_name="Engineering_Quiz.txt",
        mime="text/plain"
    )
