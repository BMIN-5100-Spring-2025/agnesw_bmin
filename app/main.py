import io
import pandas as pd
import os
import time
import json
import boto3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# Environment Variables for Fargate Compatibility
S3_BUCKET_NAME = os.getenv("S3_BUCKET_NAME", "agnesw-project")
INPUT_S3_KEYS = {
    "ml_devices": "ml_devices.csv",
    "510k": "device-510k.json",
    "pma": "device-pma.json"
}
OUTPUT_S3_KEY = os.getenv("OUTPUT_S3_KEY", "data/output/aiml_info.csv")
INPUT_DIR = os.getenv("INPUT_DIR", "data/input")
OUTPUT_DIR = os.getenv("OUTPUT_DIR", "data/output")
RUN_MODE = os.getenv("RUN_MODE", "local")

# Initialize S3 client
s3 = boto3.client('s3')

def download_all_from_s3(bucket, input_keys, local_dir):
    """Download all required files from S3 to local storage"""
    os.makedirs(local_dir, exist_ok=True)
    
    for key, filename in input_keys.items():
        local_path = os.path.join(local_dir, filename)
        logger.info(f"Downloading {filename} from S3 bucket {bucket} to {local_path}")
        s3.download_file(bucket, filename, local_path)


def upload_to_s3(local_path, bucket, s3_key):
    """Upload file from local storage to S3"""
    logger.info(f"Uploading {local_path} to S3 bucket {bucket} as {s3_key}")
    s3.upload_file(local_path, bucket, s3_key)

def build_fda_index(file_path, key_field):

    index = {}

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

        if "results" in data and isinstance(data["results"], list):
            for obj in data["results"]:
                key = obj.get(key_field)
                if key:
                    index[key] = obj
        else:
            logger.error(f"Invalid JSON format in {file_path}: 'results' field missing or not a list.")

    return index

def fetch_api_data(id_number, k_file, pma_file):
    """
    Fetches FDA device data from preloaded dictionaries instead of scanning the JSON file.
    """

    global k_index, pma_index

    if "k_index" not in globals():
        print(f"Indexing {k_file} for fast search...")
        k_index = build_fda_index(k_file, "k_number")

    if "pma_index" not in globals():
        print(f"Indexing {pma_file} for fast search...")
        pma_index = build_fda_index(pma_file, "pma_number")

    data = k_index.get(id_number) if id_number.startswith("K") or id_number.startswith("DEN") else pma_index.get(id_number)

    if data:
        desired_fields = ["city", "state", "date_received", "decision_date", 
                          "decision_code", "expedited_review_flag"]

        extracted_data = {field: data.get(field, None) for field in desired_fields}
        extracted_data["device_class"] = data.get("openfda", {}).get("device_class", None)

        return extracted_data
    
    print(f"No data found for {id_number}.")
    return {field: None for field in desired_fields + ["device_class"]}

def combine_info(input_file, output_file, k_file, pma_file):
    df = clean_csv(input_file)
    df.columns = df.columns.str.strip()
    logger.info(f"CSV Columns: {df.columns}")

    if "Submission Number" not in df.columns:
        raise ValueError("Error: 'Submission Number' column not found in the CSV file.")
    
    api_data_list = []
    for index, row in df.iterrows():
        query_value = row["Submission Number"]
        start_time = time.time()
        api_data = fetch_api_data(query_value, k_file, pma_file)
        api_data_list.append(api_data if api_data else {})
        end_time = time.time()
        # logger.info(f"Execution Time for {query_value}: {end_time - start_time:.4f} seconds")
    
    api_df = pd.DataFrame(api_data_list)
    combined_df = pd.concat([df, api_df], axis=1)
    write_csv(output_file, combined_df)

def clean_csv(input_file):
    return pd.read_csv(input_file, encoding="ISO-8859-1", dtype=str)

def write_csv(output_file, df):
    df.to_csv(output_file, index=False, encoding="utf-8", mode='w')

if __name__ == "__main__":
    
    if RUN_MODE == "local":
        input_path = os.path.join("data/input", INPUT_S3_KEYS["ml_devices"])
        output_path = os.path.join(OUTPUT_DIR, "aiml_info.csv")
        k_file_path = os.path.join(INPUT_DIR, INPUT_S3_KEYS["510k"])
        pma_file_path = os.path.join(INPUT_DIR, INPUT_S3_KEYS["pma"])
        
        os.makedirs(INPUT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    else:
        input_path = INPUT_S3_KEYS["ml_devices"]
        output_path = OUTPUT_S3_KEY
        k_file_path = INPUT_S3_KEYS["510k"]
        pma_file_path = INPUT_S3_KEYS["pma"]
        
        os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    if RUN_MODE == "fargate":
        download_all_from_s3(S3_BUCKET_NAME, INPUT_S3_KEYS, INPUT_DIR)

    combine_info(input_path, output_path, k_file_path, pma_file_path)

    if RUN_MODE == "fargate":
        upload_to_s3(output_path, S3_BUCKET_NAME, OUTPUT_S3_KEY)
    
    logger.info("Processing complete!")


