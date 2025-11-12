#!/usr/bin/env python3
"""
Local testing script for quiz solver components
"""

from quiz_solver import QuizSolver
from utils.browser import fetch_quiz_content
from utils.llm_helper import call_llm

def test_browser():
    """Test browser fetching"""
    print("Testing browser...")
    result = fetch_quiz_content("https://example.com")
    print(f"✓ Fetched {len(result['html'])} chars")
    print(f"Text preview: {result['text'][:200]}...")

def test_llm():
    """Test LLM connection"""
    print("\nTesting LLM...")
    response = call_llm("What is 2+2? Answer with just the number.")
    print(f"✓ LLM Response: {response}")

def test_quiz_solver():
    """Test full quiz solver with demo URL"""
    print("\nTesting quiz solver with demo...")
    solver = QuizSolver()
    solver.solve_quiz_chain("https://tds-llm-analysis.s-anand.net/demo")

if __name__ == "__main__":
    print("="*60)
    print("LOCAL TESTING")
    print("="*60)
    
    try:
        test_browser()
    except Exception as e:
        print(f"✗ Browser test failed: {e}")
    
    try:
        test_llm()
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
    
    try:
        test_quiz_solver()
    except Exception as e:
        print(f"✗ Quiz solver test failed: {e}")
    
    print("\n" + "="*60)
    print("Testing complete!")
    print("="*60)