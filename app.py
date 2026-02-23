import streamlit as st
import pandas as pd
from datetime import datetime
from logic import WashoutCalculator, RuleEngine
from ai_services import MockAIService, RealAIService, LocalAIService, LocalWhisperService, GeminiAIService, Chirp3GeminiService, LiveSessionService
import live_session
from form_filler import FormFiller
import os

# --- HOTFIX: Add FFmpeg to PATH programmatically ---
# We found it in Downloads, so we add it here to ensure pydub/whisper can find it.
ffmpeg_path = r"c:\Users\RagaAI_User\Downloads\ffmpeg-8.0.1-essentials_build\ffmpeg-8.0.1-essentials_build\bin"
if os.path.exists(ffmpeg_path):
    os.environ["PATH"] += os.pathsep + ffmpeg_path
# ---------------------------------------------------

@st.cache_resource
def get_faster_whisper_model():
    from faster_whisper import WhisperModel
    import torch
    
    model_size = "medium"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if device == "cuda" else "int8"
    
    print(f"Initializing Faster-Whisper model ({model_size}) on {device}...")
    return WhisperModel(model_size, device=device, compute_type=compute_type)

st.set_page_config(layout="wide", page_title="Eligibility Screening Assistant")

st.title("Voice-Enabled Eligibility Screening Assistant")

# Pre-initialize Whisper model at startup
@st.cache_data
def check_model_initialized():
    return True

if check_model_initialized():
    # This will trigger model loading when the mode is selected
    pass

# Sidebar for controls
st.sidebar.header("Controls")
mode = st.sidebar.selectbox("Mode", ["Mock Mode", "Local Mode (No LLM)", "Local Whisper Mode (No API Key)", "Gemini Mode (Gemini API)", "Chirp 3 Mode (Google Cloud)", "🎙️ Live Pre-Screen Call"])

# Pre-load Whisper model if in Whisper mode
if mode == "Local Whisper Mode (No API Key)":
    with st.sidebar:
        with st.spinner("🔄 Initializing Whisper model..."):
            whisper_model = get_faster_whisper_model()
        st.success("✅ Whisper model ready!")
else:
    whisper_model = None

mock_scenario = "Eligible (Happy Path)"
if mode == "Mock Mode":
    mock_scenario = st.sidebar.selectbox("Test Scenario", list(MockAIService.SCENARIOS.keys()))

api_key = None
gemini_api_key = None
gcp_project_id = None
gcp_region = "us"
gcp_credentials_path = None

import os
from dotenv import load_dotenv
load_dotenv()

if mode == "🎙️ Live Pre-Screen Call":
    default_key = os.getenv("GEMINI_API_KEY", "")
    gemini_api_key = st.sidebar.text_input("Gemini API Key", value=default_key, type="password", key="live_gemini_key")
    st.sidebar.divider()
    st.sidebar.subheader("📄 Protocol Document")
    uploaded_protocol = st.sidebar.file_uploader(
        "Upload Protocol (.md or PDF)",
        type=["pdf", "md"],
        key="live_protocol_upload",
        help="Upload the study protocol — used for real-time I/E criterion checking during the call."
    )
    if uploaded_protocol:
        file_ext = uploaded_protocol.name.split('.')[-1].lower()
        st.sidebar.success(f"📋 Protocol loaded: {uploaded_protocol.name}")
    if not gemini_api_key:
        st.sidebar.warning("⚠️ Enter Gemini API Key to enable I/E checking.")

if mode == "Gemini Mode (Gemini API)":
    default_key = os.getenv("GEMINI_API_KEY", "")
    gemini_api_key = st.sidebar.text_input("Gemini API Key", value=default_key, type="password")
    if not gemini_api_key:
        st.warning("Please enter your Gemini API Key to use Gemini Mode.")
    st.sidebar.divider()
    st.sidebar.subheader("📄 Protocol Document (Optional)")
    uploaded_protocol = st.sidebar.file_uploader(
        "Upload Protocol (PDF or Markdown)",
        type=["pdf", "md"],
        key="sidebar_protocol_pdf",
        help="Upload the protocol PDF or an OCR-generated .md file. The relevant sections will be sent to Gemini for protocol-aware extraction."
    )
    if uploaded_protocol:
        file_ext = uploaded_protocol.name.split('.')[-1].lower()
        icon = "📋" if file_ext == "md" else "📄"
        st.sidebar.success(f"{icon} Protocol loaded: {uploaded_protocol.name}")
        if file_ext == "md":
            st.sidebar.info("ℹ️ MD file: smart section extraction will be used (no context window limit concerns)")

if mode == "Chirp 3 Mode (Google Cloud)":
    st.sidebar.subheader("Google Cloud Settings")
    default_gemini_key = os.getenv("GEMINI_API_KEY", "")
    gemini_api_key = st.sidebar.text_input("Gemini API Key", value=default_gemini_key, type="password", key="chirp_gemini_key")
    gcp_project_id = st.sidebar.text_input("GCP Project ID", value=os.getenv("GOOGLE_CLOUD_PROJECT", ""), key="gcp_project")
    gcp_region = st.sidebar.selectbox("GCP Region", Chirp3GeminiService.SUPPORTED_REGIONS, index=0, key="gcp_region")
    gcp_credentials_path = st.sidebar.text_input(
        "Service Account JSON Path (optional)",
        value=os.getenv("GOOGLE_APPLICATION_CREDENTIALS", ""),
        help="Leave blank if using Application Default Credentials",
        key="gcp_creds"
    )
    if not gemini_api_key:
        st.warning("Please enter your Gemini API Key.")
    if not gcp_project_id:
        st.warning("Please enter your GCP Project ID.")

# ── Live Pre-Screen Call — full-page mode, skip normal two-column layout ────
if mode == "🎙️ Live Pre-Screen Call":
    # Parse protocol if one was uploaded
    live_protocol_text = ""
    if 'uploaded_protocol' in dir() and uploaded_protocol is not None:
        try:
            file_ext = uploaded_protocol.name.split('.')[-1].lower()
            if file_ext == "md":
                live_protocol_text = GeminiAIService.parse_protocol_md(uploaded_protocol)
            else:
                live_protocol_text = GeminiAIService.parse_protocol_pdf(uploaded_protocol)
        except Exception as e:
            st.error(f"Error reading protocol: {e}")
    live_session.render(
        api_key=gemini_api_key or "",
        protocol_text=live_protocol_text,
        whisper_model=get_faster_whisper_model()
    )
    st.stop()   # Don't render the file-upload UI below

col1, col2 = st.columns(2)

with col1:
    st.header("1. Call Recording/Transcription")
    uploaded_file = st.file_uploader("Upload Audio or Text Transcript", type=["wav", "mp3", "txt"])
    
    # Use button to trigger processing, not automatic on file upload
    process_button = st.button("Start Processing")
    
    # Only process if button is clicked AND file is uploaded
    if process_button and uploaded_file:
        if mode == "Live Mode (Requires API Key)" and not api_key:
            st.error("API Key missing.")
            st.stop()
        
        if mode == "Gemini Mode (Gemini API)" and not gemini_api_key:
            st.error("Gemini API Key missing.")
            st.stop()
            
        with st.spinner("Processing..."):
            if mode == "Mock Mode":
                # Check if user uploaded a text file override
                if uploaded_file and uploaded_file.name.endswith(".txt"):
                    transcript = uploaded_file.read().decode("utf-8")
                else:
                    transcript = MockAIService.transcribe_audio(None, scenario=mock_scenario)
                
                extracted_data = MockAIService.extract_data(transcript, scenario=mock_scenario)

            elif mode == "Local Mode (No LLM)":
                 # Local Mode execution
                if uploaded_file.name.endswith(".txt"):
                    transcript = uploaded_file.read().decode("utf-8")
                else:
                    # Audio Input - Use LocalAIService (SpeechRecognition)
                    transcript = LocalAIService.transcribe_audio(uploaded_file)
                
                extracted_data = LocalAIService.extract_data(transcript)

            
            elif mode == "Local Whisper Mode (No API Key)":
                 # Local Whisper execution
                if uploaded_file.name.endswith(".txt"):
                    transcript = uploaded_file.read().decode("utf-8")
                else:
                    # Audio Input - Use LocalWhisperService with Pre-loaded Model
                    try:
                        # Use the pre-loaded model from sidebar
                        transcript_placeholder = st.empty()
                        transcript_placeholder.info("🎙️ Transcribing audio... This will show live updates.")
                        
                        transcript = LocalWhisperService.transcribe_audio(
                            uploaded_file, 
                            model=whisper_model,
                            streaming_callback=lambda text: transcript_placeholder.text_area(
                                "Live Transcript (Streaming)", text, height=300, key=f"stream_{len(text)}"
                            )
                        )
                        transcript_placeholder.empty()  # Clear the placeholder
                    except Exception as e:
                         st.error(f"Error transcribing: {e}")
                         st.stop()
                
                extracted_data = LocalWhisperService.extract_data(transcript)
            
            elif mode == "Gemini Mode (Gemini API)":
                # Gemini Mode execution
                if not gemini_api_key:
                    st.error("Gemini API Key missing.")
                    st.stop()
                
                try:
                    service = GeminiAIService(gemini_api_key)
                    
                    if uploaded_file.name.endswith(".txt"):
                        # Direct Text Input
                        transcript = uploaded_file.read().decode("utf-8")
                    else:
                        # For audio, use Local Whisper for transcription
                        # Initialize Whisper model if needed
                        if whisper_model is None:
                            with st.spinner("🔄 Loading Whisper model for transcription..."):
                                whisper_model = get_faster_whisper_model()
                        
                        # Live streaming transcript placeholder
                        transcript_placeholder = st.empty()
                        transcript_placeholder.info("🎙️ Transcribing audio... Live transcript will appear below.")
                        
                        transcript = LocalWhisperService.transcribe_audio(
                            uploaded_file,
                            model=whisper_model,
                            streaming_callback=lambda text: transcript_placeholder.text_area(
                                "🎙️ Live Transcript (Streaming)",
                                text,
                                height=300,
                                key=f"gemini_stream_{len(text)}"
                            )
                        )
                        transcript_placeholder.empty()  # Clear live view once done
                    
                    # Parse protocol document if uploaded (PDF or MD)
                    protocol_text = ""
                    if uploaded_protocol:
                        file_ext = uploaded_protocol.name.split('.')[-1].lower()
                        if file_ext == "md":
                            with st.spinner("📋 Extracting relevant sections from protocol Markdown..."):
                                protocol_text = GeminiAIService.parse_protocol_md(uploaded_protocol)
                            st.info(f"📋 Protocol MD loaded — {len(protocol_text):,} characters of relevant sections extracted (eligibility, washout, assessments). Gemini will cross-reference this.")
                        else:
                            with st.spinner("📄 Reading protocol PDF..."):
                                protocol_text = GeminiAIService.parse_protocol_pdf(uploaded_protocol)
                            st.info(f"📄 Protocol PDF loaded — {len(protocol_text):,} characters extracted. Gemini will cross-reference this.")

                    # Use Gemini for extraction (with optional protocol context)
                    with st.spinner("🤖 Extracting data with Gemini AI..."):
                        extracted_data = service.extract_data(transcript, protocol_text=protocol_text)
                except ImportError as e:
                    st.error("❌ google-generativeai not installed. Please run: pip install google-generativeai")
                    st.stop()
                except Exception as e:
                    st.error(f"Error calling Gemini API: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.stop()

            elif mode == "Chirp 3 Mode (Google Cloud)":
                # Chirp 3 + Gemini 2.5 Flash Mode
                if not gemini_api_key:
                    st.error("Gemini API Key missing.")
                    st.stop()
                if not gcp_project_id:
                    st.error("GCP Project ID missing.")
                    st.stop()

                try:
                    service = Chirp3GeminiService(
                        gemini_api_key=gemini_api_key,
                        project_id=gcp_project_id,
                        region=gcp_region,
                        credentials_path=gcp_credentials_path or None,
                    )

                    if uploaded_file.name.endswith(".txt"):
                        transcript = uploaded_file.read().decode("utf-8")
                    else:
                        status_placeholder = st.empty()
                        def update_status(msg):
                            status_placeholder.info(f"🎙️ {msg}")

                        transcript = service.transcribe_audio(
                            uploaded_file,
                            progress_callback=update_status
                        )
                        status_placeholder.empty()

                    with st.spinner("🤖 Extracting data with Gemini 2.5 Flash..."):
                        extracted_data = service.extract_data(transcript)

                except ImportError as e:
                    st.error(f"❌ Missing dependency: {e}")
                    st.info("Run: pip install google-cloud-speech google-generativeai")
                    st.stop()
                except Exception as e:
                    st.error(f"Error in Chirp 3 Mode: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.stop()

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
                        st.error(f"🚨 Access Denied to 'gpt-4o-transcribe' (or configured model). Details: {e}")
                        st.warning("""
                        **Solution:**
                        1. Go to your OpenAI Dashboard > Settings > Projects.
                        2. Select your Project.
                        3. Go to **Models** and ensure `gpt-4o-transcribe` is enabled/allowed.
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

        # --- Overflow / Validation Warnings ---
        validation = data.get("validation", {})
        overflow = data.get("overflow_information", {})
        has_overflow = any(overflow.get(k) for k in [
            "patient_concerns", "medication_questions",
            "unreported_symptoms", "safety_observations", "other_clinical_notes"
        ])

        if validation:
            score = validation.get("completeness_score", 100)
            if score >= 90:
                st.success(f"✅ Data completeness: {score}%")
            elif score >= 70:
                st.warning(f"⚠️ Data completeness: {score}% — review recommended")
            else:
                st.error(f"🔴 Data completeness: {score}% — manual review required")

        if has_overflow:
            with st.expander("⚠️ Additional Medical Information Captured (Beyond Protocol Fields)", expanded=True):
                if overflow.get("patient_concerns"):
                    st.markdown("**Patient Concerns:**")
                    for c in overflow["patient_concerns"]:
                        st.markdown(f"- {c}")
                if overflow.get("medication_questions"):
                    st.markdown("**Medication Questions:**")
                    for q in overflow["medication_questions"]:
                        st.markdown(f"- {q}")
                if overflow.get("unreported_symptoms"):
                    st.markdown("**Unreported Symptoms (not logged as AE):**")
                    for s in overflow["unreported_symptoms"]:
                        st.markdown(f"- {s}")
                if overflow.get("safety_observations"):
                    st.markdown("**Safety Observations:**")
                    for o in overflow["safety_observations"]:
                        st.markdown(f"- {o}")
                if overflow.get("other_clinical_notes"):
                    st.markdown("**Other Clinical Notes:**")
                    for n in overflow["other_clinical_notes"]:
                        st.markdown(f"- {n}")

        if validation.get("flags"):
            st.warning("**Flags:** " + " | ".join(validation["flags"]))

        # --- Protocol Compliance Section ---
        protocol_compliance = data.get("protocol_compliance", {})
        if protocol_compliance:
            st.divider()
            st.subheader("📋 Protocol Compliance Check")

            visit_type = protocol_compliance.get("visit_type_detected", "Unknown")
            st.info(f"**Visit Type Detected:** {visit_type}")

            # Protocol compliance score
            compliance_score = validation.get("protocol_compliance_score")
            if compliance_score is not None:
                if compliance_score >= 90:
                    st.success(f"✅ Protocol Compliance Score: {compliance_score}%")
                elif compliance_score >= 70:
                    st.warning(f"⚠️ Protocol Compliance Score: {compliance_score}%")
                else:
                    st.error(f"🔴 Protocol Compliance Score: {compliance_score}%")

            # Missing items — the most important part
            missing = protocol_compliance.get("missing_from_transcript", [])
            if missing:
                with st.expander(f"🔴 GAPS: {len(missing)} Protocol-Required Items Missing from Transcript", expanded=True):
                    for item in missing:
                        st.error(f"❌ {item}")
            else:
                st.success("✅ All protocol-required items were found in the transcript.")

            # Found items
            found = protocol_compliance.get("found_in_transcript", [])
            if found:
                with st.expander(f"✅ {len(found)} Protocol-Required Items Found", expanded=False):
                    for item in found:
                        st.markdown(f"- ✅ {item}")

            # Eligibility criteria
            elig = protocol_compliance.get("eligibility_criteria_checked", {})
            if elig:
                with st.expander("🔍 Eligibility Criteria Check", expanded=False):
                    if elig.get("inclusion_met"):
                        st.markdown("**Inclusion Criteria Met:**")
                        for item in elig["inclusion_met"]:
                            st.markdown(f"- ✅ {item}")
                    if elig.get("inclusion_not_confirmed"):
                        st.markdown("**Inclusion Criteria NOT Confirmed (needs verification):**")
                        for item in elig["inclusion_not_confirmed"]:
                            st.markdown(f"- ⚠️ {item}")
                    if elig.get("exclusion_clear"):
                        st.markdown("**Exclusion Criteria Clear:**")
                        for item in elig["exclusion_clear"]:
                            st.markdown(f"- ✅ {item}")
                    if elig.get("exclusion_flagged"):
                        st.markdown("**Exclusion Criteria FLAGGED (needs review):**")
                        for item in elig["exclusion_flagged"]:
                            st.markdown(f"- 🔴 {item}")

            # Washout compliance
            washout = protocol_compliance.get("washout_compliance", "")
            if washout:
                st.info(f"💊 **Washout Compliance:** {washout}")

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

        # Get protocol-extracted washout periods (from Gemini) if available
        # Pass None if list is empty so WashoutCalculator treats it as "no protocol"
        protocol_washout_raw = data.get("protocol_compliance", {}).get("washout_periods", [])
        protocol_washout = protocol_washout_raw if protocol_washout_raw else None

        last_dose = data.get("last_dose")           # single {medication, date} from transcript
        medications = data.get("medications", [])   # full list of medications patient is on

        # ── Build a unified list of all medications to display ──────────────────
        # Start with last_dose (has a date → can compute clearance date)
        # Then add remaining medications from the medications list

        def _parse_date(date_str: str):
            """Try common date formats, return datetime or None."""
            for fmt in ("%Y-%m-%d", "%d %B %Y", "%B %d, %Y", "%d/%m/%Y"):
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue
            return None

        # Dict: med_name → last_dose_date (or None if we don't know the date)
        med_entries: dict = {}

        if last_dose and last_dose.get("medication"):
            med_name = last_dose["medication"]
            date_str  = last_dose.get("date", "")
            med_entries[med_name] = _parse_date(date_str) if date_str else None

        # Add remaining medications from the medications list (no date known)
        for med in (medications or []):
            if med and med not in med_entries:
                med_entries[med] = None

        if not med_entries:
            st.info("ℹ️ No medication or last dose information found in transcript.")
        else:
            if protocol_washout is None:
                st.warning("⚠️ No protocol uploaded — washout periods below are **hardcoded estimates**, not protocol-defined.")

            for med_name, dose_date in med_entries.items():
                with st.expander(f"💊 {med_name}", expanded=True):
                    washout_info = WashoutCalculator.calculate_end_date(med_name, dose_date or datetime.today(), protocol_washout)
                    source   = washout_info.get("source")
                    days     = washout_info.get("washout_days")
                    end_date = washout_info.get("end_date")

                    # Source label
                    if source == "protocol":
                        matched_as = washout_info.get("matched_as", "")
                        alias_note = f" *(matched as: {matched_as})*" if matched_as and "→" in matched_as else ""
                        st.success(f"📋 Source: **Protocol Document**{alias_note}")
                    elif source == "not_in_protocol":
                        st.warning("📋 Source: **Not found in protocol** — no washout required by protocol, or Gemini did not extract it.")
                    else:
                        st.warning("📋 Source: **Hardcoded estimate** — upload protocol for accurate value.")

                    # Washout days
                    if days is not None and days > 0:
                        st.info(f"⏱️ **Required Washout:** {days} days")
                    elif days == 0:
                        st.info("⏱️ **Required Washout:** 0 days (no washout required)")

                    # Clearance date — only if we have the actual last dose date
                    if dose_date and days is not None:
                        st.success(f"📅 **Last Dose Date:** {dose_date.strftime('%Y-%m-%d')}")
                        st.success(f"✅ **Earliest Eligible Date:** {end_date.strftime('%Y-%m-%d')}")
                    elif dose_date is None and days is not None and days > 0:
                        st.warning("📅 **Last dose date not found in transcript** — provide date to compute earliest eligible date.")
                    elif source == "not_in_protocol":
                        st.info("📅 No clearance date calculated — medication not in protocol washout list.")

        st.divider()
        st.header("3. Source Document Generation")
        
        # File Uploader for Template
        st.subheader("Configuration")
        uploaded_template = st.file_uploader("Upload Form Template (DOCX)", type=["docx"])

        # Default template path
        default_template_path = "[Internal] of Astria STAR 0215-301 Day 1.docx"
        
        # Determine strict template to use
        template_to_use = None
        if uploaded_template:
            template_to_use = uploaded_template
        elif os.path.exists(default_template_path):
            template_to_use = default_template_path
        
        if template_to_use:
             if st.button("Auto-Fill Day 1 Visit Form"):
                filler = FormFiller(template_to_use)
                filled_doc = filler.fill_form(data, is_eligible=overall_eligible)
                
                st.download_button(
                    label="Download Filled Form (DOCX)",
                    data=filled_doc,
                    file_name=f"Day1_Visit_Filled_{datetime.now().strftime('%Y%m%d')}.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                )
                st.success("Form generated! Click above to download.")
        else:
             st.warning(f"Template file not found: {default_template_path}. Please upload a template.")
