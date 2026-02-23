"""
Lightweight Gemini prompt for real-time I/E checking during a live pre-screen call.

Unlike the full extraction prompt (which extracts vitals, ECG, labs, etc.),
this prompt does ONE thing ONLY: evaluate inclusion/exclusion criteria status
based on the transcript so far.

This is fast and cheap — designed to be called every ~90 seconds during a call.
"""

LIVE_IE_PROMPT_TEMPLATE = """You are a clinical trial eligibility assistant monitoring a live pre-screen phone call.

=====================
PROTOCOL — INCLUSION / EXCLUSION CRITERIA:
=====================
{protocol_context}

=====================
TRANSCRIPT SO FAR (call is still in progress):
=====================
{transcript_so_far}

=====================
YOUR TASK:
=====================

Read the transcript so far and determine the current eligibility status for EACH criterion mentioned in the protocol above.

For each criterion, classify it as:
- "confirmed_met"    → Patient clearly meets this criterion based on what has been said
- "confirmed_failed" → Patient clearly FAILS this criterion based on what has been said
- "open"             → Not yet discussed, or discussed but unclear — still needs to be confirmed
- "needs_clarification" → Something was said that partially addresses this, but needs follow-up

Return ONLY this JSON structure:

{{
  "inclusion_criteria": [
    {{
      "criterion": "Short description of the criterion",
      "status": "confirmed_met | confirmed_failed | open | needs_clarification",
      "evidence": "What in the transcript supports this classification, or null if open",
      "action_needed": "What Ninna should ask/confirm next, or null if already resolved"
    }}
  ],
  "exclusion_criteria": [
    {{
      "criterion": "Short description of the criterion",
      "status": "confirmed_met | confirmed_failed | open | needs_clarification",
      "evidence": "What in the transcript supports this classification, or null if open",
      "action_needed": "What Ninna should ask/confirm next, or null if already resolved"
    }}
  ],
  "washout_flags": [
    {{
      "medication": "Medication name",
      "last_dose_date": "Date mentioned or null",
      "washout_days_required": "Number or null if not in protocol",
      "status": "compliant | non_compliant | unclear",
      "note": "Brief explanation"
    }}
  ],
  "summary": {{
    "overall_status": "likely_eligible | likely_ineligible | too_early_to_tell",
    "open_count": "integer — number of criteria still unresolved",
    "failed_count": "integer — number of criteria confirmed failed",
    "key_concerns": ["list of the most important issues Ninna needs to address on this call"]
  }}
}}

CRITICAL RULES:
1. Only classify a criterion as "confirmed_met" if the transcript contains CLEAR evidence.
2. If the criterion was not discussed at all, mark it "open" — do NOT assume.
3. Be concise in evidence and action_needed — Ninna will read this live during a call.
4. For washout: if a prohibited medication is mentioned with a date, always flag it and calculate compliance.
5. Return ONLY valid JSON. No markdown fences.
"""
