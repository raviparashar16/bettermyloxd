import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
import time
import json
import boto3
import os
from dotenv import load_dotenv
from typing import Dict, List
from langdetect import detect, LangDetectException

load_dotenv()

class RateLimiter:
    def __init__(self, calls_per_second: float = 2.0):
        self.calls_per_second = calls_per_second
        self.last_call = 0
        self.lock = asyncio.Lock()

    async def __aenter__(self):
        async with self.lock:
            now = time.time()
            time_since_last_call = now - self.last_call
            if time_since_last_call < 1 / self.calls_per_second:
                await asyncio.sleep(1 / self.calls_per_second - time_since_last_call)
            self.last_call = time.time()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

async def get_movie_texts(session: aiohttp.ClientSession, url: str, rate_limiter: RateLimiter) -> List[str]:
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1)",
    }
    if not url.endswith('/'):
        url += '/'
    texts = []
    num_consecutive_failures = 0
    
    while num_consecutive_failures < 3:
        async with rate_limiter:
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        print(f"Failed to fetch page: {response.status}")
                        num_consecutive_failures += 1
                        await asyncio.sleep(10 * num_consecutive_failures)
                        continue
                    
                    html = await response.text()
                    soup = BeautifulSoup(html, "html.parser")
                    meta_desc = soup.find("meta", attrs={"name": "description"})
                    
                    if meta_desc and "content" in meta_desc.attrs:
                        raw_desc = meta_desc["content"]
                        cleaned_desc = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", raw_desc).strip()
                        if not cleaned_desc:
                            return None
                        
                        try:
                            lang = detect(cleaned_desc)
                            if lang != 'en':
                                return None
                        except LangDetectException:
                            pass
                        
                        texts.append(cleaned_desc)
                        break
                    else:
                        return None
                        
            except Exception as e:
                print(f"Error fetching {url}: {e}")
                num_consecutive_failures += 1
                await asyncio.sleep(10 * num_consecutive_failures)
                continue
    else:
        print(f"Description not found for {url}")
        return None

    page_number = 1
    reviews = []
    max_review_pages = 9
    while len(reviews) < 9 and page_number <= max_review_pages:
        num_consecutive_failures = 0
        reviews_url = url + f'reviews/by/activity/page/{page_number}/'
        
        while num_consecutive_failures < 3:
            async with rate_limiter:
                try:
                    async with session.get(reviews_url, headers=headers) as response:
                        if response.status != 200:
                            print(f"Failed to fetch reviews page: {response.status}")
                            num_consecutive_failures += 1
                            await asyncio.sleep(10 * num_consecutive_failures)
                            continue
                        
                        html = await response.text()
                        soup = BeautifulSoup(html, "html.parser")
                        review_items = soup.select("section.viewings-list li")
                        
                        for li in review_items:
                            review_text_div = li.select_one("div.body-text")
                            if review_text_div:
                                review_text = review_text_div.get_text(strip=True, separator=" ")
                                if review_text:
                                    try:
                                        if detect(review_text) == 'en':
                                            reviews.append(review_text)
                                    except LangDetectException:
                                        reviews.append(review_text)
                            if len(reviews) >= 9:
                                break
                                
                except Exception as e:
                    print(f"Error fetching reviews: {e}")
                    num_consecutive_failures += 1
                    await asyncio.sleep(10 * num_consecutive_failures)
                    continue
        else:
            print(f"Failed to fetch reviews for {url}")
            return None
            
        page_number += 1
    if len(reviews) < 9:
        return None
    texts.extend(reviews)
    return texts

async def process_batch(session: aiohttp.ClientSession, urls: List[str], rate_limiter: RateLimiter) -> Dict[str, List[str]]:
    tasks = []
    for url in urls:
        task = asyncio.create_task(get_movie_texts(session, url, rate_limiter))
        tasks.append((url, task))
    
    movie_texts = {}
    for url, task in tasks:
        try:
            texts = await task
            if texts:
                movie_texts[url] = texts
        except Exception as e:
            print(f"Error processing {url}: {e}")
    
    return movie_texts

async def append_to_s3_batch(s3_client, movie_texts: Dict[str, List[str]], bucket_name: str, batch_number: int, worker_id: int) -> None:
    try:
        # Create a temporary file for this batch
        temp_file = f"/tmp/movie_texts_batch_{worker_id}_{batch_number}.json"
        
        # Write the new texts to the temp file
        with open(temp_file, 'w') as f:
            json.dump(movie_texts, f)
        
        # Upload the temp file to S3
        batch_key = f"movie_texts/worker_{worker_id}/movie_texts_batch_{batch_number}.json"
        s3_client.upload_file(temp_file, bucket_name, batch_key)
        
        # Clean up the temp file
        os.remove(temp_file)
        print(f"Uploaded batch {batch_number} with {len(movie_texts)} movies")
        
    except Exception as e:
        print(f"Error uploading batch {batch_number} to S3: {e}")

async def main(worker_id: int, total_workers: int):
    s3_client = boto3.client('s3')
    bucket_name = os.getenv("BUCKET_NAME")
    file_key = "combined_links.json"
    
    # Download the combined links file
    response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
    content = response['Body'].read().decode('utf-8')
    movie_links = json.loads(content)
    
    # Split work among workers
    total_links = len(movie_links)
    links_per_worker = total_links // total_workers
    start_idx = worker_id * links_per_worker
    end_idx = start_idx + links_per_worker if worker_id < total_workers - 1 else total_links
    worker_links = movie_links[start_idx:end_idx]
    
    print(f"Worker {worker_id}: Processing {len(worker_links)} URLs (indices {start_idx}-{end_idx})")
    
    # Configure rate limiter (2 requests per second)
    rate_limiter = RateLimiter(calls_per_second=2.0)
    
    # Configure aiohttp session
    async with aiohttp.ClientSession() as session:
        batch_size = 100
        total_batches = (len(worker_links) + batch_size - 1) // batch_size
        
        for batch_num in range(total_batches):
            start_idx = batch_num * batch_size
            end_idx = min((batch_num + 1) * batch_size, len(worker_links))
            batch_urls = worker_links[start_idx:end_idx]
            
            print(f"Worker {worker_id}: Processing batch {batch_num + 1}/{total_batches} ({len(batch_urls)} URLs)")
            movie_texts = await process_batch(session, batch_urls, rate_limiter)
            
            if movie_texts:
                await append_to_s3_batch(s3_client, movie_texts, bucket_name, batch_num + 1, worker_id)
            
            # Add a small delay between batches
            await asyncio.sleep(2)

if __name__ == "__main__":
    worker_id = os.getenv("WORKER_ID")
    total_workers = os.getenv("TOTAL_WORKERS")
    asyncio.run(main(worker_id, total_workers))
