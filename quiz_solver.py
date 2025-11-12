import requests
import time
from datetime import datetime, timedelta
from secret import EMAIL, SECRET, AIPIPE_TOKEN
from utils.browser import fetch_quiz_content
from utils.llm_helper import call_llm
from utils.data_processor import process_data_task
import json
import traceback
from urllib.parse import urljoin, urlparse

class QuizSolver:
    def __init__(self):
        self.email = EMAIL
        self.secret = SECRET
        self.start_time = None
        self.timeout = 180  # 3 minutes
        
    def solve_quiz_chain(self, initial_url):
        """Solve a chain of quizzes starting from initial_url"""
        self.start_time = datetime.now()
        current_url = initial_url
        attempt = 0
        
        print(f"\n{'='*60}")
        print(f"Starting quiz chain at {self.start_time}")
        print(f"Initial URL: {current_url}")
        print(f"{'='*60}\n")
        
        while current_url and self.within_time_limit():
            attempt += 1
            print(f"\n--- Attempt {attempt} ---")
            print(f"Time elapsed: {self.time_elapsed():.1f}s / {self.timeout}s")
            print(f"Solving: {current_url}")
            
            try:
                result = self.solve_single_quiz(current_url)
                
                if result.get('correct'):
                    print(f"✓ Correct answer!")
                    next_url = result.get('url')
                    if next_url:
                        print(f"→ Moving to next quiz: {next_url}")
                        current_url = next_url
                    else:
                        print("✓ Quiz chain completed!")
                        break
                else:
                    print(f"✗ Incorrect: {result.get('reason', 'Unknown error')}")
                    next_url = result.get('url')
                    if next_url:
                        print(f"→ Skipping to: {next_url}")
                        current_url = next_url
                    else:
                        print("Retrying same quiz...")
                        # Will retry in next iteration
                        time.sleep(2)
                        
            except Exception as e:
                print(f"✗ Error solving quiz: {e}")
                traceback.print_exc()
                time.sleep(2)
                
        if not self.within_time_limit():
            print(f"\n⏰ Time limit exceeded!")
        
        print(f"\n{'='*60}")
        print(f"Quiz chain ended. Total time: {self.time_elapsed():.1f}s")
        print(f"{'='*60}\n")
    
    def solve_single_quiz(self, quiz_url):
        """Solve a single quiz task"""
        # Step 1: Fetch the quiz content
        print("  Fetching quiz content...")
        quiz_data = fetch_quiz_content(quiz_url)
        quiz_html = quiz_data['html']
        quiz_text = quiz_data['text']
        
        # Step 2: Parse and understand the task using LLM
        print("  Analyzing task with LLM...")
        task_analysis = self.analyze_task(quiz_html, quiz_text, quiz_url)
        
        # NEW: Resolve relative URLs to absolute using quiz_url as base
        if 'data_source' in task_analysis and task_analysis['data_source']:
            task_analysis['data_source'] = urljoin(quiz_url, task_analysis['data_source'])
            print(f"  Resolved data_source: {task_analysis['data_source']}")
        
        if 'submit_url' in task_analysis and task_analysis['submit_url']:
            task_analysis['submit_url'] = urljoin(quiz_url, task_analysis['submit_url'])
            print(f"  Resolved submit_url: {task_analysis['submit_url']}")
        
        # Step 3: Execute the task
        print("  Executing task...")
        answer = self.execute_task(task_analysis)
        
        # Step 4: Submit the answer (submit_url now guaranteed absolute)
        print(f"  Submitting answer: {str(answer)[:100]}...")
        result = self.submit_answer(
            submit_url=task_analysis['submit_url'],  # Now absolute
            quiz_url=quiz_url,
            answer=answer
        )
        
        return result
    
    def analyze_task(self, quiz_html, quiz_text, quiz_url):
        """Use LLM to understand what the quiz is asking"""
        
        prompt = f"""You are analyzing a quiz task. 
        

The quiz page visible text is:
{quiz_text}

HTML snippet (for extracting URLs):
{quiz_html[:2000]}

The current quiz base URL is: {quiz_url}

Extract and return a JSON object with:
1. "task_description": A clear description of what needs to be done
2. "submit_url": The ABSOLUTE URL (full https://...) where the answer should be submitted
3. "data_source": The ABSOLUTE URL (full https://...) or location of data to download (if any, otherwise null)
4. "data_type": Type of data (pdf, csv, json, image, api, webpage, etc.)
5. "question": The specific question being asked
6. "answer_type": Expected answer type (number, string, boolean, json, base64, etc.)
7. "steps": Array of steps needed to solve this

Return ONLY valid JSON, no other text."""
        if 'scrape' in quiz_text.lower():
            prompt += "\nFor scraping: Look for unique codes (e.g., 8-char alphanumeric in <code> tags or highlighted text). Ignore URLs/emails."
        response = call_llm(prompt , max_tokens=1500)
        
        try:
            # Try to parse as JSON
            task_info = json.loads(response)
        except:
            # If LLM didn't return pure JSON, try to extract it
            import re
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                task_info = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse task analysis")
        
        print(f"  Task: {task_info.get('task_description', 'Unknown')}")
        return task_info
    
    def execute_task(self, task_analysis):
        """Execute the task based on analysis (safe debug + validation)."""
        # ... (existing debug print unchanged)
        
        # Basic validation: ensure we have a dict-like object
        if not isinstance(task_analysis, dict):
            print("ERROR: task_analysis is not a dict; aborting task execution.")
            return {"error": "invalid_task_analysis", "detail": repr(task_analysis)}

        # NEW: Validate resolved URLs (post-resolution from solve_single_quiz)
        if 'data_source' in task_analysis and task_analysis['data_source']:
            parsed = urlparse(task_analysis['data_source'])
            if not parsed.scheme:
                return {"error": "unresolved_data_source", "value": task_analysis['data_source']}
        
        if 'submit_url' in task_analysis and task_analysis['submit_url']:
            parsed = urlparse(task_analysis['submit_url'])
            if not parsed.scheme:
                return {"error": "unresolved_submit_url", "value": task_analysis['submit_url']}
        
        # Run the processor and catch exceptions so the thread doesn't die silently
        try:
            answer = process_data_task(task_analysis)
            
            # NEW: Quick sanity check on answer
            if isinstance(answer, dict) and 'error' in answer:
                print(f"WARNING: process_data_task returned error: {answer['error']}")
                # Optional: Retry once by re-calling with debug=True if your process_data_task supports it
                # answer = process_data_task(task_analysis, debug=True)
                return answer  # Still submit, but log for debugging
            
            return answer
        except Exception as e:
            print("ERROR executing process_data_task:", type(e).__name__, e)
            traceback.print_exc()  # Add for better local debugging
            return {"error": "processing_failed", "exception": str(e)}
    
    def submit_answer(self, submit_url, quiz_url, answer):
        """Submit the answer to the specified endpoint"""
        payload = {
            "email": self.email,
            "secret": self.secret,
            "url": quiz_url,
            "answer": answer
        }
        
        try:
            response = requests.post(submit_url, json=payload, timeout=30)
            response.raise_for_status()  # Raises on 4xx/5xx
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 500:
                print(f"  Server 500 on submit (bad answer? {str(answer)[:50]}...): {e}")
                return {'correct': False, 'reason': 'server_error_500', 'url': None}  # Treat as incorrect, no retry
            raise  # Re-raise other HTTP errors
        except Exception as e:
            print(f"  Submit network error: {e}")
            raise
    
    def within_time_limit(self):
        """Check if still within 3-minute time limit"""
        if not self.start_time:
            return True
        elapsed = (datetime.now() - self.start_time).total_seconds()
        return elapsed < self.timeout
    
    def time_elapsed(self):
        """Get elapsed time in seconds"""
        if not self.start_time:
            return 0
        return (datetime.now() - self.start_time).total_seconds()