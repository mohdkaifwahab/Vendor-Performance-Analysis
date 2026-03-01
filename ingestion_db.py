import os
import time
import logging

import pandas as pd
from sqlalchemy import create_engine


# Ensure log directory exists
os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/ingestion_db.log",
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    filemode="a",
)

engine = create_engine("sqlite:///inventory.db")


def ingest_db(df, table_name, engine):
    """Ingest a dataframe into a database table."""
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)


def load_raw_data():
    """Load CSV files as dataframes and ingest into DB."""
    start = time.time()
    dataset_dir = "dataset"

    if not os.path.isdir(dataset_dir):
        logging.error(f"Dataset directory not found: {dataset_dir}")
        print(f"Dataset directory not found: {dataset_dir}")
        return

    for file_name in os.listdir(dataset_dir):
        if not file_name.lower().endswith(".csv"):
            continue

        file_path = os.path.join(dataset_dir, file_name)

        try:
            df = pd.read_csv(file_path)
            table_name = os.path.splitext(file_name)[0]
            ingest_db(df, table_name, engine)

            logging.info(f"Ingested {file_name} into DB table '{table_name}'")
            print(f"Data {file_name} was successfully stored in DB")
        except Exception as e:
            logging.exception(f"Failed to ingest {file_name}: {e}")
            print(f"Failed to ingest {file_name}: {e}")

    total_time = (time.time() - start) / 60
    logging.info("----------------Ingestion Complete-----------------")
    logging.info(f"Total time taken by ingestion: {total_time:.2f} minutes")


# Backward compatibility for old typo'd function name
def laod_raw_data():
    load_raw_data()


# When in a company simple one notebook can't fill the requirement , and need to do scripting
# if data in the form of csv from the server and need to store it in continious form in database
# if data come in every 15 min then need to write the script for every 15 min that run automatically 


if __name__ == "__main__":
    load_raw_data()