import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

# Load variables from the .env file into the environment
load_dotenv()

# Configure the Gemini API with the key from the environment
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def classify_document(document_text: str) -> str:
    """Step 1: Classifies the document as 'Type A' or 'Type B'."""
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    Analyze the content of the following document text. Classify it as one of two types:
    - 'Type A': If it is a marks sheet, grade report, or contains a structured table of student scores.
    - 'Type B': If it is a general document like a research paper, essay, notice, letter, or any other text.
    Respond with ONLY 'Type A' or 'Type B'.

    Text:
    ---
    {document_text[:4000]}
    ---
    """
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "Type B"

def get_marks_structure(document_text: str) -> dict:
    """Step 2 (for Type A): Extracts column headers and structured data."""
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    Analyze the following text from a marks sheet and respond with a single, clean JSON object.
    The JSON object must have two keys: "columns" and "data".
    "columns" must be an array of strings of the mark column headers.
    "data" must be an array of objects for each student.

    Example: {{"columns": ["Maths", "Science"], "data": [{{"Name": "Student A", "Maths": 85, "Science": 92}}]}}

    Text:
    ---
    {document_text}
    ---
    Respond ONLY with the JSON object.
    """
    try:
        response = model.generate_content(prompt)
        cleaned_json_text = response.text.strip().replace("```json", "").replace("```", "")
        return json.loads(cleaned_json_text)
    except Exception:
        return {"error": "Failed to parse the marks sheet structure."}

def summarize_general_document(document_text: str) -> str:
    """Step 2 (for Type B): Generates a concise summary."""
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    prompt = f"""
    Provide a concise, insightful summary for the following document text.
    Identify the core topics and any key decisions or action items.
    Use bullet points where applicable to improve readability.

    Document Text:
    ---
    {document_text}
    ---
    """
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Could not generate summary: {str(e)}"