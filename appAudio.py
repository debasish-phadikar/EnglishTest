import streamlit as st
import google.generativeai as genai
import os
from dotenv import load_dotenv
import tempfile

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Audio Pronunciation Test", page_icon="🎤")
load_dotenv()

AUTHORIZED_USERS = {
    "admin": "admin123",
    "tester": "welcome2024"
}

# --- 2. SESSION STATE SETUP ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

# --- 3. HELPER FUNCTION (Uploads to Gemini) ---
def save_and_upload_file(uploaded_file):
    """
    Saves streamlit upload to temp file, uploads to Gemini, returns Gemini file obj.
    """
    try:
        suffix = "." + uploaded_file.name.split('.')[-1]
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            tmp_file.write(uploaded_file.getvalue())
            tmp_path = tmp_file.name

        # Upload to Google Gemini
        # MIME type is important for audio
        gemini_file = genai.upload_file(path=tmp_path, mime_type=uploaded_file.type)
        
        # Clean up local temp file
        os.remove(tmp_path)
        return gemini_file
    except Exception as e:
        st.error(f"Error uploading file: {e}")
        return None

# --- 4. LOGIN SCREEN ---
def login_screen():
    st.title("🔒 Login Required")
    
    with st.form("login_form"):
        username_input = st.text_input("Username").strip()
        password_input = st.text_input("Password", type="password").strip()
        submitted = st.form_submit_button("Login")

        if submitted:
            if username_input in AUTHORIZED_USERS and AUTHORIZED_USERS[username_input] == password_input:
                st.session_state.authenticated = True
                st.success("Login successful!")
                st.rerun()
            else:
                st.error("❌ Incorrect username or password")

# --- 5. MAIN APP (THE UI) ---
def main_app():
    # A. Sidebar Logout
    if st.sidebar.button("Logout"):
        st.session_state.authenticated = False
        st.rerun()

    # B. API Key Setup (Done once here)
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        try:
            api_key = st.secrets["GOOGLE_API_KEY"]
        except Exception:
            pass

    if not api_key:
        st.error("🚨 API Key not found. Check .env or Secrets.")
        st.stop()

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        st.error(f"Config Error: {e}")
        st.stop()

    # C. The Application UI
    st.title("🎤 Audio Pronunciation Test")
    st.write("Upload a reference audio and record your attempt. It will be evaluated instantly!")

    # SECTION 1: REFERENCE AUDIO
    st.subheader("1. The Reference Audio")
    reference_file = st.file_uploader("Upload the correct audio (mp3/wav)", type=["mp3", "wav"])
    if reference_file:
        st.audio(reference_file, format=reference_file.type)

    # SECTION 2: STUDENT AUDIO
    st.subheader("2. Your Attempt (Student)")
    student_recording = st.audio_input("Record your voice")
    
    # SECTION 3: ANALYSIS
    if st.button("Analyze Audio"):
        if not reference_file or not student_recording:
            st.warning("Please provide both a Reference audio and a Student recording.")
        else:
            with st.spinner("Uploading audio and analyzing ..."):
                
                # Upload files using the helper function
                ref_gemini = save_and_upload_file(reference_file)
                
                # Audio input usually lacks a name/type, so we force one
                student_recording.name = "student_attempt.wav" 
                # Note: st.audio_input usually returns "audio/wav"
                if not student_recording.type:
                    student_recording.type = "audio/wav"
                    
                stu_gemini = save_and_upload_file(student_recording)

                if ref_gemini and stu_gemini:
                    # Define Model (Updated to 1.5 Flash as 2.5 doesn't exist yet)
                    model = genai.GenerativeModel('gemini-2.5-flash')

                    prompt = """
                    You are an expert linguistics coach. 
                    I will provide two audio files.
                    1. The first file is the REFERENCE (perfect pronunciation).
                    2. The second file is the STUDENT ATTEMPT.

                    Please compare the student's attempt against the reference. 
                    Analyze the following:
                    - Accuracy: Did they say the right words?
                    - Pronunciation: Which specific sounds were incorrect?
                    - Speed/Intonation: Was it too fast/slow or flat?
                    
                    Give a score out of 10 and constructive feedback on how to improve.
                    """

                    response = model.generate_content([prompt, ref_gemini, stu_gemini])

                    st.success("Analysis Complete!")
                    st.markdown(response.text)

# --- 6. CONTROL FLOW ---
if not st.session_state.authenticated:
    login_screen()
else:
    main_app()