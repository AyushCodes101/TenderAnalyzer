#!/usr/bin/env python3
"""
Tender Document Analyzer API

This application analyzes tender documents through a 3-step process:
1. Text extraction using OCR
2. Semantic chunking and vector embedding
3. Key point extraction using LLM (Ollama llama3.2)

Now wrapped in FastAPI for web access.
"""

import os
import sys
import tempfile
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import uvicorn
from loguru import logger

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from src.extraction.pdf_extractor import PdfExtractor
from src.chunking.semantic_chunker import SemanticChunker
from src.analysis.key_point_extractor import KeyPointExtractor
from src.output.pdf_generator import OutputPdfGenerator
from src.utils.config import setup_logging, Config

# Configure Ollama API base URL from environment variable if available
if "OLLAMA_API_BASE" in os.environ:
    Config.OLLAMA_API_BASE = os.environ["OLLAMA_API_BASE"]
    logger.info(f"Using Ollama API base URL from environment: {Config.OLLAMA_API_BASE}")

# Initialize FastAPI app
app = FastAPI(
    title="Tender Document Analyzer API",
    description="API for analyzing tender documents and extracting key information",
    version="1.0.0"
)

# Setup logging
setup_logging("INFO")

# Create a temporary directory for uploads
UPLOAD_DIR = Path("./uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Create output directory
OUTPUT_DIR = Path("./output")
OUTPUT_DIR.mkdir(exist_ok=True)

# Store background task results
analysis_results = {}

class AnalysisRequest(BaseModel):
    """Request model for analysis status check"""
    task_id: str

@app.get("/")
async def root():
    """API root endpoint"""
    return {"message": "Welcome to Tender Document Analyzer API"}

@app.post("/analyze")
async def analyze_document(background_tasks: BackgroundTasks, file: UploadFile = File(...)):
    """
    Upload and analyze a tender document
    """
    try:
        # Create a unique task ID
        task_id = f"{file.filename.replace('.', '_')}_{id(file)}"
        
        # Save the uploaded file
        file_path = UPLOAD_DIR / file.filename
        with open(file_path, "wb") as f:
            f.write(await file.read())
        
        logger.info(f"File uploaded: {file_path}")
        
        # Add the analysis task to background tasks
        background_tasks.add_task(
            process_document,
            task_id=task_id,
            file_path=file_path
        )
        
        return JSONResponse(
            status_code=202,
            content={
                "message": "Document accepted for analysis",
                "task_id": task_id,
                "status": "processing"
            }
        )
    
    except Exception as e:
        logger.error(f"Error during upload: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": f"Failed to process the document: {str(e)}"}
        )

@app.get("/status/{task_id}")
async def check_status(task_id: str):
    """
    Check the status of a document analysis task
    """
    if task_id not in analysis_results:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task ID {task_id} not found"}
        )
    
    result = analysis_results[task_id]
    
    if result["status"] == "processing":
        return JSONResponse(
            status_code=200,
            content={"status": "processing", "task_id": task_id}
        )
    
    elif result["status"] == "completed":
        return JSONResponse(
            status_code=200,
            content={
                "status": "completed",
                "task_id": task_id,
                "output_path": str(result["output_path"]),
                "download_url": f"/download/{task_id}"
            }
        )
    
    elif result["status"] == "failed":
        return JSONResponse(
            status_code=200,
            content={
                "status": "failed",
                "task_id": task_id,
                "error": result["error"]
            }
        )

@app.get("/download/{task_id}")
async def download_results(task_id: str):
    """
    Download the analysis results
    """
    if task_id not in analysis_results:
        return JSONResponse(
            status_code=404,
            content={"error": f"Task ID {task_id} not found"}
        )
    
    result = analysis_results[task_id]
    
    if result["status"] != "completed":
        return JSONResponse(
            status_code=400,
            content={"error": f"Analysis for task {task_id} is not completed yet"}
        )
    
    output_path = result["output_path"]
    
    if not os.path.exists(output_path):
        return JSONResponse(
            status_code=404,
            content={"error": f"Output file not found"}
        )
    
    return FileResponse(
        path=output_path,
        filename=os.path.basename(output_path),
        media_type="application/pdf"
    )

def process_document(task_id: str, file_path: Path):
    """
    Process the document in the background
    
    Args:
        task_id (str): Task identifier
        file_path (Path): Path to the uploaded file
    """
    # Initialize the task status
    analysis_results[task_id] = {
        "status": "processing",
        "task_id": task_id
    }
    
    try:
        logger.info(f"Starting analysis for task {task_id}")
        
        # 1. Extract text from PDF using OCR
        logger.info("Step 1: Extracting text from PDF")
        pdf_extractor = PdfExtractor()
        extracted_text = pdf_extractor.extract(file_path)
        
        # 2. Semantic chunking and vector embedding
        logger.info("Step 2: Performing semantic chunking and embedding")
        chunker = SemanticChunker()
        vector_store = chunker.process(extracted_text)
        
        # 3. Extract key points using LLM
        logger.info("Step 3: Extracting key points using LLM")
        key_point_extractor = KeyPointExtractor(vector_store)
        key_points = key_point_extractor.extract_key_points()
        
        # 4. Generate output PDF
        logger.info("Step 4: Generating output PDF")
        output_generator = OutputPdfGenerator()
        output_path = output_generator.generate(
            key_points,
            output_dir=OUTPUT_DIR,
            input_filename=os.path.basename(file_path)
        )
        
        logger.success(f"Analysis complete! Results saved to {output_path}")
        
        # Update the task status
        analysis_results[task_id] = {
            "status": "completed",
            "task_id": task_id,
            "output_path": output_path
        }
        
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        logger.exception("Detailed error information:")
        
        # Update the task status
        analysis_results[task_id] = {
            "status": "failed",
            "task_id": task_id,
            "error": str(e)
        }

if __name__ == "__main__":
    # Run the FastAPI app with uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 