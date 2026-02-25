"""
live_session.py — Live Pre-Screen Call Session UI (Bidirectional)

Tabs:
  📋 Call Script   — Interactive question cards. Transcript auto-fills answers.
                     Ninna can also type answers manually → feeds I/E check.
  🎙️ Live Session  — Recording + growing transcript + live I/E checklist.
"""

import streamlit as st
from ai_services import LiveSessionService

# ── Status constants ───────────────────────────────────────────────────────────

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
    "too_early_to_tell": ("⏳ Still gathering information…", "info"),
}

# ── Session state ──────────────────────────────────────────────────────────────

def _init_session():
    defaults = {
        # Live session
        "live_transcript":    "",
        "ie_status":          None,
        "chunk_count":        0,
        "last_ie_chunk":      -1,
        # Script state (shared between live + recorded)
        "script_data":        None,
        "script_generated":   False,
        "manual_overrides":   {},
        "manual_notes":       "",
        "last_extract_chunk": -1,
        # Recorded-call session
        "rec_transcript":     "",
        "rec_ie_status":      None,
        "rec_manual_overrides": {},
        "rec_manual_notes":   "",
        "rec_processed":      False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── Helpers ────────────────────────────────────────────────────────────────────

def _build_manual_context() -> str:
    """Collect all manual overrides + notes into a single string for Gemini."""
    parts = []
    data = st.session_state.script_data or {}
    questions = data.get("questions", [])
    for q in questions:
        qid = q.get("id", "")
        override = st.session_state.manual_overrides.get(qid, "").strip()
        if override:
            criterion = q.get("criterion", qid)
            parts.append(f"- {criterion}: {override}")
    if st.session_state.manual_notes.strip():
        parts.append(f"Additional notes: {st.session_state.manual_notes}")
    return "\n".join(parts)


def _answer_badge(q: dict) -> str:
    status = q.get("status", "open")
    section = q.get("section", "general")
    neg = section in ("exclusion", "washout")  # inverted: confirmed_met = triggered (bad)
    if neg:
        if status == "confirmed_met":    return "❌ TRIGGERED"
        if status == "confirmed_failed": return "✅ Clear"
    else:
        if status == "confirmed_met":    return "✅ PASS"
        if status == "confirmed_failed": return "❌ FAIL"
    if status == "needs_clarification": return "⚠️ Clarify"
    return "⚪ Open"


def _status_color(q: dict) -> str:
    status  = q.get("status", "open")
    section = q.get("section", "general")
    neg = section in ("exclusion", "washout")
    if status == "confirmed_met":
        return "error" if neg else "success"
    if status == "confirmed_failed":
        return "success" if neg else "error"
    if status == "needs_clarification":
        return "warning"
    return "info"

# ── Script Tab ─────────────────────────────────────────────────────────────────

def _render_script_tab(api_key: str, protocol_text: str):
    """Interactive script cards — bidirectional fill."""
    st.subheader("📋 Pre-Screen Call Script")

    has_protocol = bool(protocol_text and protocol_text.strip())
    has_api_key  = bool(api_key and api_key.strip())

    if not has_protocol:
        st.warning("⚠️ Upload the protocol in the sidebar for a protocol-specific script.")
    if not has_api_key:
        st.error("⚠️ Gemini API key required.")
        return

    # Controls row
    col_gen, col_extract, col_dl = st.columns([2, 2, 1])
    with col_gen:
        if st.button(
            "🔄 Regenerate Script" if st.session_state.script_generated else "✨ Generate Call Script",
            use_container_width=True, type="primary"
        ):
            with st.spinner("✨ Generating structured script from protocol…"):
                svc = LiveSessionService(api_key)
                st.session_state.script_data = svc.generate_script_structured(
                    protocol_text if has_protocol else ""
                )
                st.session_state.script_generated = True
                st.session_state.manual_overrides = {}
            st.rerun()

    with col_extract:
        transcript = st.session_state.live_transcript
        questions  = (st.session_state.script_data or {}).get("questions", [])
        manual_ctx = _build_manual_context()
        can_extract = bool(transcript.strip() or manual_ctx.strip()) and bool(questions)
        if st.button(
            "🔁 Fill from Transcript + Notes",
            use_container_width=True,
            disabled=not can_extract,
            help="Let Gemini auto-fill answers based on the recorded transcript and your manual notes"
        ):
            with st.spinner("🤖 Extracting answers from transcript…"):
                svc = LiveSessionService(api_key)
                updated_q = svc.extract_script_answers(
                    questions, transcript, manual_ctx
                )
                st.session_state.script_data["questions"] = updated_q
                st.session_state.last_extract_chunk = st.session_state.chunk_count
            st.rerun()

    with col_dl:
        # Build downloadable markdown from current state
        data = st.session_state.script_data or {}
        if data:
            lines = [f"# Pre-Screen Call Script\n\n## Opening\n{data.get('opening','')}\n"]
            last_section = None
            for q in data.get("questions", []):
                sec = q.get("section", "general")
                if sec != last_section:
                    icon, label = SECTION_LABEL.get(sec, ("📋", sec.title()))
                    lines.append(f"\n## {icon} {label} Criteria\n")
                    last_section = sec
                lines.append(f"**{q.get('criterion','?')}**")
                lines.append(f"*Ninna says:* \"{q.get('ninna_says','')}\"")
                lines.append(f"✔ PASS if: {q.get('pass_condition','')}")
                if q.get("washout_days"):
                    lines.append(f"⏱️ Washout: {q['washout_days']} days")
                answer = (
                    st.session_state.manual_overrides.get(q.get("id",""), "").strip()
                    or q.get("answer") or "________________"
                )
                lines.append(f"📝 Answer: {answer}  [{_answer_badge(q)}]\n")
            lines += [
                f"\n## ✅ Closing (if Eligible)\n{data.get('closing_eligible','')}",
                f"\n## ❌ Closing (if Ineligible)\n{data.get('closing_ineligible','')}",
            ]
            if st.session_state.manual_notes:
                lines.append(f"\n## 📝 Notes\n{st.session_state.manual_notes}")
            md_text = "\n".join(lines)
            st.download_button("⬇️ .md", data=md_text,
                               file_name="prescreening_script.md",
                               mime="text/markdown",
                               use_container_width=True)

    if not st.session_state.script_generated:
        st.info(
            "👆 Click **Generate Call Script** to get started.\n\n"
            "Each I/E criterion becomes an interactive card:\n"
            "- 🤖 Auto-filled from the live transcript\n"
            "- ✏️ Manually editable if something was missed\n"
            "- ✅ / ❌ status shown for each question"
        )
        return

    data = st.session_state.script_data or {}
    if not data:
        st.error("Script generation failed — check your API key and protocol upload.")
        return

    # ── Opening ───────────────────────────────────────────────────────────────
    with st.expander("📞 Opening (read aloud)", expanded=True):
        st.info(data.get("opening", ""))

    # ── Question Cards ─────────────────────────────────────────────────────────
    questions    = data.get("questions", [])
    last_section = None

    # Progress bar
    answered = sum(1 for q in questions if q.get("status", "open") != "open")
    if questions:
        st.progress(answered / len(questions),
                    text=f"{answered}/{len(questions)} criteria resolved")

    for q in questions:
        qid     = q.get("id", "")
        section = q.get("section", "general")
        icon, _ = SECTION_LABEL.get(section, ("📋", section.title()))
        status  = q.get("status", "open")
        badge   = _answer_badge(q)

        # Section header
        if section != last_section:
            _, label = SECTION_LABEL.get(section, ("📋", section.title()))
            st.markdown(f"### {icon} {label} Criteria")
            last_section = section

        # Color border via container + caption
        color = _status_color(q)
        expanded = status in ("open", "needs_clarification", "confirmed_failed") or (
            section == "exclusion" and status == "confirmed_met"
        )

        with st.expander(f"{badge}  {q.get('criterion', '?')}", expanded=expanded):

            # Ninna's script line
            st.markdown(f"**💬 Ninna says:**")
            st.info(f'*"{q.get("ninna_says", "")}"*')

            # Pass/Fail guide
            cond_col1, cond_col2 = st.columns(2)
            with cond_col1:
                st.caption(f"✔️ **PASS if:** {q.get('pass_condition','?')}")
            with cond_col2:
                st.caption(f"❌ **FAIL if:** {q.get('fail_condition','?')}")
            if q.get("washout_days"):
                st.caption(f"⏱️ Required washout: **{q['washout_days']} days**")

            st.divider()

            # Auto-filled answer (from transcript)
            auto_answer = q.get("answer")
            auto_source = q.get("source", "none")
            if auto_answer and auto_source == "auto":
                st.success(f"🤖 **Auto-filled from transcript:** {auto_answer}")
            elif auto_answer and auto_source == "manual":
                st.info(f"✏️ **From manual notes:** {auto_answer}")

            # Manual override input (always shown)
            current_override = st.session_state.manual_overrides.get(qid, "")
            new_val = st.text_input(
                "✏️ Manual answer / override",
                value=current_override,
                key=f"override_{qid}",
                placeholder="Type patient's answer here if not captured by transcript…",
                label_visibility="visible"
            )
            if new_val != current_override:
                st.session_state.manual_overrides[qid] = new_val

            # Status indicator
            # For exclusion + washout: confirmed_met = BAD (triggered), confirmed_failed = GOOD (clear)
            # For inclusion: confirmed_met = GOOD (pass), confirmed_failed = BAD (fail)
            neg = section in ("exclusion", "washout")
            if status == "confirmed_met" and not neg:
                st.success("✅ PASS — criterion confirmed")
            elif status == "confirmed_met" and neg:
                st.error("❌ Exclusion / Washout TRIGGERED")
            elif status == "confirmed_failed" and neg:
                st.success("✅ Clear — not triggered")
            elif status == "confirmed_failed":
                st.error("❌ FAIL — patient does not meet this criterion")
            elif status == "needs_clarification":
                st.warning("⚠️ Needs clarification — follow up required")
            else:
                st.info("⚪ Not yet captured — record more or type above")

    # ── Free-text notes ────────────────────────────────────────────────────────
    st.divider()
    st.markdown("### 📝 Additional Notes")
    new_notes = st.text_area(
        "Free-text notes (included in I/E context)",
        value=st.session_state.manual_notes,
        height=80,
        placeholder="Anything Ninna wants to note that wasn't captured above…",
        key="global_manual_notes"
    )
    if new_notes != st.session_state.manual_notes:
        st.session_state.manual_notes = new_notes

    # ── Closings ──────────────────────────────────────────────────────────────
    st.divider()
    cl1, cl2 = st.columns(2)
    with cl1:
        with st.expander("✅ Closing — If Eligible"):
            st.success(data.get("closing_eligible", ""))
    with cl2:
        with st.expander("❌ Closing — If Not Eligible"):
            st.error(data.get("closing_ineligible", ""))


# ── I/E Panel ──────────────────────────────────────────────────────────────────

def _render_ie_panel(ie_status: dict):
    if not ie_status:
        st.info("⏳ I/E status will update after your first recording chunk or a manual fill.")
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
        st.markdown("### 🟢 Inclusion")
        for item in inclusion:
            status = item.get("status", "open")
            emoji  = STATUS_EMOJI.get(status, "⚪")
            with st.expander(f"{emoji} {item.get('criterion','?')}",
                             expanded=(status in ("confirmed_failed", "needs_clarification", "open"))):
                if item.get("evidence"):
                    st.caption(f"📋 {item['evidence']}")
                if item.get("action_needed"):
                    st.info(f"💬 *{item['action_needed']}*")
                labels = {"confirmed_met": st.success, "confirmed_failed": st.error,
                          "needs_clarification": st.warning}
                labels.get(status, st.info)(f"{emoji} {status.replace('_',' ').title()}")

    st.divider()

    # Exclusion
    exclusion = ie_status.get("exclusion_criteria", [])
    if exclusion:
        st.markdown("### 🔴 Exclusion")
        for item in exclusion:
            status = item.get("status", "open")
            emoji  = "❌" if status == "confirmed_met" else ("✅" if status == "confirmed_failed" else STATUS_EMOJI.get(status, "⚪"))
            with st.expander(f"{emoji} {item.get('criterion','?')}",
                             expanded=(status in ("confirmed_met", "needs_clarification"))):
                if item.get("evidence"):
                    st.caption(f"📋 {item['evidence']}")
                if item.get("action_needed"):
                    st.info(f"💬 *{item['action_needed']}*")
                if status == "confirmed_met":
                    st.error("⚠️ Exclusion TRIGGERED")
                elif status == "confirmed_failed":
                    st.success("✅ Clear")
                elif status == "needs_clarification":
                    st.warning("⚠️ Needs clarification")
                else:
                    st.info("⚪ Not yet discussed")

    # Washout
    washout = ie_status.get("washout_flags", [])
    if washout:
        st.divider()
        st.markdown("### 💊 Washout")
        for w in washout:
            wstatus = w.get("status", "unclear")
            emoji   = STATUS_EMOJI.get(wstatus, "⚠️")
            with st.expander(f"{emoji} {w.get('medication','?')}",
                             expanded=(wstatus == "non_compliant")):
                if w.get("washout_days_required"):
                    st.caption(f"⏱️ Required: {w['washout_days_required']} days")
                if w.get("last_dose_date"):
                    st.caption(f"📅 Last dose: {w['last_dose_date']}")
                note = w.get("note", "")
                if note:
                    {"non_compliant": st.error, "compliant": st.success}.get(wstatus, st.warning)(note)


# ── Recorded Call Tab ────────────────────────────────────────────────────────

def _render_recorded_tab(api_key: str, protocol_text: str, whisper_model=None):
    """One-shot analysis: upload .wav/.mp3 or .txt, get filled script + I/E."""
    st.subheader("📼 Recorded Call Analysis")
    st.caption(
        "Upload a recorded call (`.wav` / `.mp3`) or a plain-text transcript (`.txt`). "
        "The app transcribes, fills every script card, and runs the I/E check — all in one shot."
    )

    if not api_key:
        st.error("⚠️ Gemini API key required.")
        return

    uploaded = st.file_uploader(
        "Upload recorded call or transcript",
        type=["wav", "mp3", "txt"],
        key="rec_upload"
    )

    # Reset recorded state when a new file is picked
    if uploaded is None:
        for k in ["rec_transcript", "rec_ie_status", "rec_manual_overrides",
                  "rec_manual_notes", "rec_processed"]:
            st.session_state[k] = (
                "" if k in ("rec_transcript", "rec_manual_notes") else
                {} if k == "rec_manual_overrides" else
                None if k == "rec_ie_status" else False
            )
        st.info(
            "👆 Upload a file to begin.\n\n"
            "- **.wav / .mp3** — transcribed locally with Whisper\n"
            "- **.txt** — plain transcript pasted or exported from any transcription tool"
        )
        return

    file_ext = uploaded.name.split(".")[-1].lower()
    is_audio  = file_ext in ("wav", "mp3")

    if not st.session_state.rec_processed:
        if st.button("▶ Analyse Call", type="primary", use_container_width=True):
            svc = LiveSessionService(api_key)

            # Step 1 — Transcribe / read
            if is_audio:
                with st.spinner(f"🎧 Transcribing {uploaded.name} with Whisper…"):
                    transcript = LiveSessionService.transcribe_chunk(uploaded.read(), whisper_model)
                if transcript.startswith("["):
                    st.error(f"Transcription failed: {transcript}")
                    st.stop()
                st.session_state.rec_transcript = transcript
            else:
                st.session_state.rec_transcript = uploaded.read().decode("utf-8", errors="ignore").strip()

            # Step 2 — Generate script if needed (or if previous attempt failed)
            has_questions = bool((st.session_state.script_data or {}).get("questions"))
            if not has_questions:
                with st.spinner("✨ Generating script from protocol…"):
                    st.session_state.script_data = svc.generate_script_structured(protocol_text or "")
                    st.session_state.script_generated = True
                    st.session_state.manual_overrides = {}

            # Step 3 — I/E check (primary source of truth)
            # Pass the script questions so Gemini evaluates EXACTLY those criteria.
            _q_for_ie = (st.session_state.script_data or {}).get("questions", []) or []
            with st.spinner("🤖 Running I/E analysis…"):
                ie = svc.run_ie_check(
                    st.session_state.rec_transcript, protocol_text or "",
                    questions=_q_for_ie or None
                )
                st.session_state.rec_ie_status = ie

            # Step 4 — Fill script cards via BOTH methods (belt + suspenders)
            data = dict(st.session_state.script_data or {})
            questions = data.get("questions", [])
            if questions:
                with st.spinner("📝 Filling script cards…"):
                    # Method A: sync from I/E results (fast, no extra API call)
                    synced = LiveSessionService.sync_ie_to_script(questions, ie)
                    # Method B: extract directly from transcript (catches anything sync missed)
                    filled = svc.extract_script_answers(
                        synced, st.session_state.rec_transcript, ""
                    )
                    data["questions"] = filled
                    st.session_state.script_data = data  # full reassignment, Streamlit detects it

            st.session_state.rec_processed = True
            st.rerun()
    else:
        st.success(f"✅ Processed: **{uploaded.name}** ({len(st.session_state.rec_transcript):,} chars)")
        if st.button("🔄 Re-analyse", help="Run analysis again on the same file"):
            st.session_state.rec_processed = False
            st.rerun()

    if not st.session_state.rec_processed:
        return

    # ── Results ───────────────────────────────────────────────────────────────
    with st.expander("📄 Full Transcript", expanded=False):
        st.text_area("transcript", value=st.session_state.rec_transcript,
                     height=200, label_visibility="hidden", disabled=True)

    st.divider()
    left, right = st.columns([6, 4])

    # LEFT — filled script cards (reuses the same shared script_data)
    with left:
        st.subheader("📋 Script Cards — Filled")

        col_fill, col_dl = st.columns([3, 1])
        with col_fill:
            svc = LiveSessionService(api_key)
            questions = (st.session_state.script_data or {}).get("questions", [])
            manual_ctx = _build_manual_context()
            if st.button("🔁 Re-fill Answers", use_container_width=True,
                         disabled=not (st.session_state.rec_transcript or manual_ctx)):
                with st.spinner("📝 Re-extracting…"):
                    updated = svc.extract_script_answers(
                        questions, st.session_state.rec_transcript, manual_ctx
                    )
                    st.session_state.script_data["questions"] = updated
                st.rerun()
        with col_dl:
            data = st.session_state.script_data or {}
            if data:
                lines = [f"# Pre-Screen Script\n\n## Opening\n{data.get('opening','')}\n"]
                last_sec = None
                for q in data.get("questions", []):
                    sec = q.get("section", "general")
                    if sec != last_sec:
                        icon, lbl = SECTION_LABEL.get(sec, ("📋", sec.title()))
                        lines.append(f"\n## {icon} {lbl}\n")
                        last_sec = sec
                    ans = (st.session_state.rec_manual_overrides.get(q.get("id",""), "").strip()
                           or q.get("answer") or "________________")
                    badge = _answer_badge(q)
                    lines += [f"**{q.get('criterion','?')}**",
                              f"*Ninna says:* \"{q.get('ninna_says','')}\"  ",
                              f"📝 Answer: {ans}  [{badge}]\n"]
                st.download_button("⬇️ .md", data="\n".join(lines),
                                   file_name="recorded_script.md", mime="text/markdown",
                                   use_container_width=True)

        # Progress
        questions = (st.session_state.script_data or {}).get("questions", [])
        answered  = sum(1 for q in questions if q.get("status", "open") != "open")
        if questions:
            st.progress(answered / len(questions), text=f"{answered}/{len(questions)} criteria resolved")

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

            expanded = not (status == "confirmed_met" and section != "exclusion")
            with st.expander(f"{badge}  {q.get('criterion','?')}", expanded=expanded):
                st.markdown("**💬 Ninna says:**")
                st.info(f'*"{q.get("ninna_says","")}"*')
                c1, c2 = st.columns(2)
                c1.caption(f"✔️ PASS if: {q.get('pass_condition','?')}")
                c2.caption(f"❌ FAIL if: {q.get('fail_condition','?')}")
                if q.get("washout_days"):
                    st.caption(f"⏱️ Washout: **{q['washout_days']} days**")
                st.divider()
                auto_ans = q.get("answer")
                auto_src = q.get("source", "none")
                if auto_ans and auto_src == "auto":
                    st.success(f"🤖 **From recording:** {auto_ans}")
                elif auto_ans and auto_src == "manual":
                    st.info(f"✏️ **From notes:** {auto_ans}")
                cur = st.session_state.rec_manual_overrides.get(qid, "")
                nv  = st.text_input("✏️ Manual override", value=cur,
                                    key=f"rec_ov_{qid}",
                                    placeholder="Type answer if missed in recording…")
                if nv != cur:
                    st.session_state.rec_manual_overrides[qid] = nv
                neg = section in ("exclusion", "washout")
                if status == "confirmed_met" and not neg:
                    st.success("✅ PASS")
                elif status == "confirmed_met" and neg:
                    st.error("❌ Exclusion / Washout TRIGGERED")
                elif status == "confirmed_failed" and neg:
                    st.success("✅ Clear")
                elif status == "confirmed_failed":
                    st.error("❌ FAIL")
                elif status == "needs_clarification":
                    st.warning("⚠️ Needs clarification")
                else:
                    st.info("⚪ Not captured")

        st.divider()
        st.markdown("### 📝 Additional Notes")
        nn = st.text_area("Notes (feed into I/E context on re-analyse)",
                          value=st.session_state.rec_manual_notes, height=70,
                          key="rec_notes_box",
                          placeholder="Any extra context not in the recording…")
        if nn != st.session_state.rec_manual_notes:
            st.session_state.rec_manual_notes = nn

    # RIGHT — I/E checklist
    with right:
        st.subheader("✅ I/E Checklist")
        _render_ie_panel(st.session_state.rec_ie_status)


# ── Main render ────────────────────────────────────────────────────────────────

def render(api_key: str, protocol_text: str, whisper_model=None):
    """Entry point called from app.py for Live Pre-Screen mode."""
    _init_session()

    st.title("🎙️ Live Pre-Screen Call Session")

    if not api_key:
        st.error("⚠️ Please enter your Gemini API key in the sidebar.")
        return
    if not protocol_text:
        st.warning("⚠️ No protocol uploaded — Gemini will use general knowledge.")

    # Top status bar
    top_c1, top_c2 = st.columns([5, 1])
    with top_c1:
        st.caption(
            f"Chunks: **{st.session_state.chunk_count}** | "
            f"Protocol: {'✅' if protocol_text else '⚠️ not loaded'} | "
            f"Script: {'✅ generated' if st.session_state.script_generated else '⚠️ not generated'}"
        )
    with top_c2:
        if st.button("🔄 Reset", help="Clear everything"):
            for k in ["live_transcript", "ie_status", "chunk_count", "last_ie_chunk",
                      "script_data", "script_generated", "manual_overrides",
                      "manual_notes", "last_extract_chunk"]:
                st.session_state[k] = (
                    "" if k in ("live_transcript", "manual_notes") else
                    None if k in ("ie_status", "script_data") else
                    {} if k == "manual_overrides" else
                    False if k == "script_generated" else
                    -1 if k in ("last_ie_chunk", "last_extract_chunk") else 0
                )
            st.rerun()

    st.divider()

    # Tabs
    tab_script, tab_live, tab_rec = st.tabs(["📋 Call Script", "🎙️ Live Session", "📼 Recorded Call"])

    # ── Tab 1: Interactive Script ─────────────────────────────────────────────
    with tab_script:
        _render_script_tab(api_key, protocol_text)

    # ── Tab 2: Live Recording + I/E ───────────────────────────────────────────
    with tab_live:
        left_col, right_col = st.columns([6, 4])

        with left_col:
            st.subheader("📝 Live Transcript")

            audio_data = st.audio_input(
                "🎙️ Record a chunk (15–30s), then stop",
                key=f"audio_chunk_{st.session_state.chunk_count}"
            )

            if audio_data is not None:
                with st.spinner("🎧 Transcribing with Whisper…"):
                    chunk_text = LiveSessionService.transcribe_chunk(
                        audio_data.read(), whisper_model
                    )

                if chunk_text and not chunk_text.startswith("["):
                    st.session_state.live_transcript += (
                        (" " if st.session_state.live_transcript else "") + chunk_text
                    )
                    st.session_state.chunk_count += 1

                    # Auto I/E check every 3 chunks — includes manual context
                    if (st.session_state.chunk_count > st.session_state.last_ie_chunk and
                            st.session_state.chunk_count % LiveSessionService.IE_CHECK_EVERY_N_CHUNKS == 0):
                        manual_ctx = _build_manual_context()
                        combined   = st.session_state.live_transcript
                        if manual_ctx:
                            combined += f"\n\n[MANUAL NOTES]: {manual_ctx}"
                        with st.spinner("🤖 Updating I/E checklist…"):
                            svc = LiveSessionService(api_key)
                            _qs = data.get("questions", [])
                            ie = svc.run_ie_check(combined, protocol_text,
                                                  questions=_qs or None)
                            st.session_state.ie_status = ie
                            # Sync I/E results → script cards
                            data = dict(st.session_state.script_data or {})
                            questions = data.get("questions", [])
                            if questions:
                                synced = LiveSessionService.sync_ie_to_script(questions, ie)
                                data["questions"] = synced
                                st.session_state.script_data = data
                            st.session_state.last_ie_chunk = st.session_state.chunk_count
                            st.session_state.last_extract_chunk = st.session_state.chunk_count

                    st.success(f"✅ Chunk {st.session_state.chunk_count} transcribed")
                    st.rerun()
                else:
                    st.warning(f"⚠️ {chunk_text}")

            # Manual trigger buttons
            if st.session_state.live_transcript:
                btn1, btn2 = st.columns(2)
                with btn1:
                    if st.button("🔁 Run I/E Check Now"):
                        manual_ctx = _build_manual_context()
                        combined   = st.session_state.live_transcript
                        if manual_ctx:
                            combined += f"\n\n[MANUAL NOTES]: {manual_ctx}"
                        with st.spinner("🤖 Running I/E check…"):
                            svc = LiveSessionService(api_key)
                            data = dict(st.session_state.script_data or {})
                            _qs = data.get("questions", [])
                            ie  = svc.run_ie_check(combined, protocol_text,
                                                   questions=_qs or None)
                            st.session_state.ie_status = ie
                            if _qs:
                                synced = LiveSessionService.sync_ie_to_script(_qs, ie)
                                data["questions"] = synced
                                st.session_state.script_data = data
                            st.session_state.last_ie_chunk = st.session_state.chunk_count
                        st.rerun()
                with btn2:
                    questions = (st.session_state.script_data or {}).get("questions", [])
                    if st.button("📝 Fill Script Now", disabled=not questions):
                        manual_ctx = _build_manual_context()
                        with st.spinner("📝 Filling script answers…"):
                            svc = LiveSessionService(api_key)
                            up = svc.extract_script_answers(
                                questions, st.session_state.live_transcript, manual_ctx
                            )
                            st.session_state.script_data["questions"] = up
                            st.session_state.last_extract_chunk = st.session_state.chunk_count
                        st.rerun()

            transcript = st.session_state.live_transcript
            if transcript:
                st.markdown("---")
                st.text_area("transcript", value=transcript, height=360,
                             label_visibility="hidden", disabled=True)
                ie_chunk  = st.session_state.last_ie_chunk
                if ie_chunk >= 0:
                    nxt = ((ie_chunk // LiveSessionService.IE_CHECK_EVERY_N_CHUNKS) + 1) * LiveSessionService.IE_CHECK_EVERY_N_CHUNKS
                    rem = nxt - st.session_state.chunk_count
                    if rem > 0:
                        st.caption(f"⏱️ Auto I/E check in **{rem}** more chunk(s)")
            else:
                st.info("Record your first chunk above to begin.")

        with right_col:
            st.subheader("✅ I/E Checklist (Live)")
            _render_ie_panel(st.session_state.ie_status)

    # ── Tab 3: Recorded Call ──────────────────────────────────────────────────
    with tab_rec:
        _render_recorded_tab(api_key, protocol_text, whisper_model)
