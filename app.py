import streamlit as st
import pandas as pd
from datetime import datetime
from logic import WashoutCalculator, RuleEngine
from ai_services import MockAIService, RealAIService
from form_filler import FormFiller
import os

st.set_page_config(layout="wide", page_title="Eligibility Screening Assistant")

st.title("Voice-Enabled Eligibility Screening Assistant")

# Sidebar for controls
st.sidebar.header("Controls")
mode = st.sidebar.selectbox("Mode", ["Mock Mode", "Live Mode (Requires API Key)"])

mock_scenario = "Eligible (Happy Path)"
if mode == "Mock Mode":
    mock_scenario = st.sidebar.selectbox("Test Scenario", list(MockAIService.SCENARIOS.keys()))

api_key = None
if mode == "Live Mode (Requires API Key)":
    api_key = st.sidebar.text_input("OpenAI API Key", type="password")
    if not api_key:
        st.warning("Please enter your API Key to use Live Mode.")

col1, col2 = st.columns(2)

with col1:
    st.header("1. Call Recording/Transcription")
    uploaded_file = st.file_uploader("Upload Audio or Text Transcript", type=["wav", "mp3", "txt"])
    
    if st.button("Start Processing") or uploaded_file:
        if mode == "Live Mode (Requires API Key)" and not api_key:
            st.error("API Key missing.")
            st.stop()
            
        with st.spinner("Processing..."):
            if mode == "Mock Mode":
                # Check if user uploaded a text file override
                if uploaded_file and uploaded_file.name.endswith(".txt"):
                    transcript = uploaded_file.read().decode("utf-8")
                else:
                    transcript = MockAIService.transcribe_audio(None, scenario=mock_scenario)
                
                extracted_data = MockAIService.extract_data(transcript, scenario=mock_scenario)
            else:
                try:
                    service = RealAIService(api_key)
                    
                    if uploaded_file.name.endswith(".txt"):
                        # Direct Text Input - Skip Whisper
                        transcript = uploaded_file.read().decode("utf-8")
                    else:
                        # Audio Input - Use Whisper
                        transcript = service.transcribe_audio(uploaded_file)
                    
                    extracted_data = service.extract_data(transcript)
                except Exception as e:
                    error_str = str(e)
                    if "403" in error_str and "model_not_found" in error_str:
                        st.error("🚨 Access Denied to 'whisper-1' model.")
                        st.warning("""
                        **Solution:**
                        1. Go to your OpenAI Dashboard > Settings > Projects.
                        2. Select your Project.
                        3. Go to **Models** and ensure `whisper-1` is enabled/allowed.
                        4. Or use a different API Key (e.g. from a 'Default' project).
                        """)
                    else:
                        st.error(f"Error calling OpenAI: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                    st.stop()

            st.text_area("Live Transcript", transcript, height=300)
            
            st.session_state['transcript'] = transcript
            st.session_state['extracted_data'] = extracted_data

with col2:
    st.header("2. Eligibility Review")
    
    if 'extracted_data' in st.session_state:
        data = st.session_state['extracted_data']
        
        st.subheader("Extracted Data")
        st.json(data)
        
        st.subheader("I/E Checklist")
        results, overall_eligible = RuleEngine.check_eligibility(data)
        
        if overall_eligible:
            st.success("✅ Patient is ELIGIBLE based on checked criteria.")
        else:
            st.error("❌ Patient is NOT ELIGIBLE.")
        
        df_results = pd.DataFrame(results)
        st.table(df_results)
        
        st.subheader("Washout Calculator")
        if data.get("last_dose"):
            ld = data["last_dose"]
            try:
                date_obj = datetime.strptime(ld["date"], "%Y-%m-%d")
                washout_info = WashoutCalculator.calculate_end_date(ld["medication"], date_obj)
                
                st.info(f"Medication: {washout_info['medication']}")
                st.info(f"Washout Period: {washout_info['washout_days']} days")
                st.success(f"Earliest Run-In Date: {washout_info['end_date'].strftime('%Y-%m-%d')}")
            except Exception as e:
                st.error(f"Error calculating washout: {e}")

        st.divider()
        st.header("3. Source Document Generation")
        
        template_path = "[Internal] of Astria STAR 0215-301 Day 1.docx"
        if os.path.exists(template_path):
             if st.button("Auto-Fill Day 1 Visit Form"):
                filler = FormFiller(template_path)
                filled_doc = filler.fill_form(data, is_eligible=overall_eligible)
                
                st.download_button(
                    label="Download Filled Form (DOCX)",
                    data=filled_doc,
                    file_name=f"Day1_Visit_Filled_{datetime.now().strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                st.success("Form generated! Click above to download.")
        else:
            st.warning(f"Template file not found: {template_path}")
