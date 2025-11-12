import requests
import json  # For serialization
import traceback  # For errors
from urllib.parse import urlparse
import os  # (optional)

from utils.llm_helper import call_llm  # NEW: For processing content
from utils.browser import fetch_quiz_content  # NEW: For webpages

def process_data_task(task_analysis, base_url=None):
    data_source = task_analysis.get('data_source')
    data_type = task_analysis.get('data_type', 'webpage')
    submit_url = task_analysis.get('submit_url')
    
    print(f"process_data_task: resolved data_source = {data_source}")
    print(f"process_data_task: resolved submit_url = {submit_url}")
    
    if not data_source and base_url:  # NEW: Fallback to base_url
        data_source = base_url
        print(f"  Fallback data_source: {data_source}")
    
    if not data_source:
        return {'error': 'no_data_source'}
    
    try:
        # Detect file type from extension/path
        parsed_url = urlparse(data_source)
        path = parsed_url.path.lower()
        is_file_download = any(ext in path for ext in ['.csv', '.pdf', '.json', '.xlsx', '.txt', '.mp3', '.wav'])
        
        content = None
        if is_file_download or data_type in ['csv', 'pdf', 'json', 'image']:  # Exclude 'api' unless ext
            print(f"  Downloading file ({data_type}) via requests...")
            response = requests.get(data_source, timeout=30, stream=True)
            response.raise_for_status()
            
            if data_type == 'csv':
                import pandas as pd
                from io import StringIO
                csv_text = response.text
                df = pd.read_csv(StringIO(csv_text))
                content = {  # Summary to avoid huge dumps
                    'shape': list(df.shape),
                    'columns': list(df.columns),
                    'head': df.head(5).to_dict('records'),
                    'describe': df.describe().to_dict()
                }
                print(f"  Loaded CSV: {df.shape[0]} rows, columns: {list(df.columns)}")
            
            elif data_type == 'pdf':
                import fitz  # pymupdf
                doc = fitz.open(stream=response.content, filetype='pdf')
                content = [page.get_text() for page in doc]
                doc.close()
            
            elif data_type in ['json']:
                content = response.json()
            
            else:  # Generic text/binary
                content = response.text if 'text/' in response.headers.get('Content-Type', '') else response.content
        
        else:  # Webpage/scrape/api: Use browser
            print(f"  Fetching webpage via browser...")
            quiz_data = fetch_quiz_content(data_source)
            content = quiz_data['text']  # Or 'html' if needed
        
        # Use LLM to analyze/process content
        question = task_analysis.get('question', '')
        steps = task_analysis.get('steps', [])
        # Safe dump for prompt
        dump_content = json.dumps(content, default=str) if content else str(content)
        prompt = f"""Based on the {data_type} data below, answer the question: {question}

Data: {dump_content[:4000]}...  # Truncate if huge

Steps to follow: {steps}

Return just the final answer (e.g., number, string, JSON)."""
        
        # NEW: Safe LLM call
        try:
            if data_type == 'csv' or 'audio' in question.lower():
                answer = call_llm(prompt, model="openai/gpt-4o", temperature=0.0, max_tokens=100)  # Short for numbers
            else:
                answer = call_llm(prompt, max_tokens=500)  # Uses default
            
            print(f"  Processed answer preview: {str(answer)[:50]}...")
            return answer.strip() if isinstance(answer, str) else answer
        except Exception as llm_e:
            print(f"  LLM error: {llm_e}")
            return {'error': 'llm_failed', 'exception': str(llm_e)[:200]}
        
    except Exception as e:
        print(f"  Fetch/Process error: {e}")
        return {'error': 'fetch_failed', 'exception': str(e)[:200]}