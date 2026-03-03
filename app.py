import streamlit as st
import pandas as pd
import plotly.express as px
import numpy as np
import matplotlib.pyplot as plt

# page config
st.set_page_config(
    page_icon='📈',
    page_title='Vendor Sales Dashboard',
    layout='wide'
)

st.title('📈 Vendor Sales Dashboard')

# -------------------------
# LOAD DATA (with notebook filter condition)
# -------------------------
@st.cache_data
def load_data():
    df = pd.read_csv('vendor_sales_summary.csv')
    df = df[
        (df['GrossProfit'] > 0) & 
        (df['ProfitMargin'] > 0) & 
        (df['TotalSalesQuantity'] > 0)
    ]
    return df

df = load_data()

# -------------------------
# FORMAT FUNCTION (UNCHANGED)
# -------------------------
def format_dollars(value):
    if value >= 1_000_000:
        return f"{value/1_000_000:.2f}M"
    elif value >= 1_000:
        return f"{value/1_000:.2f}K"
    return str(round(value,2))


def kpi_card(title, value, color="#C2185B"):
    return f"""
    <div style="padding:15px; border-radius:10px; background-color:#1E1E1E;">
        <h4 style="color:white; margin-bottom:5px;">{title}</h4>
        <h2 style="color:{color};">{value}</h2>
    </div>
    """

# -------------------------
# KPI SECTION (UNCHANGED STYLE)
# -------------------------
total_sales = format_dollars(df['TotalSalesDollars'].sum())
total_purchases = format_dollars(df['TotalPurchaseDollars'].sum())
gross_profit = format_dollars(df['GrossProfit'].sum())

unsold_capital = format_dollars(
    ((df['TotalPurchaseQuantity'] - df['TotalSalesQuantity']) 
     * df['PurchasePrice']).sum()
)

st.subheader("📊 Key Performance Indicators")

col1, col2, col3, col4 = st.columns(4)

col1.markdown(kpi_card("Total Sales", total_sales, "#4CAF50"), unsafe_allow_html=True)
col2.markdown(kpi_card("Total Purchases", total_purchases, "#4CAF50"), unsafe_allow_html=True)
col3.markdown(kpi_card("Gross Profit", gross_profit, "#4CAF50"), unsafe_allow_html=True)
col4.markdown(kpi_card("Unsold Capital", unsold_capital), unsafe_allow_html=True)

st.markdown("---")

# -------------------------
# ROW 1
# -------------------------
col6, col7, col8 = st.columns([1.2,1,1])

# Purchase Contribution
purchase_contribution = (
    df.groupby("VendorName")["TotalPurchaseDollars"]
    .sum()
    .reset_index()
)

# """ main data start from here """
# venod performance
vendor_performance = df.groupby('VendorName').agg({
    'TotalPurchaseDollars' : 'sum',
    'GrossProfit':'sum',
    'TotalSalesDollars':'sum'
}).reset_index()

# ''' filter vendor_performance'''
vendor_performance['PurchaseContribution%'] = vendor_performance['TotalPurchaseDollars']/ vendor_performance['TotalPurchaseDollars'].sum()*100
vendor_performance = round(vendor_performance.sort_values('PurchaseContribution%',ascending=False),2)





### Conut chart
# ''' top vendros'''
top_vendors = vendor_performance.head(10)
top_vendors['TotalPurchaseDollars'] = top_vendors['TotalPurchaseDollars'].apply(format_dollars)
top_vendors['GrossProfit'] = top_vendors['GrossProfit'].apply(format_dollars)
top_vendors['TotalSalesDollars'] = top_vendors['TotalSalesDollars'].apply(format_dollars)


# data for donut chart
vendors = list(top_vendors['VendorName'].values)
purchase_contribution = list(top_vendors['PurchaseContribution%'].values)
total_contribution = sum(purchase_contribution)
remaning_contribution = 100 - total_contribution

# Append the others 
vendors.append('Other Vendors')
purchase_contribution.append(remaning_contribution)

# Donut chart
fig_donut = px.pie(
    values=purchase_contribution,
    names=vendors,
    hole=0.6,
    title="Top 10 Vendor's Purchase Contribution (%)"
)
col6.plotly_chart(fig_donut, use_container_width=True)






# Horizontal Bar
top_vendors = df.groupby('VendorName')['TotalSalesDollars'].sum().nlargest(10).sort_values()
top_brands = df.groupby('Description')['TotalSalesDollars'].sum().nlargest(10).sort_values()

fig_bar = px.bar(
    x=top_vendors.values,
    y=top_vendors.index,
    orientation="h",
    title="Top 10 Vendors Sales ",
)
col7.plotly_chart(fig_bar, use_container_width=True)

fig_sales = px.bar(
    x=top_brands.values,
    y=top_brands.index,
    orientation="h",
    title="Top 10 Brands Sales",
)
col8.plotly_chart(fig_sales, use_container_width=True)

st.markdown("---")





# -------------------------
# ROW 2
# -------------------------
col9, col10 = st.columns([1,2])


# top vendors average turn over 
low_turnover = df[df['StockTurnover']<1]
top_ten_turnover = low_turnover.groupby('VendorName').agg({
    'StockTurnover':'mean'
}).reset_index().sort_values(by='StockTurnover').head(5)


fig_top5 = px.bar(
    top_ten_turnover,
    x='StockTurnover',
    y='VendorName',
    orientation="h",
    title="Top 5 Vendors"
)
col9.plotly_chart(fig_top5, use_container_width=True)

# -------------------------
# LOW PERFORMING BRANDS (WITH TURNOVER FILTER)
# -------------------------

brand_perf = df.groupby("Description").agg({
    "TotalSalesDollars": "sum",
    "ProfitMargin": "mean"
}).reset_index()

# 🔹 Add TurnOver column (if TurnOver = TotalSalesDollars)
brand_perf["TurnOver"] = brand_perf["TotalSalesDollars"]

# 🔹 Apply TurnOver filter < 10000
brand_perf = brand_perf[brand_perf["TurnOver"] < 10000]

# Percentile thresholds
low_sales_threshold = brand_perf["TotalSalesDollars"].quantile(0.15)
high_margin_threshold = brand_perf["ProfitMargin"].quantile(0.85)

# Target identification
brand_perf["TargetFlag"] = np.where(
    (brand_perf["TotalSalesDollars"] <= low_sales_threshold) &
    (brand_perf["ProfitMargin"] >= high_margin_threshold),
    "Target Brand",
    "Other Brands"
)

# Plot Scatter
fig_scatter = px.scatter(
    brand_perf,
    x="TotalSalesDollars",
    y="ProfitMargin",
    color="TargetFlag",
    color_discrete_map={
        "Other Brands": "blue",
        "Target Brand": "red"
    },
    opacity=0.6,
    title="Brands for Promotional or Pricing Adjustment"
)

# Add Threshold Lines
fig_scatter.add_vline(
    x=low_sales_threshold,
    line_dash="dash",
    line_color="black"
)

fig_scatter.add_hline(
    y=high_margin_threshold,
    line_dash="dash",
    line_color="black"
)

fig_scatter.update_layout(
    xaxis_title="Total Sales ($)",
    yaxis_title="Profit Margin",
    legend_title="Brand Type"
)

# 🔹 IMPORTANT: Add unique key
col10.plotly_chart(fig_scatter, width="stretch", key="low_perf_scatter")

st.markdown("---")

if st.checkbox(label='Show Data'):
    st.subheader("📄 Detailed Data")
    st.dataframe(df)