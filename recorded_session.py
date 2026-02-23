"""
recorded_session.py — Recorded Call I/E Analysis

Ninna uploads a recorded call (.wav / .mp3) or a plain text transcript (.txt).
The app:
  1. Transcribes audio locally with Whisper (if audio uploaded)
  2. Generates the structured script from the protocol (if not already done)
  3. Runs a full I/E check + fills every script answer card in one shot
  4. Shows the completed interactive script + I/E checklist side by side

No chunking needed — the whole transcript is processed at once.
"""

import streamlit as st
from ai_services import LiveSessionService

# ── Re-use the same visual helpers from live_session ──────────────────────────

STATUS_EMOJI = {
    "confirmed_met":       "✅",
    "confirmed_failed":    "❌",
    "open":                "⚪",
    "needs_clarification": "⚠️",
    "compliant":           "✅",
    "non_compliant":       "❌",
    "unclear":             "⚠️",
}

SECTION_LABEL = {
    "inclusion": ("🟢", "Inclusion"),
    "exclusion": ("🔴", "Exclusion"),
    "washout":   ("💊", "Washout"),
    "general":   ("📋", "General"),
}

OVERALL_BANNER = {
    "likely_eligible":   ("✅ Likely Eligible", "success"),
    "likely_ineligible": ("❌ Likely Ineligible — review required", "error"),
    "too_early_to_tell": ("⏳ Could not determine eligibility", "info"),
}

# ── Session state ──────────────────────────────────────────────────────────────

def _init():
    defaults = {
        "rec_transcript":      "",
        "rec_ie_status":       None,
        "rec_script_data":     None,
        "rec_manual_overrides": {},
        "rec_manual_notes":    "",
        "rec_processed":       False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def _reset():
    for k in ["rec_transcript", "rec_ie_status", "rec_script_data",
              "rec_manual_overrides", "rec_manual_notes", "rec_processed"]:
        st.session_state[k] = (
            "" if k in ("rec_transcript", "rec_manual_notes") else
            None if k in ("rec_ie_status", "rec_script_data") else
            {} if k == "rec_manual_overrides" else False
        )

# ── Helpers ────────────────────────────────────────────────────────────────────

def _answer_badge(q: dict) -> str:
    status  = q.get("status", "open")
    section = q.get("section", "general")
    if section == "exclusion":
        return {"confirmed_met": "❌ TRIGGERED", "confirmed_failed": "✅ Clear"}.get(status, STATUS_EMOJI.get(status, "⚪") + " " + status.replace("_", " ").title())
    return {"confirmed_met": "✅ PASS", "confirmed_failed": "❌ FAIL", "needs_clarification": "⚠️ Clarify"}.get(status, "⚪ Open")


def _build_manual_ctx() -> str:
    parts = []
    for q in (st.session_state.rec_script_data or {}).get("questions", []):
        ov = st.session_state.rec_manual_overrides.get(q.get("id",""), "").strip()
        if ov:
            parts.append(f"- {q.get('criterion', q['id'])}: {ov}")
    if st.session_state.rec_manual_notes.strip():
        parts.append(f"Additional notes: {st.session_state.rec_manual_notes}")
    return "\n".join(parts)

# ── I/E panel ──────────────────────────────────────────────────────────────────

def _render_ie(ie_status: dict):
    if not ie_status:
        st.info("Process a call above to see the I/E analysis.")
        return

    summary = ie_status.get("summary", {})
    overall = summary.get("overall_status", "too_early_to_tell")
    text, kind = OVERALL_BANNER.get(overall, OVERALL_BANNER["too_early_to_tell"])
    getattr(st, kind)(text)

    c1, c2 = st.columns(2)
    c1.metric("⚪ Open", summary.get("open_count", 0))
    c2.metric("❌ Failed", summary.get("failed_count", 0))

    concerns = summary.get("key_concerns", [])
    if concerns:
        st.warning("**Key concerns:**\n\n" + "\n".join(f"- {c}" for c in concerns))

    st.divider()

    for ie_key, header in [("inclusion_criteria", "### 🟢 Inclusion"),
                            ("exclusion_criteria", "### 🔴 Exclusion")]:
        items = ie_status.get(ie_key, [])
        if not items:
            continue
        st.markdown(header)
        for item in items:
            status  = item.get("status", "open")
            section = "exclusion" if "exclusion" in ie_key else "inclusion"
            if section == "exclusion":
                emoji = "❌" if status == "confirmed_met" else ("✅" if status == "confirmed_failed" else STATUS_EMOJI.get(status, "⚪"))
            else:
                emoji = STATUS_EMOJI.get(status, "⚪")
            with st.expander(f"{emoji} {item.get('criterion','?')}",
                             expanded=(status in ("confirmed_met" if section=="exclusion" else "confirmed_failed",
                                                   "needs_clarification", "open"))):
                if item.get("evidence"):
                    st.caption(f"📋 {item['evidence']}")
                if item.get("action_needed"):
                    st.info(f"💬 *{item['action_needed']}*")
        st.divider()

    washout = ie_status.get("washout_flags", [])
    if washout:
        st.markdown("### 💊 Washout")
        for w in washout:
            ws = w.get("status", "unclear")
            with st.expander(f"{STATUS_EMOJI.get(ws,'⚠️')} {w.get('medication','?')}",
                             expanded=(ws == "non_compliant")):
                if w.get("washout_days_required"):
                    st.caption(f"⏱️ Required: {w['washout_days_required']} days")
                if w.get("last_dose_date"):
                    st.caption(f"📅 Last dose: {w['last_dose_date']}")
                if w.get("note"):
                    {"non_compliant": st.error, "compliant": st.success}.get(ws, st.warning)(w["note"])

# ── Script cards ───────────────────────────────────────────────────────────────

def _render_script_cards(api_key: str, protocol_text: str):
    data      = st.session_state.rec_script_data or {}
    questions = data.get("questions", [])

    if not questions:
        st.info("Generate the script or process the call to see question cards.")
        return

    # Controls
    col_gen, col_fill, col_dl = st.columns([2, 2, 1])
    with col_gen:
        if st.button("🔄 Regen Script", use_container_width=True):
            with st.spinner("✨ Regenerating…"):
                svc = LiveSessionService(api_key)
                st.session_state.rec_script_data = svc.generate_script_structured(
                    protocol_text or ""
                )
                st.session_state.rec_manual_overrides = {}
            st.rerun()

    with col_fill:
        transcript = st.session_state.rec_transcript
        manual_ctx = _build_manual_ctx()
        can_fill = bool(transcript.strip() or manual_ctx.strip())
        if st.button("🔁 Re-fill Answers", use_container_width=True, disabled=not can_fill):
            with st.spinner("🤖 Re-extracting answers…"):
                svc = LiveSessionService(api_key)
                updated = svc.extract_script_answers(
                    questions, transcript, manual_ctx
                )
                st.session_state.rec_script_data["questions"] = updated
            st.rerun()

    with col_dl:
        lines = [f"# Pre-Screen Script\n\n## Opening\n{data.get('opening','')}\n"]
        last_sec = None
        for q in questions:
            sec = q.get("section", "general")
            if sec != last_sec:
                icon, label = SECTION_LABEL.get(sec, ("📋", sec.title()))
                lines.append(f"\n## {icon} {label}\n")
                last_sec = sec
            ans = (st.session_state.rec_manual_overrides.get(q.get("id",""), "").strip()
                   or q.get("answer") or "________________")
            lines += [f"**{q.get('criterion','?')}**",
                      f"*Ninna says:* \"{q.get('ninna_says','')}\"",
                      f"📝 Answer: {ans}  [{_answer_badge(q)}]\n"]
        if st.session_state.rec_manual_notes:
            lines.append(f"\n## 📝 Notes\n{st.session_state.rec_manual_notes}")
        st.download_button("⬇️ .md", data="\n".join(lines),
                           file_name="recorded_call_script.md", mime="text/markdown",
                           use_container_width=True)

    # Opening
    if data.get("opening"):
        with st.expander("📞 Opening", expanded=False):
            st.info(data["opening"])

    # Progress
    answered = sum(1 for q in questions if q.get("status", "open") != "open")
    if questions:
        st.progress(answered / len(questions), text=f"{answered}/{len(questions)} criteria resolved")

    # Cards
    last_section = None
    for q in questions:
        qid     = q.get("id", "")
        section = q.get("section", "general")
        status  = q.get("status", "open")
        badge   = _answer_badge(q)
        icon, _ = SECTION_LABEL.get(section, ("📋", section.title()))

        if section != last_section:
            _, label = SECTION_LABEL.get(section, ("📋", section.title()))
            st.markdown(f"### {icon} {label} Criteria")
            last_section = section

        bad_status = (status == "confirmed_met" and section == "exclusion") or \
                     (status == "confirmed_failed" and section != "exclusion")
        expanded = (status != "confirmed_met" or section == "exclusion") and status != "confirmed_failed"

        with st.expander(f"{badge}  {q.get('criterion','?')}", expanded=expanded):
            st.markdown("**💬 Ninna says:**")
            st.info(f'*"{q.get("ninna_says","")}"*')

            c1, c2 = st.columns(2)
            c1.caption(f"✔️ PASS if: {q.get('pass_condition','?')}")
            c2.caption(f"❌ FAIL if: {q.get('fail_condition','?')}")
            if q.get("washout_days"):
                st.caption(f"⏱️ Washout required: **{q['washout_days']} days**")

            st.divider()

            auto_ans = q.get("answer")
            auto_src = q.get("source", "none")
            if auto_ans and auto_src == "auto":
                st.success(f"🤖 **From transcript:** {auto_ans}")
            elif auto_ans and auto_src == "manual":
                st.info(f"✏️ **From notes:** {auto_ans}")

            cur = st.session_state.rec_manual_overrides.get(qid, "")
            new_val = st.text_input("✏️ Manual answer / override", value=cur,
                                    key=f"rec_ov_{qid}",
                                    placeholder="Type patient's answer if missed…")
            if new_val != cur:
                st.session_state.rec_manual_overrides[qid] = new_val

            if status == "confirmed_met" and section != "exclusion":
                st.success("✅ PASS")
            elif status == "confirmed_met" and section == "exclusion":
                st.error("❌ Exclusion TRIGGERED")
            elif status == "confirmed_failed" and section == "exclusion":
                st.success("✅ Clear")
            elif status == "confirmed_failed":
                st.error("❌ FAIL")
            elif status == "needs_clarification":
                st.warning("⚠️ Needs clarification")
            else:
                st.info("⚪ Not captured in transcript")

    # Global notes
    st.divider()
    st.markdown("### 📝 Additional Notes")
    new_notes = st.text_area("Free-text notes (feed into I/E context)",
                              value=st.session_state.rec_manual_notes, height=80,
                              key="rec_global_notes",
                              placeholder="Any additional context not in the call…")
    if new_notes != st.session_state.rec_manual_notes:
        st.session_state.rec_manual_notes = new_notes

    # Closings
    c1, c2 = st.columns(2)
    with c1:
        with st.expander("✅ If Eligible"):
            st.success(data.get("closing_eligible", ""))
    with c2:
        with st.expander("❌ If Not Eligible"):
            st.error(data.get("closing_ineligible", ""))

# ── Main render ────────────────────────────────────────────────────────────────

def render(api_key: str, protocol_text: str, whisper_model=None):
    """Entry point called from app.py for Recorded Call mode."""
    _init()

    st.title("📼 Recorded Call — I/E Analysis")
    st.caption("Upload a recorded call audio or a text transcript. The app transcribes, fills the I/E checklist, and completes the script cards — all in one shot.")

    if not api_key:
        st.error("⚠️ Enter your Gemini API key in the sidebar.")
        return
    if not protocol_text:
        st.warning("⚠️ No protocol uploaded — I/E check will use general knowledge.")

    # ── Upload + Process bar ─────────────────────────────────────────────────
    up_col, reset_col = st.columns([5, 1])
    with reset_col:
        if st.button("🔄 Reset"):
            _reset()
            st.rerun()

    with up_col:
        uploaded = st.file_uploader(
            "Upload recorded call (.wav, .mp3) or transcript (.txt)",
            type=["wav", "mp3", "txt"],
            key="rec_upload"
        )

    if uploaded and not st.session_state.rec_processed:
        file_ext = uploaded.name.split(".")[-1].lower()

        if file_ext == "txt":
            # Plain text transcript
            transcript = uploaded.read().decode("utf-8", errors="ignore").strip()
            st.session_state.rec_transcript = transcript
            step_transcribe = False
        else:
            # Audio file — transcribe with Whisper
            step_transcribe = True

        process_btn = st.button("▶ Analyse Call", type="primary", use_container_width=True)

        if process_btn:
            svc = LiveSessionService(api_key)

            # Step 1: Transcribe if audio
            if step_transcribe:
                with st.spinner(f"🎧 Transcribing {uploaded.name} with Whisper…"):
                    audio_bytes = uploaded.read()
                    transcript  = LiveSessionService.transcribe_chunk(audio_bytes, whisper_model)
                    if transcript.startswith("["):
                        st.error(f"Transcription failed: {transcript}")
                        st.stop()
                    st.session_state.rec_transcript = transcript
                st.success(f"✅ Transcribed — {len(transcript)} characters")

            # Step 2: Generate script (if not already done)
            if not st.session_state.rec_script_data:
                with st.spinner("✨ Generating script from protocol…"):
                    st.session_state.rec_script_data = svc.generate_script_structured(
                        protocol_text or ""
                    )

            # Step 3: Fill script answers from transcript
            questions = (st.session_state.rec_script_data or {}).get("questions", [])
            if questions:
                with st.spinner("📝 Filling script answers from transcript…"):
                    updated = svc.extract_script_answers(
                        questions, st.session_state.rec_transcript, ""
                    )
                    st.session_state.rec_script_data["questions"] = updated

            # Step 4: I/E check
            with st.spinner("🤖 Running I/E analysis…"):
                st.session_state.rec_ie_status = svc.run_ie_check(
                    st.session_state.rec_transcript, protocol_text or ""
                )

            st.session_state.rec_processed = True
            st.rerun()

    elif uploaded and st.session_state.rec_processed:
        st.success(f"✅ Already processed: **{uploaded.name}** ({len(st.session_state.rec_transcript):,} chars)")

    # ── Results ───────────────────────────────────────────────────────────────
    if st.session_state.rec_processed:
        st.divider()

        # Show raw transcript in collapsible
        with st.expander("📄 Full Transcript", expanded=False):
            st.text_area("transcript", value=st.session_state.rec_transcript,
                         height=250, label_visibility="hidden", disabled=True)

        st.divider()

        # Two-column results
        left, right = st.columns([6, 4])

        with left:
            st.subheader("📋 Script Cards — Filled")
            _render_script_cards(api_key, protocol_text)

        with right:
            st.subheader("✅ I/E Checklist")
            _render_ie(st.session_state.rec_ie_status)
