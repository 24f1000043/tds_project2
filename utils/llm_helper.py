import requests
from secret import AIPIPE_TOKEN

def call_llm(prompt, model="openai/gpt-4o", temperature=0.0, max_tokens=2000):
    """
    Call LLM via AI Pipe API (OpenRouter endpoint)
    
    Args:
        prompt: The prompt to send
        model: Model to use (format: "provider/model-name")
               Examples: "openai/gpt-4o" (recommended for accuracy), "google/gemini-2.0-flash-lite-001"
        temperature: Creativity level (0-1; 0.0 for exact math/sums)
        max_tokens: Maximum response length
    
    Returns:
        String response from LLM
    """
    
    # AI Pipe OpenRouter endpoint
    url = "https://aipipe.org/openrouter/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        return data['choices'][0]['message']['content']
        
    except Exception as e:
        print(f"LLM API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise

def call_vision_llm(prompt, image_base64, model="openai/gpt-4o"):
    """
    Call vision-enabled LLM for image analysis
    
    Args:
        prompt: Text prompt
        image_base64: Base64 encoded image
        model: Vision model to use (must support vision)
               Example: "openai/gpt-4o"
    
    Returns:
        String response
    """
    url = "https://aipipe.org/openrouter/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {AIPIPE_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 2000,
        "temperature": 0.0  # NEW: Deterministic for analysis
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=60)
        response.raise_for_status()
        
        data = response.json()
        return data['choices'][0]['message']['content']
        
    except Exception as e:
        print(f"Vision LLM API Error: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Response: {e.response.text}")
        raise