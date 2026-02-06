import os
from pypdf import PdfReader

pdf_path = "C4531029_Original Protocol_21Nov2024 (1).pdf"

def analyze_pdf_pages(path, start_page, end_page):
    print(f"--- Extracting pages {start_page}-{end_page} from {path} ---")
    try:
        reader = PdfReader(path)
        # Pages are 0-indexed in pypdf
        for i in range(start_page - 1, end_page):
            if i < len(reader.pages):
                print(f"\n--- Page {i+1} ---")
                print(reader.pages[i].extract_text())
    except Exception as e:
        print(f"Error reading PDF: {e}")

if __name__ == "__main__":
    analyze_pdf_pages(pdf_path, 33, 37)
