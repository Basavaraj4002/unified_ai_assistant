from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Dict, Any
import os

# Import all the custom modules that contain the application's logic
from utils import save_upload_file, extract_text_from_file
from gemini_processor import classify_document, get_marks_structure, summarize_general_document
from marks_analyzer import process_and_analyze_marks
from reporter import create_eligibility_report_pdf

# --- Automatic Directory Creation (The Fix) ---
# Define the directory name as a variable for consistency
REPORTS_DIR = "reports"
# This command creates the 'reports' directory if it doesn't already exist.
# The 'exist_ok=True' prevents an error if the folder is already there.
os.makedirs(REPORTS_DIR, exist_ok=True)
# -----------------------------------------------

app = FastAPI(title="Unified AI Document Assistant API")

# Mount the 'reports' directory to make generated PDFs downloadable via a URL
app.mount(f"/{REPORTS_DIR}", StaticFiles(directory=REPORTS_DIR), name="reports")

# Configure CORS to allow the frontend (on a different port) to communicate with this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for simplicity. In production, you might restrict this.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Define the structure for the eligibility analysis request body
class EligibilityAnalysisRequest(BaseModel):
    marks_data: List[Dict[str, Any]]
    criteria: Dict[str, int]
    max_marks_per_subject: int
    assessment_name: str

@app.post("/analyze-document/")
async def analyze_document_endpoint(file: UploadFile = File(...)):
    """
    This is the first endpoint that receives the uploaded file.
    It orchestrates the classification and initial processing.
    """
    try:
        # Save the file temporarily and get its path
        file_path = save_upload_file(file)
        # Extract all text from the document
        document_text = extract_text_from_file(file_path)
        
        if not document_text.strip():
            raise HTTPException(status_code=400, detail="Could not extract any readable text from the document.")
        
        # Step 1: Use the AI to classify the document
        doc_type = classify_document(document_text)

        # Step 2: Branch the logic based on the classification
        if doc_type == 'Type A':
            # If it's a marks sheet, get the structured data
            marks_payload = get_marks_structure(document_text)
            if "error" in marks_payload:
                raise HTTPException(status_code=400, detail=marks_payload["error"])
            return {"type": "Type A", "payload": marks_payload}
        else: # Handles 'Type B' and any classification errors
            # If it's a general document, get the summary
            summary = summarize_general_document(document_text)
            return {"type": "Type B", "payload": summary}
            
    except Exception as e:
        # General error handler for any unexpected issues
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

@app.post("/generate-eligibility-report/")
async def generate_eligibility_report_endpoint(request: EligibilityAnalysisRequest):
    """
    This endpoint is called for Type A documents after the user provides the eligibility criteria.
    It performs the final analysis and generates the PDF report.
    """
    try:
        # Perform all calculations: totals, percentages, eligibility, and ranking
        analysis_results = process_and_analyze_marks(
            request.marks_data, request.criteria, request.max_marks_per_subject
        )
        # Create the PDF report using the analysis results
        report_path = create_eligibility_report_pdf(analysis_results, request.assessment_name)
        
        # Construct a downloadable URL for the generated report
        # NOTE: This assumes the backend runs on http://127.0.0.1:8000
        base_url = "http://127.0.0.1:8000"
        # Ensure path separators are URL-friendly (forward slashes)
        report_url = f"{base_url}/{report_path.replace(os.sep, '/')}"
        
        # Send the downloadable URL back to the frontend
        return {"report_url": report_url}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")