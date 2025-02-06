import io
import pandas as pd
import os
import time
import ijson

def build_fda_index(file_path, key_field):

    index = {}

    with open(file_path, "r", encoding="utf-8") as file:
        objects = ijson.items(file, "results.item")
        
        for obj in objects:
            key = obj.get(key_field) 
            if key:
                index[key] = obj

    return index

def fetch_api_data(id_number, k_file="data/input/device-510k.json", pma_file="data/input/device-pma.json"):
    """
    Fetches FDA device data from preloaded dictionaries instead of scanning the JSON file.
    """

    global k_index, pma_index  

    if "k_index" not in globals():
        print("Indexing 510k JSON for fast search...")
        k_index = build_fda_index(k_file, "k_number")

    if "pma_index" not in globals():
        print("Indexing PMA JSON for fast search...")
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


def combine_info(input_directory, output_directory):
    
    df = clean_csv(input_directory)
    df.columns = df.columns.str.strip()
    print(df.columns)

    if "Submission Number" not in df.columns:
        raise ValueError("Error: 'Submission Number' column not found in the CSV file.")
    
    api_data_list = []
    for index, row in df.iterrows():
        query_value = row["Submission Number"]
        start_time = time.time()
        api_data = fetch_api_data(query_value)
        api_data_list.append(api_data if api_data else {})
        end_time = time.time()
        print(f"Execution Time: {end_time - start_time:.4f} seconds")

    api_df = pd.DataFrame(api_data_list)
    combined_df = pd.concat([df, api_df], axis=1)

    output_filename = 'aiml_info.csv'
    output_file = os.path.join(output_directory, output_filename)
    write_csv(output_file, combined_df)

def clean_csv(input_directory):
    with open(input_directory, "rb") as f:
        content = f.read().decode("ISO-8859-1", errors="replace")
        cleaned_file = input_directory.replace(".csv", "_cleaned.csv")
    df = pd.read_csv(io.StringIO(content), encoding="utf-8")
    return df

def write_csv(output_file, df):
    df.to_csv(output_file, index=False, mode='w')

if __name__ == "__main__":

    base_directory = os.path.dirname(os.path.dirname(__file__))
    input_directory = os.getenv('INPUT_DIR', os.path.join(base_directory, 'data', 'input', 'ml_devices.csv'))
    output_directory = os.getenv('OUTPUT_DIR', os.path.join(base_directory, 'data', 'output'))

    combine_info(input_directory, output_directory)
