import os
import shutil
import pdfplumber
import docx
from fastapi import UploadFile
import fitz  # PyMuPDF
import easyocr
import numpy as np

# --- OCR Initialization ---
# We initialize the reader once when the application starts.
# This is a heavy object and loading it every time would be very slow.
# ['en'] specifies that we are looking for the English language.
print("Initializing EasyOCR Reader... (This may take a moment)")
reader = easyocr.Reader(['en'])
print("EasyOCR Reader initialized successfully.")
# -------------------------


UPLOAD_DIR = "uploads"

def save_upload_file(upload_file: UploadFile) -> str:
    """Saves the uploaded file to a temporary directory and returns the path."""
    if not os.path.exists(UPLOAD_DIR):
        os.makedirs(UPLOAD_DIR)
    
    file_path = os.path.join(UPLOAD_DIR, upload_file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(upload_file.file, buffer)
    return file_path

def perform_ocr_on_pdf(file_path: str) -> str:
    """Performs OCR on each page of a PDF and returns the combined text."""
    print(f"Performing OCR on {file_path}...")
    try:
        doc = fitz.open(file_path)
        full_text = ""
        for page_num, page in enumerate(doc):
            print(f"  - Processing page {page_num + 1}/{len(doc)}")
            # Convert the page to an image (pixmap)
            pix = page.get_pixmap()
            img_bytes = pix.tobytes("png")
            
            # Use EasyOCR to read text from the image bytes
            # The 'detail=0' makes it return a simple list of strings
            text_list = reader.readtext(img_bytes, detail=0, paragraph=True)
            page_text = "\n".join(text_list)
            full_text += page_text + "\n\n"
        
        doc.close()
        return full_text
    except Exception as e:
        print(f"An error occurred during OCR: {e}")
        return ""

def extract_text_from_file(file_path: str) -> str:
    """
    Extracts text from various documents. It first tries normal extraction,
    and if that fails, it falls back to OCR for PDFs.
    """
    text = ""
    try:
        if file_path.endswith(".pdf"):
            # --- Smart Text Extraction Logic ---
            # 1. Try the fast, standard method first
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            
            # 2. If standard method yields little/no text, assume it's a scanned image and use OCR
            if len(text.strip()) < 50: # A threshold to detect if it's likely a scanned PDF
                print("Standard text extraction failed. Falling back to OCR...")
                text = perform_ocr_on_pdf(file_path)

        elif file_path.endswith(".docx"):
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                text += para.text + "\n"
    except Exception as e:
        print(f"An error occurred during text extraction: {e}")
        return ""
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
    return text