#!/usr/bin/env python3
"""Simple test to verify AI Pipe connection"""

from secret import AIPIPE_TOKEN
from utils.llm_helper import call_llm
from utils.browser import fetch_quiz_content

def test_aipipe():
    """Test AI Pipe API connection"""
    print("="*60)
    print("Testing AI Pipe Connection")
    print("="*60)
    
    print(f"\nAPI Token: {AIPIPE_TOKEN[:20]}...")
    
    try:
        print("\nSending test prompt to LLM...")
        response = call_llm("What is 2+2? Answer with just the number.", max_tokens=50)
        print(f"✓ LLM Response: {response}")
        
        if "4" in response:
            print("✓ LLM is working correctly!")
        else:
            print("⚠ LLM responded but answer seems wrong")
            
    except Exception as e:
        print(f"✗ LLM test failed: {e}")
        return False
    
    return True

def test_browser():
    """Test browser fetching"""
    print("\n" + "="*60)
    print("Testing Browser")
    print("="*60)
    
    try:
        print("\nFetching example.com...")
        result = fetch_quiz_content("https://example.com")
        print(f"✓ Fetched {len(result['html'])} chars of HTML")
        print(f"✓ Text preview: {result['text'][:100]}...")
        return True
    except Exception as e:
        print(f"✗ Browser test failed: {e}")
        return False

def test_json_extraction():
    """Test JSON extraction from LLM response"""
    print("\n" + "="*60)
    print("Testing JSON Extraction")
    print("="*60)
    
    try:
        prompt = """Return this exact JSON and nothing else:
{"name": "test", "value": 42}"""
        
        print("\nAsking LLM to return JSON...")
        response = call_llm(prompt, max_tokens=100)
        print(f"Raw response: {response}")
        
        import json
        import re
        
        # Try direct parse
        try:
            data = json.loads(response)
            print(f"✓ Direct JSON parse successful: {data}")
        except:
            # Try extracting JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                data = json.loads(json_match.group())
                print(f"✓ Extracted JSON: {data}")
            else:
                print("✗ Could not extract JSON")
                return False
        
        return True
        
    except Exception as e:
        print(f"✗ JSON test failed: {e}")
        return False

if __name__ == "__main__":
    print("\n" + "="*60)
    print("RUNNING SIMPLE TESTS")
    print("="*60 + "\n")
    
    results = []
    
    # Test 1: AI Pipe
    results.append(("AI Pipe", test_aipipe()))
    
    # Test 2: Browser
    results.append(("Browser", test_browser()))
    
    # Test 3: JSON Extraction
    results.append(("JSON", test_json_extraction()))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{name:20s} {status}")
    
    all_passed = all(result[1] for result in results)
    if all_passed:
        print("\n✓ All tests passed! Ready to test Flask endpoint.")
    else:
        print("\n✗ Some tests failed. Fix these before proceeding.")