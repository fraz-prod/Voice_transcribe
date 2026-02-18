# 🏥 Voice-Enabled Eligibility Screening Assistant
## Gemini Mode — Architecture & Pipeline Overview

---

## 📌 The One-Line Summary

> **A nurse uploads a patient visit recording → the system transcribes it, extracts all medical data using Google Gemini AI, checks trial eligibility, and auto-fills the official visit form — in under a minute.**

---

## 🎬 How It Works: The Full Story

Imagine a nurse just finished a 15-minute screening call with a patient for the **STAR-0215-301 clinical trial** (a study for Hereditary Angioedema). During that call, the nurse asked about the patient's age, medications, vital signs, lab results, and more. Normally, the nurse would now spend **30+ minutes** manually writing all of that into a Word form.

**This app does it automatically.** Here's exactly what happens, step by step:

---

### Step 1️⃣ — The Nurse Opens the App

The nurse opens the **Streamlit web app** in their browser and selects **"Gemini Mode"** from the sidebar. They enter their Gemini API key (pre-loaded from environment settings).

---

### Step 2️⃣ — Uploading Files

The nurse uploads **two things**:

| What they upload | Why |
|---|---|
| **Audio recording** of the patient call (WAV or MP3) — *OR* a **.txt** transcript if already typed out | This is the raw visit conversation |
| **Protocol document** (optional, PDF or Markdown) | This is the official study protocol — the system uses it to know *exactly* what data must be collected for this visit type |

---

### Step 3️⃣ — Audio Transcription (Local, Private)

If the nurse uploaded an **audio file**, the system transcribes it using **Faster-Whisper** — an AI speech-to-text model that runs **entirely on the local machine**. No audio is ever sent to the cloud.

- Model size: **medium** (good accuracy vs speed tradeoff)
- The transcript appears **live** on screen as it processes
- If the nurse uploaded a **.txt** file instead, this step is skipped

**Output:** A full text transcript of the nurse-patient conversation.

---

### Step 4️⃣ — Protocol Document Parsing (Smart Extraction)

If the nurse uploaded a **protocol document**, the system reads it — but it doesn't send the *entire* 200+ page document to Gemini. Instead:

- **If PDF:** The system extracts all text using `pypdf`, then caps it at 30,000 characters
- **If Markdown (.md):** The system uses **smart regex-based extraction** to pull out *only* the clinically relevant sections:
  - ✅ Inclusion / Exclusion criteria
  - ✅ Washout periods
  - ✅ Prohibited medications
  - ✅ Schedule of Assessments
  - ✅ Synopsis

  This reduces a 200KB+ file down to ~30-60K characters — **saving cost and avoiding context window limits** with zero AI usage (pure text processing).

**Output:** A focused excerpt of the protocol, ready for Gemini to cross-reference.

---

### Step 5️⃣ — Gemini AI Extraction (The Brain)

Now the magic happens. The system sends **two things** to **Google Gemini 2.5 Flash**:

1. The **transcript** (from Step 3)
2. The **protocol excerpt** (from Step 4, if available)

Along with a detailed **prompt template** that instructs Gemini to:

- Identify the **visit type** (Day 1, Screening, Follow-up, etc.)
- Extract **every piece of medical data** from the conversation (vitals, labs, medications, ECG, injections, etc.)
- **Cross-reference** the transcript against the protocol — checking whether everything the protocol *requires* for this visit was actually discussed
- Flag any **missing items** (gaps the nurse needs to address)
- Capture **overflow information** — things discussed that don't fit standard form fields (patient concerns, unreported symptoms, safety observations)

**Gemini returns a structured JSON object** with 40+ fields covering:

| Category | What's extracted |
|---|---|
| **Patient basics** | Subject ID, visit date, age, HAE type |
| **Medications** | Current meds, last dose medication & date |
| **Pre-dose vitals** | Time, weight, blood pressure, heart rate, temperature, respiratory rate |
| **Post-dose vitals** | Same measurements taken after treatment |
| **ECG results** | Date, HR, PR, RR, QRS, QT intervals, normal/abnormal |
| **Lab work** | Whether collected, date, time, urine collection time |
| **Pregnancy test** | Childbearing potential, date, time, result |
| **Injection details** | Dose, injection site, laterality, start date/time (up to 2 injections) |
| **HAE attacks** | Attack history during run-in period |
| **Adverse events** | Any reported adverse events |
| **Overflow info** | Patient concerns, medication questions, unreported symptoms, safety observations |
| **Protocol compliance** | Required vs. found vs. missing items, eligibility criteria, washout periods |
| **Validation scores** | Completeness % (0-100), compliance % (0-100), review flags |

> **Built-in error handling:** If Gemini returns malformed JSON, the system auto-repairs it (fixes trailing commas, closes unclosed brackets, strips markdown formatting). If that fails, it retries without the protocol document. If *that* fails, it retries with a lower temperature setting.

---

### Step 6️⃣ — Eligibility Check (Rule Engine)

The extracted data is run through the **Rule Engine**, which checks the patient against the study's key criteria:

| Criteria | Rule | Example |
|---|---|---|
| **Inclusion #2** | Age must be ≥ 12 years | Patient is 34 → ✅ Pass |
| **Inclusion #3** | Must have HAE Type 1 or Type 2 | Type 1 → ✅ Pass |
| **Exclusion #6** | Must NOT be taking ACE inhibitors (lisinopril, enalapril, etc.) | No ACE inhibitors → ✅ Pass |

**Result:** The system displays either ✅ **"Patient is ELIGIBLE"** or ❌ **"Patient is NOT ELIGIBLE"** with a detailed breakdown.

---

### Step 7️⃣ — Washout Calculator

If the patient is on any medications, the system calculates when they'd be **clear to enter the study**:

- It checks the **protocol-defined washout periods** first (extracted by Gemini from the protocol document)
- Falls back to **hardcoded defaults** if no protocol data is available
- Calculates the **earliest run-in date** based on the last dose

Example: If the patient's last dose of Takhzyro was Jan 1, and the washout period is 70 days → earliest eligibility is **March 12**.

---

### Step 8️⃣ — Protocol Compliance Report

The dashboard shows a **compliance report** with:

- 📊 **Completeness Score** — What percentage of protocol-required data was found in the transcript?
- 🔴 **Missing Items** — Specific gaps the nurse needs to address (e.g., "Post-dose vitals not recorded", "ECG not discussed")
- ✅ **Found Items** — Confirmed protocol requirements that were discussed
- ⚠️ **Overflow Warnings** — Extra medical information that was captured but doesn't fit standard fields

---

### Step 9️⃣ — Auto-Fill the Visit Form (DOCX)

Finally, the nurse clicks **"Auto-Fill Day 1 Visit Form"** and the system:

1. Loads the official **DOCX template** (Day 1 Visit form)
2. Maps every extracted JSON field to the correct form field
3. Marks ✓ Yes / ✓ No checkboxes appropriately
4. Fills in blanks, tables, and underscored fields
5. Generates a **downloadable .docx file** ready for review and submission

---

## 🧩 System Components at a Glance

| # | Component | File | What it does |
|---|---|---|---|
| 1 | **Web Interface** | `app.py` | Streamlit app — the user-facing dashboard |
| 2 | **AI Service** | `ai_services.py` | `GeminiAIService` class — handles protocol parsing, Gemini API calls, JSON parsing/repair |
| 3 | **Prompt Template** | `gemini_prompt_template.py` | The detailed extraction prompt sent to Gemini with the JSON schema |
| 4 | **Rule Engine** | `logic.py` | `RuleEngine` — checks eligibility criteria; `WashoutCalculator` — computes medication clearance dates |
| 5 | **Form Filler** | `form_filler.py` | `FormFiller` — maps extracted data into the DOCX template |
| 6 | **Utilities** | `utils.py` | Helper functions (date arithmetic, etc.) |

---

## � The Pipeline in One Picture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        NURSE'S WORKFLOW                                │
│                                                                        │
│   📱 Record patient call                                               │
│       ↓                                                                │
│   📤 Upload audio + protocol to app                                    │
│       ↓                                                                │
│   🗣️ TRANSCRIPTION ─── Faster-Whisper (runs locally, no cloud)        │
│       ↓                                                                │
│   📋 PROTOCOL PARSING ─── Regex extracts key sections (no AI cost)    │
│       ↓                                                                │
│   🤖 GEMINI 2.5 FLASH ─── Extracts 40+ fields + cross-references     │
│       │                    protocol + captures overflow info            │
│       ↓                                                                │
│   ┌───────────────┬──────────────────┬─────────────────┐               │
│   │ 📊 Eligibility│ 💊 Washout       │ 📋 Protocol     │               │
│   │    Check      │    Calculator    │    Compliance   │               │
│   └───────┬───────┴────────┬─────────┴────────┬────────┘               │
│           └────────────────┼──────────────────┘                        │
│                            ↓                                           │
│   📊 DASHBOARD ─── Shows everything: transcript, eligibility,          │
│                    extracted data, gaps, warnings                       │
│       ↓                                                                │
│   📝 AUTO-FILL ─── Generates completed Day 1 Visit form (DOCX)        │
│       ↓                                                                │
│   📥 DOWNLOAD ─── Nurse downloads, reviews, submits                    │
│                                                                        │
│   ⏱️ Total time: ~1 minute (vs 30+ minutes manually)                  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 💡 Key Benefits

| Before (Manual) | After (Gemini Mode) |
|---|---|
| Nurse listens to recording and types everything | Audio auto-transcribed locally |
| Nurse reads 200-page protocol to check requirements | System auto-extracts relevant protocol sections |
| Nurse manually fills 40+ form fields | AI extracts and fills all fields automatically |
| Gaps discovered days later during review | Gaps flagged **immediately** with specific missing items |
| Extra patient concerns get lost | Overflow capture preserves everything discussed |
| 30-60 minutes per visit | ~1 minute per visit |

---

*Document prepared for internal review — STAR-0215-301 Voice Screening Assistant*  
*Generated: February 2026*
