import sqlite3
import pandas as pd

def sqlite_to_csv_pandas(database_file, table_name, output_csv_file):
    conn = sqlite3.connect(database_file)

    # Read the SQL query result directly into a pandas DataFrame
    df = pd.read_sql_query(f'SELECT * FROM {table_name}', conn)
    
    # Write the DataFrame to a CSV file
    # index=False prevents pandas from writing the DataFrame index as a column
    df.to_csv(output_csv_file, index=False)

    conn.close()
    print(f"Data from table '{table_name}' successfully exported to '{output_csv_file}' using pandas")



if __name__ == "__main__":
    sqlite_to_csv_pandas('inventory.db', 'vendor_sales_summary', 'vendor_sales_summary.csv')
