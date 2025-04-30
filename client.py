#!/usr/bin/env python3
"""
Simple client for the Tender Document Analyzer API
"""

import sys
import time
import requests
import argparse
from pathlib import Path

def parse_arguments():
    parser = argparse.ArgumentParser(description="Tender Document Analyzer API Client")
    parser.add_argument("--file", required=True, help="Path to the PDF file to analyze")
    parser.add_argument("--api", default="http://localhost:8000", help="API endpoint URL")
    parser.add_argument("--output", default="./analysis_result.pdf", help="Path to save the result PDF")
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    file_path = Path(args.file)
    api_url = args.api
    output_path = Path(args.output)
    
    if not file_path.exists():
        print(f"Error: File {file_path} does not exist")
        return 1
    
    print(f"Uploading {file_path} for analysis...")
    
    # Step 1: Upload file for analysis
    with open(file_path, "rb") as f:
        response = requests.post(
            f"{api_url}/analyze",
            files={"file": (file_path.name, f, "application/pdf")}
        )
    
    if response.status_code != 202:
        print(f"Error: {response.json().get('error', 'Unknown error')}")
        return 1
    
    task_id = response.json()["task_id"]
    print(f"Document accepted for analysis. Task ID: {task_id}")
    
    # Step 2: Poll for status
    print("Waiting for analysis to complete...")
    
    while True:
        status_response = requests.get(f"{api_url}/status/{task_id}")
        
        if status_response.status_code != 200:
            print(f"Error checking status: {status_response.json().get('error', 'Unknown error')}")
            return 1
        
        status_data = status_response.json()
        
        if status_data["status"] == "processing":
            print(".", end="", flush=True)
            time.sleep(3)
            continue
        
        if status_data["status"] == "failed":
            print(f"\nAnalysis failed: {status_data.get('error', 'Unknown error')}")
            return 1
        
        if status_data["status"] == "completed":
            print("\nAnalysis completed successfully!")
            break
    
    # Step 3: Download the result
    print(f"Downloading result to {output_path}...")
    
    download_response = requests.get(f"{api_url}/download/{task_id}")
    
    if download_response.status_code != 200:
        print(f"Error downloading result: {download_response.text}")
        return 1
    
    # Save the result
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(download_response.content)
    
    print(f"Analysis result saved to {output_path}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 