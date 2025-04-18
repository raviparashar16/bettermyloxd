import requests
from bs4 import BeautifulSoup
import re
def get_movie_description(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; Bot/0.1)",
    }
    if not url.endswith('/'):
        url += '/'
    reviews_url = url + 'reviews/by/activity/'
    responses = []
    for url in [url, reviews_url]:
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch page: {response.status_code}")
            return None
        responses.append(response)
    texts = []
    desc_response, rev_response = responses[0], responses[1]
    soup = BeautifulSoup(desc_response.text, "html.parser")
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc and "content" in meta_desc.attrs:
        raw_desc = meta_desc["content"]
        cleaned_desc = re.sub(r"[\u200e\u200f\u202a-\u202e]", "", raw_desc).strip()
        texts.append(cleaned_desc)
    else:
        raise Exception("")
    
    soup = BeautifulSoup(rev_response.text, "html.parser")
    review_items = soup.select("section.viewings-list li")
    reviews = []
    for li in review_items:
        review_text_div = li.select_one("div.body-text")
        if review_text_div:
            review_text = review_text_div.get_text(strip=True, separator=" ")
            if review_text:
                reviews.append(review_text)
        if len(reviews) >= 9:
            break
    if not reviews:
        raise Exception("")
    texts.extend(reviews)
    return texts

# TODO: add check for description being in english - if not, skip and in loop of reviews,
# get top 9 english reviews and if not found, skip movie
# TODO: add retry logic and better logging
# TODO: add concurrency but without hitting rate limits
# TODO: add upload to s3/db(?)