import boto3
import json
import os
from typing import Set, List
from tqdm import tqdm
from dotenv import load_dotenv
import time

load_dotenv()

def list_s3_files(s3_client, bucket_name: str, prefix: str = '') -> List[str]:
    """List all files in the S3 bucket with the given prefix."""
    print(f"Listing files in bucket {bucket_name} with prefix {prefix}...")
    files = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                files.append(obj['Key'])
    
    print(f"Found {len(files)} JSON files")
    return files

def download_and_process_file(s3_client, bucket_name: str, file_key: str) -> Set[str]:
    """Download a file from S3 and extract the links."""
    try:
        # Download the file to memory
        response = s3_client.get_object(Bucket=bucket_name, Key=file_key)
        content = response['Body'].read().decode('utf-8')
        
        data = json.loads(content)
        return data
    except Exception as e:
        print(f"Error processing file {file_key}: {str(e)}")
        return set()

def combine_links(bucket_name: str, output_key: str, prefix: str = '') -> None:
    """Combine all JSON files in the bucket into a single deduplicated list."""
    s3_client = boto3.client('s3')
    files = list_s3_files(s3_client, bucket_name, prefix)
    if not files:
        raise Exception("No files found to process")
    all_links = set()
    for file_key in tqdm(files, desc="Processing files"):
        links = download_and_process_file(s3_client, bucket_name, file_key)
        all_links.update(links)
        time.sleep(0.1)
    final_links = list(all_links)
    print(f"Total unique links found: {len(final_links)}")
    try:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=output_key,
            Body=json.dumps(final_links, indent=2),
            ContentType='application/json'
        )
        print(f"Successfully uploaded combined links to {output_key}")
    except Exception as e:
        print(f"Error uploading combined links: {str(e)}")

if __name__ == "__main__":
    BUCKET_NAME = os.getenv("BUCKET_NAME")
    OUTPUT_KEY = "combined_links.json"
    if not BUCKET_NAME:
        raise ValueError("BUCKET_NAME environment variable is not set")
    combine_links(BUCKET_NAME, OUTPUT_KEY)
