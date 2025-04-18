import asyncio
from playwright.async_api import async_playwright
import boto3
import json
import os
from dotenv import load_dotenv
from typing import List
import random
import asyncio

load_dotenv()

async def scrape_page(page, page_number: int) -> List[str]:
    try:
        print(f"Attempting to load page {page_number}...")
        
        # Try to load the specific page
        response = await page.goto(
            f"https://letterboxd.com/films/by/name/page/{page_number}", 
            timeout=60000,
            wait_until="domcontentloaded"
        )
        
        if not response:
            raise Exception("No response received from server")
            
        if response.status != 200:
            raise Exception(f"Server returned status code: {response.status}")
            
        print(f"Page {page_number} loaded successfully, waiting for content...")
        
        try:
            # First wait for the page to be interactive
            await page.wait_for_load_state("domcontentloaded")
            await asyncio.sleep(2)  # Give some time for dynamic content
            
            # Then wait for the specific content
            await page.wait_for_selector("ul.poster-list", timeout=30000)
            
            # Get the links
            page_links = await page.eval_on_selector_all(
                "ul.poster-list a[href^='/film/']",
                "elements => elements.map(el => el.href)"
            )
            
            if not page_links:
                raise Exception("No links found on page")
            
            print(f"Successfully extracted {len(page_links)} links from page {page_number}")
            return page_links
            
        except Exception as e:
            # If the selector isn't found, check if we got a different page
            content = await page.content()
            if "404" in content:
                raise Exception("Page not found (404)")
            elif "rate limit" in content.lower():
                raise Exception("Rate limit detected")
            else:
                raise Exception(f"Content not found: {str(e)}")
        
    except Exception as e:
        print(f"Error on page {page_number}: {str(e)}")
        if hasattr(e, 'message'):
            print(f"Error message: {e.message}")
        if hasattr(e, 'stack'):
            print(f"Stack trace: {e.stack}")
        raise e

def append_to_s3(links: List[str], bucket_name: str, file_key: str) -> None:
    s3 = boto3.client('s3')
    try:
        # Create a temporary file for this batch
        temp_file = f"/tmp/{file_key}_{os.getpid()}_{random.randint(0, 1000000)}.json"
        
        # Write the new links to the temp file
        with open(temp_file, 'w') as f:
            json.dump(links, f)
        
        # Upload the temp file to S3 with a unique key
        batch_key = f"{file_key}_batch_{os.getpid()}_{random.randint(0, 1000000)}"
        s3.upload_file(temp_file, bucket_name, batch_key)
        
        # Clean up the temp file
        os.remove(temp_file)
        
        print(f"Uploaded batch to {batch_key}")
        
    except Exception as e:
        print(f"Error uploading batch to S3: {e}")
        raise e

async def scrape_letterboxd_movie_links(start_page: int = 1):
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    file_key = "movie_links.json"
    
    async with async_playwright() as p:
        # Configure browser with more options
        browser = await p.chromium.launch(
            headless=True,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process'
            ]
        )
        
        # Set up a context with custom user agent and additional settings
        context = await browser.new_context(
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            java_script_enabled=True,
            ignore_https_errors=True
        )
        
        page = await context.new_page()
        consecutive_errors = 0
        max_consecutive_errors = 3
        current_page = start_page
        
        try:
            while consecutive_errors < max_consecutive_errors:
                try:
                    # Add delay between requests
                    await asyncio.sleep(random.uniform(5, 7))
                    
                    # Scrape the page
                    links = await scrape_page(page, current_page)
                    
                    if links:
                        # Upload to S3
                        append_to_s3(links, BUCKET_NAME, file_key)
                        consecutive_errors = 0  # Reset error count on success
                    else:
                        consecutive_errors += 1
                        print(f"No links found on page {current_page}")
                    
                    current_page += 1
                    
                except Exception as e:
                    print(f"Error processing page {current_page}: {e}")
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        print(f"Stopping due to {max_consecutive_errors} consecutive errors")
                        break
                    await asyncio.sleep(10*3**consecutive_errors)  # Longer delay after error
                    
        finally:
            await page.close()
            await context.close()
            await browser.close()

if __name__ == "__main__":
    asyncio.run(scrape_letterboxd_movie_links())
