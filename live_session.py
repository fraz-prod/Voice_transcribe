"""
live_session.py — Live Pre-Screen Call Session UI

A dedicated Streamlit page for real-time I/E categorization during
a live phone pre-screen call. Ninna records audio chunks one at a time
via the browser mic. Each chunk is transcribed locally by Whisper.
Every 3 chunks, Gemini evaluates the I/E checklist and updates the panel.

Tabs:
  📋 Call Script   — Gemini-generated script Ninna reads during the call
  🎙️ Live Session  — Two-column: transcript left, I/E checklist right
"""

import streamlit as st
from ai_services import LiveSessionService

# ── Constants ─────────────────────────────────────────────────────────────────

STATUS_EMOJI = {
    "confirmed_met":        "✅",
    "confirmed_failed":     "❌",
    "open":                 "⚪",
    "needs_clarification":  "⚠️",
    "compliant":            "✅",
    "non_compliant":        "❌",
    "unclear":              "⚠️",
}

OVERALL_BANNER = {
    "likely_eligible":     ("✅ Likely Eligible", "success"),
    "likely_ineligible":   ("❌ Likely Ineligible — review required", "error"),
    "too_early_to_tell":   ("⏳ Still gathering information…", "info"),
}

# ── Session state helpers ─────────────────────────────────────────────────────

def _init_session():
    defaults = {
        "live_transcript":   "",
        "ie_status":         None,
        "chunk_count":       0,
        "last_ie_chunk":     -1,
        "call_script":       None,   # Generated script text
        "script_generated":  False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── I/E Panel ─────────────────────────────────────────────────────────────────

def _render_ie_panel(ie_status: dict):
    if not ie_status:
        st.info("⏳ I/E status will update after your first recording chunk.")
        return

    summary = ie_status.get("summary", {})
    overall = summary.get("overall_status", "too_early_to_tell")
    banner_text, banner_kind = OVERALL_BANNER.get(overall, OVERALL_BANNER["too_early_to_tell"])
    getattr(st, banner_kind)(banner_text)

    col1, col2 = st.columns(2)
    col1.metric("⚪ Open", summary.get("open_count", 0))
    col2.metric("❌ Failed", summary.get("failed_count", 0))

    concerns = summary.get("key_concerns", [])
    if concerns:
        st.warning("**Key concerns:**\n\n" + "\n".join(f"- {c}" for c in concerns))

    st.divider()

    # Inclusion
    inclusion = ie_status.get("inclusion_criteria", [])
    if inclusion:
        st.markdown("### 🟢 Inclusion Criteria")
        for item in inclusion:
            status    = item.get("status", "open")
            emoji     = STATUS_EMOJI.get(status, "⚪")
            criterion = item.get("criterion", "Unknown")
            evidence  = item.get("evidence")
            action    = item.get("action_needed")
            with st.expander(f"{emoji} {criterion}",
                             expanded=(status in ("confirmed_failed", "needs_clarification", "open"))):
                if evidence:
                    st.caption(f"📋 {evidence}")
                if action:
                    st.info(f"💬 Ask: *{action}*")
                if status == "confirmed_met":
                    st.success("Confirmed ✅")
                elif status == "confirmed_failed":
                    st.error("Failed ❌")
                elif status == "needs_clarification":
                    st.warning("Needs clarification ⚠️")
                else:
                    st.info("Not yet discussed ⚪")

    st.divider()

    # Exclusion
    exclusion = ie_status.get("exclusion_criteria", [])
    if exclusion:
        st.markdown("### 🔴 Exclusion Criteria")
        for item in exclusion:
            status    = item.get("status", "open")
            emoji     = "❌" if status == "confirmed_met" else ("✅" if status == "confirmed_failed" else STATUS_EMOJI.get(status, "⚪"))
            criterion = item.get("criterion", "Unknown")
            evidence  = item.get("evidence")
            action    = item.get("action_needed")
            with st.expander(f"{emoji} {criterion}",
                             expanded=(status in ("confirmed_met", "needs_clarification"))):
                if evidence:
                    st.caption(f"📋 {evidence}")
                if action:
                    st.info(f"💬 Ask: *{action}*")
                if status == "confirmed_met":
                    st.error("⚠️ Exclusion TRIGGERED")
                elif status == "confirmed_failed":
                    st.success("✅ Clear")
                elif status == "needs_clarification":
                    st.warning("⚠️ Needs clarification")
                else:
                    st.info("Not yet discussed ⚪")

    # Washout
    washout = ie_status.get("washout_flags", [])
    if washout:
        st.divider()
        st.markdown("### 💊 Washout Flags")
        for w in washout:
            med     = w.get("medication", "Unknown")
            wstatus = w.get("status", "unclear")
            days    = w.get("washout_days_required")
            date    = w.get("last_dose_date")
            note    = w.get("note", "")
            emoji   = STATUS_EMOJI.get(wstatus, "⚠️")
            with st.expander(f"{emoji} {med}", expanded=(wstatus == "non_compliant")):
                if days:
                    st.caption(f"⏱️ Required washout: {days} days")
                if date:
                    st.caption(f"📅 Last dose: {date}")
                if note:
                    if wstatus == "non_compliant":
                        st.error(note)
                    elif wstatus == "compliant":
                        st.success(note)
                    else:
                        st.warning(note)

# ── Script Tab ────────────────────────────────────────────────────────────────

def _render_script_tab(api_key: str, protocol_text: str):
    st.subheader("📋 Pre-Screen Call Script")
    st.caption("A structured script for Ninna to read aloud during the patient call. Generated from the study protocol's I/E criteria.")

    has_protocol = bool(protocol_text and protocol_text.strip())
    has_api_key  = bool(api_key and api_key.strip())

    if not has_protocol:
        st.warning("⚠️ Upload the protocol in the sidebar to generate a protocol-specific script.")

    if not has_api_key:
        st.error("⚠️ Gemini API key required to generate the script.")
        return

    col1, col2 = st.columns([2, 1])
    with col1:
        regen = st.button(
            "🔄 Regenerate Script" if st.session_state.script_generated else "✨ Generate Call Script",
            use_container_width=True,
            type="primary"
        )
    with col2:
        if st.session_state.call_script:
            st.download_button(
                "⬇️ Download Script (.md)",
                data=st.session_state.call_script,
                file_name="prescreening_call_script.md",
                mime="text/markdown",
                use_container_width=True
            )

    if regen:
        with st.spinner("✨ Generating call script from protocol…"):
            service = LiveSessionService(api_key)
            st.session_state.call_script = service.generate_prescreening_script(
                protocol_text if has_protocol else ""
            )
            st.session_state.script_generated = True
        st.rerun()

    if st.session_state.call_script:
        st.divider()
        # Render script with nice styling
        st.markdown(st.session_state.call_script)
    elif not regen:
        # Show a placeholder before generation
        st.info(
            "👆 Click **Generate Call Script** to create a structured script from the protocol.\n\n"
            "The script will include:\n"
            "- 📞 Opening introduction\n"
            "- ✅ Inclusion criteria questions (with PASS criteria)\n"
            "- ❌ Exclusion criteria questions (with FAIL criteria)\n"
            "- 💊 Medication & washout questions (with specific days from protocol)\n"
            "- 📋 Call closing and next steps"
        )

# ── Main render function ──────────────────────────────────────────────────────

def render(api_key: str, protocol_text: str, whisper_model=None):
    """
    Main entry point called from app.py when Live Pre-Screen mode is selected.
    """
    _init_session()

    st.title("🎙️ Live Pre-Screen Call Session")

    if not api_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar before starting.")
        return

    if not protocol_text:
        st.warning(
            "⚠️ **No protocol uploaded.** Gemini will use general clinical trial knowledge. "
            "Upload the protocol `.md` file in the sidebar for accurate results."
        )

    # Reset button in top-right
    top_col1, top_col2 = st.columns([5, 1])
    with top_col2:
        if st.button("🔄 Reset", help="Clear transcript and I/E status"):
            for k in ["live_transcript", "ie_status", "chunk_count", "last_ie_chunk"]:
                st.session_state[k] = "" if k == "live_transcript" else (None if k == "ie_status" else -1 if k == "last_ie_chunk" else 0)
            st.rerun()
    with top_col1:
        st.caption(f"Chunks recorded: **{st.session_state.chunk_count}** | "
                   f"Protocol: {'✅ Loaded' if protocol_text else '⚠️ Not loaded'}")

    st.divider()

    # ── Tabs ──────────────────────────────────────────────────────────────────
    tab_script, tab_live = st.tabs(["📋 Call Script", "🎙️ Live Session"])

    # ── Tab 1: Script ─────────────────────────────────────────────────────────
    with tab_script:
        _render_script_tab(api_key, protocol_text)

    # ── Tab 2: Live Session ───────────────────────────────────────────────────
    with tab_live:
        left_col, right_col = st.columns([6, 4])

        # LEFT: Recording + Transcript
        with left_col:
            st.subheader("📝 Live Transcript")

            audio_data = st.audio_input(
                "🎙️ Click to record a chunk (speak for 15–30 seconds, then stop)",
                key=f"audio_chunk_{st.session_state.chunk_count}"
            )

            if audio_data is not None:
                with st.spinner("🎧 Transcribing with Whisper…"):
                    audio_bytes = audio_data.read()
                    chunk_text  = LiveSessionService.transcribe_chunk(audio_bytes, whisper_model)

                if chunk_text and not chunk_text.startswith("["):
                    st.session_state.live_transcript += (
                        (" " if st.session_state.live_transcript else "") + chunk_text
                    )
                    st.session_state.chunk_count += 1

                    # Auto I/E check every 3 chunks
                    should_run_ie = (
                        st.session_state.chunk_count > st.session_state.last_ie_chunk and
                        st.session_state.chunk_count % LiveSessionService.IE_CHECK_EVERY_N_CHUNKS == 0
                    )
                    if should_run_ie:
                        with st.spinner("🤖 Updating I/E checklist…"):
                            svc = LiveSessionService(api_key)
                            st.session_state.ie_status = svc.run_ie_check(
                                st.session_state.live_transcript, protocol_text
                            )
                            st.session_state.last_ie_chunk = st.session_state.chunk_count

                    st.success(f"✅ Chunk {st.session_state.chunk_count} transcribed")
                    st.rerun()
                else:
                    st.warning(f"⚠️ Transcription issue: {chunk_text}")

            # Manual I/E trigger
            if st.session_state.live_transcript:
                if st.button("🔁 Run I/E Check Now"):
                    with st.spinner("🤖 Running I/E check…"):
                        svc = LiveSessionService(api_key)
                        st.session_state.ie_status = svc.run_ie_check(
                            st.session_state.live_transcript, protocol_text
                        )
                        st.session_state.last_ie_chunk = st.session_state.chunk_count
                    st.rerun()

            transcript = st.session_state.live_transcript
            if transcript:
                st.markdown("---")
                st.text_area(
                    label="transcript",
                    value=transcript,
                    height=380,
                    label_visibility="hidden",
                    disabled=True
                )
                ie_chunk = st.session_state.last_ie_chunk
                next_check = ((ie_chunk // LiveSessionService.IE_CHECK_EVERY_N_CHUNKS) + 1) * LiveSessionService.IE_CHECK_EVERY_N_CHUNKS
                remaining  = next_check - st.session_state.chunk_count
                if remaining > 0 and ie_chunk >= 0:
                    st.caption(f"⏱️ Next auto I/E check in **{remaining}** more chunk(s)")
            else:
                st.info("Record your first chunk above to begin.")

        # RIGHT: I/E Checklist
        with right_col:
            st.subheader("✅ I/E Checklist (Live)")
            _render_ie_panel(st.session_state.ie_status)
