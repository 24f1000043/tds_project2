from playwright.sync_api import sync_playwright
import time

def fetch_quiz_content(url, wait_time=3):
    """
    Fetch rendered HTML content from a URL using headless browser
    This handles JavaScript-rendered content
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # Navigate to URL
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to render
            time.sleep(wait_time)
            
            # Get the full page content
            content = page.content()
            
            # Also get visible text (useful for analysis)
            body_text = page.locator('body').inner_text()
            
            browser.close()
            
            return {
                'html': content,
                'text': body_text,
                'url': url
            }
            
        except Exception as e:
            browser.close()
            raise Exception(f"Failed to fetch {url}: {e}")

def download_file_from_page(url, file_url):
    """
    Download a file that's linked on a page
    Returns the downloaded content as bytes
    """
    import requests
    
    # Handle relative URLs
    if not file_url.startswith('http'):
        from urllib.parse import urljoin
        file_url = urljoin(url, file_url)
    
    response = requests.get(file_url, timeout=30)
    response.raise_for_status()
    
    return response.content