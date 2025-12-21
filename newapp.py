import streamlit as st
import google.generativeai as genai
import tempfile
import os
from dotenv import load_dotenv

# --- 1. SETUP & SECURITY ---
# Load environment variables from .env file
#load_dotenv()

# Fetch API Key securely
#api_key = os.getenv("GOOGLE_API_KEY")
# Streamlit automatically loads the secrets file
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    st.error("Missing API Key. Please set it in .streamlit/secrets.toml")
    st.stop()


st.set_page_config(page_title="Expert English Institute", page_icon="🎓")

# --- 2. LOGIN SYSTEM ---
# Simple hardcoded users (In real life, this would be a database)
USERS = {
    "student": "english123",
    "demo": "pass123",
    "admin": "admin123"
}

if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

def login_page():
    st.title("🔐 Student Portal Login")
    st.write("Welcome to the Expert English Institute.")
    
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if username in USERS and USERS[username] == password:
            st.session_state['logged_in'] = True
            st.success("Login Successful!")
            st.rerun()  # Reload the page to show the app
        else:
            st.error("Invalid Username or Password")

def logout():
    st.session_state['logged_in'] = False
    st.rerun()

# --- 3. THE EXAMINER APP (Only runs if logged in) ---
def main_app():
    # Sidebar with Logout
    with st.sidebar:
        st.write(f"Logged in as: **User**")
        if st.button("Logout"):
            logout()
    
    # Configure Google AI
    if not api_key:
        st.error("API Key not found!")
        st.stop()
        
    genai.configure(api_key=api_key)

    # RUBRIC (The Brain)
    RUBRIC_PROMPT = """
    You are an expert IELTS Speaking Examiner. Grade the student on these 4 criteria (0-9 Scale):
    1. Fluency and Coherence (Speed, pauses, flow)
    2. Lexical Resource (Vocabulary range, idioms)
    3. Grammatical Range (Sentence structure, error frequency)
    4. Pronunciation (Clarity, intonation)

    **TASK:**
    Listen to the audio. Analyze it against the questions asked.
    Provide:
    - **Approximate Band Score:** (e.g., 6.5)
    - **Detailed Feedback:** Break down by the 4 criteria.
    - **Corrected Examples:** Quote 3 mistakes and show how a native speaker would say it.
    """

    st.title("🗣️ Student Speaking Mock Test")
    st.markdown("### IELTS Automated Speaking Assessment Tool")

    # TEST QUESTIONS
    questions_part_1 = [
        "1. What job do you do?",
        "2. Why did you choose this job?",
        "3. What do you like most about your job?",
        "4. Do you like shopping?",
        "5. Who do you like going shopping with?",
        "6. What do you buy online?",
        "7. Do you like to shop around to get a good price?",
        "8. Do you like where you live now?",
        "9. What places do you go to in order to relax?",
        "10. Where is your favourite place in your country?",
        "11. What kind of places do you visit with your family/friends?"
    ]

    question_part_2 = """
    **12. Describe a story from a book or film that you enjoyed.**
    You should say:
    a. Where you read/saw it
    b. When you read/saw it
    c. What the story was about
    d. Explain why you enjoyed it.
    """

    # TABS LAYOUT
    tab1, tab2, tab3 = st.tabs(["Part 1: Interview", "Part 2: Long Turn", "Analysis"])

    audio_part_1 = None
    audio_part_2 = None

    with tab1:
        st.header("Part 1: Quick Fire")
        st.info("Answer these questions in one continuous recording. Once Part 1 completed, go to Part 2.")
        with st.expander("Show Questions"):
            for q in questions_part_1:
                st.write(q)
        audio_part_1 = st.audio_input("Record your Part 1 Answer")

    with tab2:
        st.header("Part 2: The Story")
        st.info("Speak for 1-2 minutes on this topic. Once Part 2 completed, Click Analyse for final score.")
        st.write(question_part_2)
        audio_part_2 = st.audio_input("Record your Part 2 Answer")

    with tab3:
        st.header("📊 Final Score")
        if st.button("Generate Your Report"):
            if not audio_part_1 or not audio_part_2:
                st.error("Please record BOTH parts first.")
            else:
                with st.spinner("Analyzing your voice..."):
                    try:
                        # Helper to save temp files
                        def save_audio(audio_bytes):
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                                tmp.write(audio_bytes.read())
                                return tmp.name

                        path1 = save_audio(audio_part_1)
                        path2 = save_audio(audio_part_2)

                        # Upload to Google
                        myfile1 = genai.upload_file(path1)
                        myfile2 = genai.upload_file(path2)
                        
                        # Generate Content (Using the model you confirmed works)
                        # NOTE: Change "gemini-1.5-flash" below if you are using a different one
                        model = genai.GenerativeModel("gemini-2.5-flash-lite")
                        
                        result = model.generate_content(
                            [RUBRIC_PROMPT, "Part 1 Audio:", myfile1, "Part 2 Audio:", myfile2]
                        )
                        
                        st.markdown(result.text)
                        
                        # Clean up
                        os.remove(path1)
                        os.remove(path2)
                        
                    except Exception as e:
                        st.error(f"Error: {e}")

# --- 4. CONTROL FLOW ---
if not st.session_state['logged_in']:
    login_page()
else:
    main_app()
