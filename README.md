# Tender Document Analyzer API

This application analyzes tender documents through a 3-step process:
1. Text extraction using OCR
2. Semantic chunking and vector embedding
3. Key point extraction using LLM (Ollama llama3.2)

The application is now implemented as a FastAPI web service, allowing for easy integration with other systems.

## Installation

1. Clone the repository
2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```
3. Make sure you have Tesseract OCR installed on your system:
   - For Windows: https://github.com/UB-Mannheim/tesseract/wiki
   - For Linux: `sudo apt-get install tesseract-ocr`
   - For macOS: `brew install tesseract`

4. (Optional) Install Ollama if you want to use the LLM features:
   https://ollama.com/download

## Running the Application

Start the application with:

```
python tender_analyzer/main.py
```

The API will be available at http://localhost:8000

## API Endpoints

### Welcome Page
- **GET** `/`
  - Returns a welcome message

### Analyze Document
- **POST** `/analyze`
  - Upload a PDF document for analysis
  - Returns a task ID for checking status

### Check Analysis Status
- **GET** `/status/{task_id}`
  - Check the status of a document analysis task
  - Returns status (processing, completed, or failed)

### Download Results
- **GET** `/download/{task_id}`
  - Download the analysis results PDF
  - Only available when analysis is complete

## Example Usage

```python
import requests

# Upload document for analysis
with open('tender_document.pdf', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/analyze',
        files={'file': ('tender_document.pdf', f, 'application/pdf')}
    )
    
task_id = response.json()['task_id']

# Check status
status_response = requests.get(f'http://localhost:8000/status/{task_id}')
status = status_response.json()

# When completed, download results
if status['status'] == 'completed':
    download_url = f'http://localhost:8000/download/{task_id}'
    result = requests.get(download_url)
    
    # Save the PDF
    with open('analysis_results.pdf', 'wb') as f:
        f.write(result.content)
```

## Features

- **Asynchronous Processing**: Documents are processed in the background, allowing users to check status and retrieve results when ready
- **PDF Analysis**: Extract and analyze key information from tender documents
- **OCR Support**: Process scanned documents using optical character recognition
- **Key Point Extraction**: Automatically extract important information like deadlines, requirements, costs, and quality standards 