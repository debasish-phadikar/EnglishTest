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

   # --- REPLACEMENT RUBRIC (The "Strict Examiner" Brain) ---
    RUBRIC_PROMPT = """
    You are a strict, senior IELTS Speaking Examiner. Your task is to evaluate the student's audio response based EXCLUSIVELY on the official IELTS Speaking Band Descriptors provided below.
    
    ### OFFICIAL IELTS SPEAKING BAND DESCRIPTORS (ABBREVIATED):
    
    **1. Fluency and Coherence (FC)**
    - Band 9: Speaks fluently with rare repetition; hesitation is content-related only. Coherent with fully appropriate cohesive features.
    - Band 7: Speaks at length without noticeable effort. May demonstrate language-related hesitation at times. Uses a range of connectives/discourse markers with some flexibility.
    - Band 6: Willing to speak at length but may lose coherence due to occasional repetition, self-correction, or hesitation. Uses a range of connectives but not always appropriately.
    - Band 5: Slow speech, over-use of certain connectives, simple speech is fluent but complex communication causes problems.
    - Band 4: Cannot respond without noticeable pauses; frequent repetition/self-correction.
    
    **2. Lexical Resource (LR)**
    - Band 9: Uses vocabulary with full flexibility and precision. Uses idiomatic language naturally.
    - Band 7: Uses vocabulary flexibly. Uses some less common and idiomatic vocabulary with some awareness of style/collocation (occasional errors). Paraphrases effectively.
    - Band 6: Has wide enough vocabulary to discuss topics at length. Uses some less common vocabulary but with some inappropriate choices.
    - Band 5: Limited flexibility. Manages to talk about familiar topics but struggles with unfamiliar ones.
    
    **3. Grammatical Range and Accuracy (GRA)**
    - Band 9: Full range of structures naturally. Consistently accurate apart from 'slips'.
    - Band 7: Uses a range of complex structures with some flexibility. Frequently produces error-free sentences, though some grammatical mistakes persist.
    - Band 6: Uses a mix of simple and complex structures. May make frequent mistakes with complex structures, but these rarely cause comprehension problems.
    - Band 5: Produces basic sentence forms with reasonable accuracy. Complex structures usually contain errors.
    
    **4. Pronunciation (P)**
    - Band 9: Effortless to understand. Full range of pronunciation features with precision and subtlety.
    - Band 7: Easy to understand throughout. L1 accent has minimal effect. Uses a range of pronunciation features.
    - Band 6: Can generally be understood, but mispronunciation of individual words/sounds reduces clarity at times. Mixed control of features.
    - Band 4: Limited range of pronunciation features. Frequent mispronunciations cause difficulty for the listener.
    
    ### YOUR TASK:
    Analyze the provided audio transcript and provide a rigorous assessment. 
    You MUST provide the output in the following Markdown format:
    
    # 📊 IELTS Speaking Test Report
    
    ## **Overall Band Score: [Insert Score, e.g., 6.5]**
    
    ---
    
    ### 1. Fluency and Coherence (Score: [0-9])
    * **Analysis:** [Explain why they got this score referring to the descriptors above]
    * **Strengths:** [Quote specific examples where flow was good]
    * **Weaknesses:** [Quote specific examples of hesitation or repetition]
    
    ### 2. Lexical Resource (Score: [0-9])
    * **Analysis:** [Evaluate their vocabulary range]
    * **High-Level Vocabulary Used:** [List 3-5 advanced words/idioms the student used]
    * **Vocabulary Errors:** [List specific words used incorrectly -> Suggest better alternatives]
    
    ### 3. Grammatical Range and Accuracy (Score: [0-9])
    * **Analysis:** [Evaluate sentence structures]
    * **Complex Structures Used:** [Quote a complex sentence the student used correctly]
    * **Grammar Errors:** [Quote the error -> Show the corrected version]
    
    ### 4. Pronunciation (Score: [0-9])
    * **Analysis:** [Evaluate clarity, intonation, and stress]
    * **Problem Areas:** [List specific sounds or words the student mispronounced]
    
    ---
    ### 💡 Examiner's Final Advice
    [Provide 3 actionable steps the student can take to move to the next Band level]
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
