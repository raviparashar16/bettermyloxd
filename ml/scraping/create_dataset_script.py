import boto3
import json
import os
from tqdm import tqdm
from dotenv import load_dotenv
import time
import math
import random

load_dotenv()

def create_dataset(bucket_name: str, output_key: str) -> None:
    """Create dataset from movie texts"""
    s3_client = boto3.client('s3')
    response = s3_client.get_object(Bucket=BUCKET_NAME, Key="movie_texts.json")
    content = response['Body'].read().decode('utf-8')
    data = json.loads(content)
    print(f"Total unique records found: {len(data)}")
    num_shards = math.ceil(len(data) / 10_000)
    for i in tqdm(range(num_shards), desc="Shard processing progress", position=0):
        shard_data = list(data.keys())[i * 10_000:(i + 1) * 10_000]
        shard_records = []
        for movie_id in tqdm(shard_data, desc="Movie processing progress", position=1, leave=False):
            for j in range(10):
                query_text = data[movie_id][j]
                assoc_text = random.choice([txt for k, txt in enumerate(data[movie_id]) if k != j])
                assoc_text_loc = random.randint(0, 9)
                non_assoc_texts = []
                for _ in range(9):
                    rand_non_assoc_movie_id = random.choice(list(filter(lambda x: x != movie_id, list(data.keys()))))
                    non_assoc_texts.append(random.choice(data[rand_non_assoc_movie_id]))
                label = []
                texts = []
                non_assoc_ind = 0
                for k in range(10):
                    if k == assoc_text_loc:
                        texts.append(assoc_text)
                        label.append(1)
                    else:
                        texts.append(non_assoc_texts[non_assoc_ind])
                        label.append(0)
                        non_assoc_ind += 1
                shard_records.append({
                    "movie_id": movie_id,
                    "query_text": query_text,
                    "texts": texts,
                    "label": label
                })
        # convert shard data into jsonl
        jsonl_str = "\n".join(json.dumps(record) for record in shard_records)
        shard_key = f"{output_key}_shard{i}.jsonl"
        s3_client.put_object(Bucket=bucket_name, Key=shard_key, Body=jsonl_str)

if __name__ == "__main__":
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    OUTPUT_KEY = "dataset/movie_dataset"
    if not BUCKET_NAME:
        raise ValueError("BUCKET_NAME environment variable is not set")
    create_dataset(BUCKET_NAME, OUTPUT_KEY)
