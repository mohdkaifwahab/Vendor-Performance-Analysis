import pandas as pd
import sqlite3
import logging
import os
import ingestion_db as ingestion_db



os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename='logs/get_vendor_summary.log',
    format='%(asctime)s - %(levelname)s - %(message)s',  # fixed
    level=logging.DEBUG,
    filemode='a',
    force=True
)


def create_vendor_summary(conn):
    vendor_sales_summary = pd.read_sql_query("""
    WITH FreightSummary     AS (
        SELECT
            VendorNumber,
            SUM(Freight) AS FreightCost
        FROM vendor_invoice
        GROUP BY VendorNumber
    ),
    PurchaseSummary AS (
        SELECT
            p.VendorNumber,
            p.VendorName,
            p.Brand,
            p.PurchasePrice,
            p.Description,
            pp.Volume,
            pp.Price AS ActualPrice,
            SUM(p.Quantity) AS TotalPurchaseQuantity,
            SUM(p.Dollars) AS TotalPurchaseDollars
        FROM purchases p
        JOIN purchase_prices pp
            ON p.Brand = pp.Brand
        AND p.VendorNumber = pp.VendorNumber
        WHERE p.PurchasePrice > 0
        GROUP BY
            p.VendorNumber, p.VendorName, p.Brand, p.PurchasePrice,
            p.Description, pp.Volume, pp.Price
    ),
    SalesSummary AS (
        SELECT
            VendorNo AS VendorNumber,
            Brand,
            SUM(SalesDollars) AS TotalSalesDollars,
            SUM(SalesPrice) AS TotalSalesPrice,
            SUM(SalesQuantity) AS TotalSalesQuantity,
            SUM(ExciseTax) AS TotalExciseTax
        FROM sales
        GROUP BY VendorNo, Brand
    )
    SELECT
        ps.*,
        fs.FreightCost,
        ss.TotalSalesDollars,
        ss.TotalSalesPrice,
        ss.TotalSalesQuantity,
        ss.TotalExciseTax
    FROM PurchaseSummary ps
    LEFT JOIN FreightSummary fs
        ON ps.VendorNumber = fs.VendorNumber
    LEFT JOIN SalesSummary ss
        ON ps.VendorNumber = ss.VendorNumber
        AND ps.Brand = ss.Brand                   
    ORDER BY ps.TotalPurchaseDollars DESC   """, conn)

    return vendor_sales_summary


def clean_data(df):

    """ This Function clean the data """
    # Chaning datatype into float64
    df['Volume'] = df['Volume'].astype('float64')

    # Remove irrelavant white  spacing in name
    df['VendorName'] = df['VendorName'].str.strip()
    df['Description'] = df['Description'].str.strip()

    # fill null value with 0 
    df.fillna(0,inplace=True)

    # Creating the new called using feature engineering
    df['GrossProfit'] = df['TotalSalesDollars'] - df['TotalPurchaseDollars']
    df['ProfitMargin'] = (df['GrossProfit'] / df['TotalSalesDollars']) *100
    df['StockTurnover'] = df['TotalSalesQuantity'] / df['TotalPurchaseQuantity']
    df['SalestoPurchaseRatio'] = df['TotalSalesDollars'] / df['TotalPurchaseDollars']

    return df



if __name__ == '__main__':
     
    # create connection 
    conn = sqlite3.connect('inventory.db')

    logging.info('Creating Vendor Summary Table....')
    summary_df = create_vendor_summary(conn)
    logging.info(summary_df.head())

    logging.info('Cleaing the data....')
    clean_df = clean_data(summary_df)
    logging.info(clean_df.head())

    logging.info('Ingestion into db....')
    ingestion_db.ingest_db(clean_df,'vendor_sales_summary',conn)
    logging.info('Completed👊')

