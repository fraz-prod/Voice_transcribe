from docx import Document
from datetime import datetime
import io

class FormFiller:
    def __init__(self, template_path):
        self.template_path = template_path

    def fill_form(self, data: dict, is_eligible: bool = False) -> io.BytesIO:
        """
        Fills the DOCX template with data.
        Returns a BytesIO object of the filled document.
        """
        doc = Document(self.template_path)

        # Helper to mark Yes/No checkboxes
        def mark_yes_no(paragraph, answer_yes: bool):
            """
            Replaces ' Yes ' and ' No' patterns with [X] markers.
            answer_yes=True marks Yes, answer_yes=False marks No.
            """
            text = paragraph.text
            if answer_yes:
                text = text.replace("  Yes  ", "  [X] Yes  ").replace("  No", "  [ ] No")
                text = text.replace(" Yes  No", " [X] Yes  [ ] No")
            else:
                text = text.replace("  Yes  ", "  [ ] Yes  ").replace("  No", "  [X] No")
                text = text.replace(" Yes  No", " [ ] Yes  [X] No")
            paragraph.text = text

        # Helper to fill underscores
        def fill_underscores(paragraph, value: str):
            if "_____" in paragraph.text:
                paragraph.text = paragraph.text.replace("__________", str(value), 1)
                paragraph.text = paragraph.text.replace("_____", str(value), 1)

        # === SECTION 1: Visit Performed ===
        for para in doc.paragraphs:
            if "Was the visit performed?" in para.text:
                mark_yes_no(para, True)
                break

        # === SECTION 2: Visit Date ===
        if "visit_date" in data:
            for para in doc.paragraphs:
                if "Visit Date:" in para.text:
                    fill_underscores(para, data["visit_date"])
                    break

        # === SECTION 3: Weekly Diary ===
        for para in doc.paragraphs:
            if "did the participant complete all weekly diary entries" in para.text:
                mark_yes_no(para, True)
                break

        # === SECTION 4: HAE Attack Contact ===
        for para in doc.paragraphs:
            if "did the site make contact with the participant to collect" in para.text:
                mark_yes_no(para, True)
                break

        # === SECTION 5: Adverse Events ===
        for para in doc.paragraphs:
            if "Were AEs reviewed at this visit?" in para.text:
                mark_yes_no(para, True)
                break

        for para in doc.paragraphs:
            if "Any new AEs reported?" in para.text:
                # Default: No new AEs (happy path)
                ae_status = data.get("adverse_events", "None")
                mark_yes_no(para, ae_status.lower() != "none")
                break

        # === SECTION 6: Concomitant Medications ===
        for para in doc.paragraphs:
            if "Were conmeds reviewed at this visit?" in para.text:
                mark_yes_no(para, True)
                break

        for para in doc.paragraphs:
            if "Any new or changes to conmeds reported?" in para.text:
                # Check if there are non-standard meds or changes
                meds = data.get("medications", [])
                has_changes = len(meds) > 1 or any(m.lower() != "takhzyro" for m in meds)
                mark_yes_no(para, has_changes)
                break

        # === SECTION 7: Eligibility Criteria ===
        for para in doc.paragraphs:
            if "Were all eligibility criteria met" in para.text:
                mark_yes_no(para, is_eligible)
                break

        for para in doc.paragraphs:
            if "Did the participant continue to meet eligibility at Day 1 visit?" in para.text:
                continued = data.get("continued_eligibility", "Yes")
                mark_yes_no(para, continued.lower() == "yes")
                break

        # === SECTION 8: IRT Randomization ===
        for para in doc.paragraphs:
            if "Subject randomized in IRT?" in para.text:
                mark_yes_no(para, True)
                break

        # === SECTION 9: Physical Exam (Pre-dose) ===
        for i, para in enumerate(doc.paragraphs):
            if "Physical Exam completed?" in para.text:
                mark_yes_no(para, True)
                break

        for para in doc.paragraphs:
            if "Any clinically significant abnormalities?" in para.text:
                mark_yes_no(para, False)  # Happy path: No abnormalities
                break

        # === SECTION 10: Pre-Dose Vitals (Table 0) ===
        if "vitals_pre" in data:
            vitals = data["vitals_pre"]
            if len(doc.tables) > 0:
                table = doc.tables[0]
                try:
                    table.rows[0].cells[0].text += f" {vitals.get('weight', '')}"
                    table.rows[1].cells[0].text += f" {vitals.get('bp', '')}"
                    table.rows[2].cells[0].text += f" {vitals.get('hr', '')}"
                    table.rows[3].cells[0].text += f" {vitals.get('temp', '')}"
                    table.rows[4].cells[0].text += f" {vitals.get('rr', '')}"
                except IndexError:
                    pass

        # === SECTION 11: ECG ===
        for para in doc.paragraphs:
            if "Was the 12-lead ECG performed?" in para.text:
                mark_yes_no(para, True)
                break

        ecg = data.get("ecg", {})
        for para in doc.paragraphs:
            if "Results:" in para.text and "Normal" in para.text:
                result = ecg.get("result", "Normal")
                if result == "Normal":
                    para.text = para.text.replace(" Normal ", " [X] Normal ")
                break

        # === SECTION 12: Labs ===
        for para in doc.paragraphs:
            if "Were all required labs collected?" in para.text:
                labs = data.get("labs", {})
                mark_yes_no(para, labs.get("collected", True))
                break

        for para in doc.paragraphs:
            if "Was Pharmacogenetics (DNA paxgene) sample collected?" in para.text:
                mark_yes_no(para, False)  # Often not collected
                break

        # === SECTION 13: Childbearing Potential ===
        for para in doc.paragraphs:
            if "Is subject of childbearing potential?" in para.text:
                mark_yes_no(para, False)  # Happy path: No
                break

        # === SECTION 14: Investigational Product ===
        for para in doc.paragraphs:
            if "Was investigational product administered?" in para.text:
                mark_yes_no(para, True)
                break

        # === SECTION 15: Injection 1 Details ===
        if "injection" in data:
            inj = data["injection"]
            for para in doc.paragraphs:
                if "Dose administered:" in para.text:
                    fill_underscores(para, inj.get("dose", ""))
                    break

            for para in doc.paragraphs:
                if "Anatomical Location:" in para.text:
                    fill_underscores(para, inj.get("site", ""))
                    break

        # Injection 1 Interrupted
        for para in doc.paragraphs:
            if "Was injection interrupted?" in para.text:
                mark_yes_no(para, False)
                break

        # === SECTION 16: Post-Dose Vitals (Table 1) ===
        if "vitals_post" in data:
            vitals = data["vitals_post"]
            if len(doc.tables) > 1:
                table = doc.tables[1]
                try:
                    table.rows[0].cells[0].text += f" {vitals.get('weight', '')}"
                    table.rows[1].cells[0].text += f" {vitals.get('bp', '')}"
                    table.rows[2].cells[0].text += f" {vitals.get('hr', '')}"
                    table.rows[3].cells[0].text += f" {vitals.get('temp', '')}"
                    table.rows[4].cells[0].text += f" {vitals.get('rr', '')}"
                except IndexError:
                    pass

        # === SECTION 17: Physical Exam (Post-dose) ===
        # Find the SECOND occurrence of "Physical Exam completed?"
        pe_count = 0
        for para in doc.paragraphs:
            if "Physical Exam completed?" in para.text:
                pe_count += 1
                if pe_count == 2:
                    mark_yes_no(para, True)
                    break

        # Find the SECOND occurrence of abnormalities
        abn_count = 0
        for para in doc.paragraphs:
            if "Any clinically significant abnormalities?" in para.text:
                abn_count += 1
                if abn_count == 2:
                    mark_yes_no(para, False)
                    break

        # Save to buffer
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer
