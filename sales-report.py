import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import json
import requests
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Retail Sales Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ffffff;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.1);
    }
    .chart-title {
        font-size: 1.2rem;
        font-weight: 600;
        color: #ffffff;
        margin-bottom: 0.5rem;
    }
    .section-divider {
        margin-top: 2rem;
        margin-bottom: 2rem;
        border-top: 1px solid #e0e0e0;
    }
    /* Make pie charts bigger */
    .big-chart {
        min-height: 500px !important;
    }
</style>
""", unsafe_allow_html=True)

# Function to load data
@st.cache_data(ttl=300)  # Cache data for 5 minutes
def load_data(api_url="https://bookish-winner-seven.vercel.app/api/dashboard"):
    """Load data from the API or use the provided JSON as a fallback"""
    try:
        # First try to get data from API
        response = requests.get(api_url, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
        else:
            st.warning(f"API returned status code {response.status_code}. Using fallback data.")
    except Exception as e:
        st.warning(f"Could not fetch data from API: {e}. Using fallback data.")
        
    
    # Convert to DataFrame
    df = pd.DataFrame(json_data['data'])
    
    # Extract month and year from the date field
    if 'month' in df.columns:
        # Convert month to datetime
        df['date'] = pd.to_datetime(df['month'])
    else:
        st.warning("No 'month' field found in data. Please check API structure.")
        # Create a dummy date field to avoid errors
        df['date'] = pd.to_datetime('2025-01-01')
    
    # Add month name and year columns
    df['month_name'] = df['date'].dt.strftime('%b')
    df['year'] = df['date'].dt.year
    df['month_year'] = df['date'].dt.strftime('%b %Y')
    
    # Clean store names
    df['store_name'] = df['store_name'].str.strip()
    
    # Create product category column
    def categorize_product(name):
        if not isinstance(name, str):
            return 'Unknown'
        
        if 'Kimono' in name:
            return 'Kimono Jacket'
        elif 'Gilet' in name:
            return 'Gilet Jacket'
        elif 'TP Jacket' in name or 'Trucker Jacket' in name:
            return 'TP/Trucker Jacket'
        elif 'Tote' in name:
            return 'Tote Bag'
        elif 'Hat' in name:
            return 'Campaign Hats'
        elif 'Shorts' in name:
            return 'Shorts'
        elif 'Jeans' in name:
            return 'Jeans'
        elif 'Skirt' in name:
            return 'Skirt'
        elif 'Bottle' in name:
            return 'Bottle Sling'
        elif 'DRESS' in name:
            return 'Dress'
        else:
            return 'Other'
    
    df['product_category'] = df['item_name'].apply(categorize_product)
    
    return df

# Sidebar configuration
st.sidebar.markdown("## Dashboard Controls")
st.sidebar.markdown("---")



# Main dashboard header
st.markdown('<div class="main-header">📊 Retail Sales Analytics</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Interactive Performance Dashboard</div>', unsafe_allow_html=True)

# Load the data
with st.spinner("Fetching latest sales data..."):
    df = load_data()

# Check if data is loaded successfully
if df.empty:
    st.error("No data available. Please check the data source.")
    st.stop()


st.sidebar.markdown("### Data Filters")

# Year filter
years = sorted(df['year'].unique(), reverse=True)
selected_year = st.sidebar.selectbox(
    "Select Year",
    options=years,
    index=0
)

# Month filter
months = ['All Months', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
selected_month = st.sidebar.selectbox(
    "Select Month",
    options=months,
    index=0
)

# Store filter
all_stores = sorted(df['store_name'].unique())
all_stores_option = ["All Stores"] + all_stores
selected_store = st.sidebar.selectbox(
    "Select Store",
    options=all_stores_option,
    index=0
)

# Product category filter
all_categories = ["All Categories"] + sorted(df['product_category'].unique())
selected_category = st.sidebar.selectbox(
    "Select Product Category",
    options=all_categories,
    index=0
)

# Apply filters
filtered_df = df.copy()

# Apply year filter
filtered_df = filtered_df[filtered_df['year'] == selected_year]

# Apply month filter
if selected_month != "All Months":
    filtered_df = filtered_df[filtered_df['month_name'] == selected_month]

# Apply store filter
if selected_store != "All Stores":
    filtered_df = filtered_df[filtered_df['store_name'] == selected_store]

# Apply category filter
if selected_category != "All Categories":
    filtered_df = filtered_df[filtered_df['product_category'] == selected_category]



# Display metrics at the top for all views
st.markdown("### Key Performance Metrics")

metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)

# Calculate KPIs - focusing more on quantity than revenue
total_items_sold = filtered_df['total_quantity'].sum()
avg_item_price = filtered_df['average_price'].mean()
total_sales = filtered_df['total_value'].sum()

# Previous period comparison (if data allows)
previous_period_df = None
if selected_month != "All Months":
    # Compare to previous month in same year
    month_idx = months.index(selected_month)
    if month_idx > 1:  # Not January
        prev_month = months[month_idx-1]
        previous_period_df = df[(df['year'] == selected_year) & (df['month_name'] == prev_month)]
    else:  # January - compare with December of previous year
        if selected_year > min(years):
            prev_month = 'Dec'
            prev_year = selected_year - 1
            previous_period_df = df[(df['year'] == prev_year) & (df['month_name'] == prev_month)]
else:
    # Compare to previous year
    if selected_year > min(years):
        prev_year = selected_year - 1
        previous_period_df = df[df['year'] == prev_year]

# Calculate change if previous period data exists
if previous_period_df is not None and not previous_period_df.empty:
    prev_total_items = previous_period_df['total_quantity'].sum()
    prev_total_sales = previous_period_df['total_value'].sum()
    prev_avg_price = previous_period_df['average_price'].mean()
    
    items_change = ((total_items_sold - prev_total_items) / prev_total_items * 100) if prev_total_items > 0 else 0
    sales_change = ((total_sales - prev_total_sales) / prev_total_sales * 100) if prev_total_sales > 0 else 0
    price_change = ((avg_item_price - prev_avg_price) / prev_avg_price * 100) if prev_avg_price > 0 else 0
    
    # Prioritizing quantity metrics
    metric_col1.metric(
        "Items Sold", 
        f"{total_items_sold}", 
        f"{items_change:+.1f}%" if items_change else "N/A"
    )
    
    metric_col2.metric(
        "Avg. Price", 
        f"₹{avg_item_price:,.2f}", 
        f"{price_change:+.1f}%" if price_change else "N/A"
    )
    metric_col3.metric(
        "Total Sales", 
        f"₹{total_sales:,.2f}", 
        f"{sales_change:+.1f}%" if sales_change else "N/A"
    )
else:
    # Prioritizing quantity metrics
    metric_col1.metric("Items Sold", f"{total_items_sold}")
    metric_col2.metric("Avg. Price", f"₹{avg_item_price:,.2f}")
    metric_col3.metric("Total Sales", f"₹{total_sales:,.2f}")

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

# Create tabs for different views - using tabs as in main.py
tab1, tab2, tab3, tab4 = st.tabs(["Sales Overview", "Store Performance", "Product Analytics", "Time Trends"])

with tab1:
    st.markdown('<div class="sub-header">Sales Overview</div>', unsafe_allow_html=True)
    
    # Sales by Store and Product Category - focus on quantity
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="chart-title">Quantity Distribution by Store</div>', unsafe_allow_html=True)
        quantity_by_store = filtered_df.groupby('store_name')['total_quantity'].sum().reset_index()
        quantity_by_store = quantity_by_store.sort_values('total_quantity', ascending=False)
        
        fig_store_pie = px.pie(
            quantity_by_store,
            values='total_quantity',
            names='store_name',
            color_discrete_sequence=px.colors.qualitative.Bold,
            title="Percentage of Items Sold by Store",
            hole=0.4,
            height=500  # Make pie chart bigger
        )
        fig_store_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_store_pie, use_container_width=True, className="big-chart")
    
    with col2:
        st.markdown('<div class="chart-title">Top Selling Product Categories</div>', unsafe_allow_html=True)
        quantity_by_category = filtered_df.groupby('product_category')['total_quantity'].sum().reset_index()
        quantity_by_category = quantity_by_category.sort_values('total_quantity', ascending=False)
        
        fig_category = px.bar(
            quantity_by_category,
            x='product_category',
            y='total_quantity',
            color='product_category',
            color_discrete_sequence=px.colors.qualitative.Vivid,
            labels={'product_category': 'Product Category', 'total_quantity': 'Quantity Sold'},
            title="Items Sold by Product Category",
            text_auto=True
        )
        fig_category.update_layout(xaxis_tickangle=-45, showlegend=False)
        st.plotly_chart(fig_category, use_container_width=True)
    
    # Monthly Quantity Trend
    st.markdown('<div class="chart-title">Monthly Quantity Trend</div>', unsafe_allow_html=True)
    monthly_quantity = filtered_df.groupby('month_year')['total_quantity'].sum().reset_index()
    # Create datetime for proper sorting without using month_num
    monthly_quantity['sort_date'] = pd.to_datetime(monthly_quantity['month_year'], format='%b %Y')
    monthly_quantity = monthly_quantity.sort_values('sort_date')
    
    fig_trend = px.line(
        monthly_quantity, 
        x='month_year', 
        y='total_quantity',
        markers=True,
        labels={'month_year': 'Month-Year', 'total_quantity': 'Quantity Sold'},
        color_discrete_sequence=['#1E88E5'],
        title="Monthly Quantity Sold"
    )
    fig_trend.update_layout(
        xaxis_title="Month",
        yaxis_title="Quantity",
        hovermode="x unified"
    )
    st.plotly_chart(fig_trend, use_container_width=True)
    
    # Top 10 Products by quantity
    st.markdown('<div class="chart-title">Top 10 Products by Quantity Sold</div>', unsafe_allow_html=True)
    top_products = filtered_df.groupby('item_name')['total_quantity'].sum().reset_index()
    top_products = top_products.sort_values('total_quantity', ascending=False).head(10)
    
    fig_top_products = px.bar(
        top_products,
        x='total_quantity',
        y='item_name',
        orientation='h',
        color='total_quantity',
        color_continuous_scale='Blues',
        labels={'item_name': 'Product', 'total_quantity': 'Quantity Sold'},
        text_auto=True
    )
    fig_top_products.update_layout(
        yaxis={'categoryorder': 'total ascending'},
        coloraxis_showscale=False
    )
    st.plotly_chart(fig_top_products, use_container_width=True)

with tab2:
    st.markdown('<div class="sub-header">Store Performance Analysis</div>', unsafe_allow_html=True)
    
    # Store performance metrics in 3 columns
    store_col1, store_col2, store_col3 = st.columns(3)
    
    # For selected store (or all stores)
    if selected_store != "All Stores":
        store_data = filtered_df[filtered_df['store_name'] == selected_store]
        store_title = f"Store: {selected_store}"
    else:
        store_data = filtered_df
        store_title = "All Stores"
    
    # Store overview metrics - focus on quantity
    store_col1.markdown(f"#### {store_title}")
    store_col1.metric("Total Items Sold", f"{store_data['total_quantity'].sum()}")
    store_col1.metric("Total Sales", f"₹{store_data['total_value'].sum():,.2f}")
    
    # Store products metrics
    store_col2.markdown("#### Product Mix")
    store_col2.metric("Unique Products", f"{store_data['item_name'].nunique()}")
    store_col2.metric("Categories", f"{store_data['product_category'].nunique()}")
    
    # Store price metrics
    store_col3.markdown("#### Pricing")
    store_col3.metric("Average Price", f"₹{store_data['average_price'].mean():,.2f}")
    store_col3.metric("Highest Quantity Item", f"{store_data.groupby('item_name')['total_quantity'].sum().idxmax() if not store_data.empty else 'N/A'}")
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Monthly quantity trend by store
    st.markdown('<div class="chart-title">Store Performance Over Time (Quantity)</div>', unsafe_allow_html=True)
    
    if selected_store == "All Stores":
        # Show multiple stores
        store_monthly = filtered_df.groupby(['month_year', 'store_name'])['total_quantity'].sum().reset_index()
        store_monthly['sort_date'] = pd.to_datetime(store_monthly['month_year'], format='%b %Y')
        store_monthly = store_monthly.sort_values('sort_date')
        
        fig_store_trend = px.line(
            store_monthly,
            x='month_year',
            y='total_quantity',
            color='store_name',
            markers=True,
            title="Monthly Quantity Sold by Store",
            labels={
                'month_year': 'Month-Year',
                'total_quantity': 'Quantity Sold',
                'store_name': 'Store'
            }
        )
        st.plotly_chart(fig_store_trend, use_container_width=True)
    else:
        # Show single store with additional detail
        store_monthly = filtered_df[filtered_df['store_name'] == selected_store].groupby(['month_year'])['total_quantity'].sum().reset_index()
        store_monthly['sort_date'] = pd.to_datetime(store_monthly['month_year'], format='%b %Y')
        store_monthly = store_monthly.sort_values('sort_date')
        
        fig_store_trend = px.bar(
            store_monthly,
            x='month_year',
            y='total_quantity',
            title=f"Monthly Quantity Sold: {selected_store}",
            labels={
                'month_year': 'Month-Year',
                'total_quantity': 'Quantity Sold'
            },
            color_discrete_sequence=['#1E88E5']
        )
        fig_store_trend.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_store_trend, use_container_width=True)
    
    # Store product category distribution
    st.markdown('<div class="chart-title">Product Category Distribution by Store (Quantity)</div>', unsafe_allow_html=True)
    store_category_col1, store_category_col2 = st.columns(2)
    
    with store_category_col1:
        # Pie chart of quantity by store and category
        if selected_store == "All Stores":
            store_category_pie = filtered_df.groupby('store_name')['total_quantity'].sum().reset_index()
            
            fig_store_pie = px.pie(
                store_category_pie,
                values='total_quantity',
                names='store_name',
                title="Quantity Distribution by Store",
                height=500  # Make pie chart bigger
            )
            fig_store_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_store_pie, use_container_width=True, className="big-chart")
        else:
            # For a specific store, show category distribution
            store_cat_pie = filtered_df[filtered_df['store_name'] == selected_store].groupby('product_category')['total_quantity'].sum().reset_index()
            
            fig_store_cat_pie = px.pie(
                store_cat_pie,
                values='total_quantity',
                names='product_category',
                title=f"Category Distribution for {selected_store}",
                height=500  # Make pie chart bigger
            )
            fig_store_cat_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_store_cat_pie, use_container_width=True, className="big-chart")
    
    with store_category_col2:
        # Stacked bar for all stores by category
        store_category = filtered_df.groupby(['store_name', 'product_category'])['total_quantity'].sum().reset_index()
        
        fig_store_category = px.bar(
            store_category,
            x='store_name',
            y='total_quantity',
            color='product_category',
            title="Product Category Quantities by Store",
            labels={
                'store_name': 'Store',
                'total_quantity': 'Quantity Sold',
                'product_category': 'Product Category'
            }
        )
        fig_store_category.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_store_category, use_container_width=True)

with tab3:
    st.markdown('<div class="sub-header">Product Analytics</div>', unsafe_allow_html=True)
    
    # Product category distribution - focus on quantity
    product_col1, product_col2 = st.columns(2)
    
    with product_col1:
        st.markdown('<div class="chart-title">Quantity Distribution by Product Category</div>', unsafe_allow_html=True)
        quantity_by_category = filtered_df.groupby('product_category')['total_quantity'].sum().reset_index()
        quantity_by_category = quantity_by_category.sort_values('total_quantity', ascending=False)
        
        fig_category_pie = px.pie(
            quantity_by_category,
            values='total_quantity',
            names='product_category',
            color_discrete_sequence=px.colors.qualitative.Bold,
            title="Product Category Quantity Distribution",
            hole=0.4,
            height=500  # Make pie chart bigger
        )
        fig_category_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_category_pie, use_container_width=True, className="big-chart")
    
    with product_col2:
        st.markdown('<div class="chart-title">Top 10 Products by Quantity</div>', unsafe_allow_html=True)
        top_products = filtered_df.groupby('item_name')['total_quantity'].sum().reset_index()
        top_products = top_products.sort_values('total_quantity', ascending=False).head(10)
        
        fig_top_products = px.bar(
            top_products,
            x='total_quantity',
            y='item_name',
            orientation='h',
            title="Top 10 Products by Quantity Sold",
            labels={'item_name': 'Product', 'total_quantity': 'Quantity Sold'},
            color_discrete_sequence=['#1E88E5'],
            text_auto=True
        )
        fig_top_products.update_layout(yaxis={'categoryorder': 'total ascending'})
        st.plotly_chart(fig_top_products, use_container_width=True)
    
    # Category performance over time
    st.markdown('<div class="chart-title">Category Performance Over Time (Quantity)</div>', unsafe_allow_html=True)
    
    category_monthly = filtered_df.groupby(['month_year', 'product_category'])['total_quantity'].sum().reset_index()
    category_monthly['sort_date'] = pd.to_datetime(category_monthly['month_year'], format='%b %Y')
    category_monthly = category_monthly.sort_values('sort_date')
    
    fig_category_trend = px.line(
        category_monthly,
        x='month_year',
        y='total_quantity',
        color='product_category',
        markers=True,
        title="Monthly Quantity Trend by Product Category",
        labels={
            'month_year': 'Month-Year',
            'total_quantity': 'Quantity Sold',
            'product_category': 'Product Category'
        }
    )
    st.plotly_chart(fig_category_trend, use_container_width=True)
    
    # Quantity vs. price analysis
    st.markdown('<div class="chart-title">Quantity vs. Price Analysis</div>', unsafe_allow_html=True)
    
    product_analysis = filtered_df.groupby('product_category').agg({
        'average_price': 'mean',
        'total_quantity': 'sum',
        'total_value': 'sum'
    }).reset_index()
    
    fig_bubble = px.scatter(
        product_analysis,
        x='average_price',
        y='total_quantity',
        size='total_value',
        color='product_category',
        hover_name='product_category',
        text='product_category',
        title="Quantity vs. Price by Product Category",
        labels={
            'average_price': 'Average Price (₹)',
            'total_quantity': 'Quantity Sold',
            'total_value': 'Total Sales Value'
        }
    )
    fig_bubble.update_traces(textposition='top center')
    st.plotly_chart(fig_bubble, use_container_width=True)
    
    # If a specific category is selected, show detailed analysis
    if selected_category != "All Categories":
        st.markdown(f'<div class="chart-title">Detailed Analysis: {selected_category}</div>', unsafe_allow_html=True)
        
        # Filter for selected category
        category_df = filtered_df[filtered_df['product_category'] == selected_category]
        
        # Top items in the category
        top_items = category_df.groupby('item_name')['total_quantity'].sum().reset_index()
        top_items = top_items.sort_values('total_quantity', ascending=False).head(10)
        
        cat_col1, cat_col2 = st.columns(2)
        
        with cat_col1:
            # Stores selling this category by quantity
            stores_selling = category_df.groupby('store_name')['total_quantity'].sum().reset_index()
            stores_selling = stores_selling.sort_values('total_quantity', ascending=False)
            
            fig_cat_stores = px.pie(
                stores_selling,
                values='total_quantity',
                names='store_name',
                title=f"Quantity of {selected_category} by Store",
                height=500  # Make pie chart bigger
            )
            fig_cat_stores.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_cat_stores, use_container_width=True, className="big-chart")
        
        with cat_col2:
            # Top items in category by quantity
            fig_cat_items = px.bar(
                top_items,
                x='item_name',
                y='total_quantity',
                title=f"Top Items in {selected_category} by Quantity",
                color='total_quantity',
                color_continuous_scale='Blues',
                labels={
                    'item_name': 'Product',
                    'total_quantity': 'Quantity Sold'
                },
                text_auto=True
            )
            fig_cat_items.update_layout(xaxis_tickangle=-45, coloraxis_showscale=False)
            st.plotly_chart(fig_cat_items, use_container_width=True)

with tab4:
    st.markdown('<div class="sub-header">Time-Based Analysis</div>', unsafe_allow_html=True)
    
    # Monthly Quantity Trend
    st.markdown('<div class="chart-title">Monthly Quantity Sold</div>', unsafe_allow_html=True)
    
    monthly_quantity = filtered_df.groupby('month_year')['total_quantity'].sum().reset_index()
    # Create datetime for proper sorting without using month_num
    monthly_quantity['sort_date'] = pd.to_datetime(monthly_quantity['month_year'], format='%b %Y')
    monthly_quantity = monthly_quantity.sort_values('sort_date')
    
    fig_monthly = px.line(
        monthly_quantity,
        x='month_year',
        y='total_quantity',
        markers=True,
        title="Monthly Quantity Trend",
        labels={
            'month_year': 'Month-Year',
            'total_quantity': 'Quantity Sold'
        },
        color_discrete_sequence=['#1E88E5']
    )
    fig_monthly.update_layout(
        xaxis_title="Month",
        yaxis_title="Quantity",
        hovermode="x unified"
    )
    st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Month-over-Month Growth in Quantity
    if len(monthly_quantity) > 1:
        st.markdown('<div class="chart-title">Month-over-Month Quantity Growth</div>', unsafe_allow_html=True)
        
        monthly_quantity['previous_quantity'] = monthly_quantity['total_quantity'].shift(1)
        monthly_quantity['growth_rate'] = ((monthly_quantity['total_quantity'] - monthly_quantity['previous_quantity']) / monthly_quantity['previous_quantity'] * 100)
        
        fig_growth = px.bar(
            monthly_quantity.dropna(),
            x='month_year',
            y='growth_rate',
            title="Month-over-Month Quantity Growth (%)",
            labels={
                'month_year': 'Month-Year',
                'growth_rate': 'Growth Rate (%)'
            },
            color='growth_rate',
            color_continuous_scale=['red', 'yellow', 'green'],
            text_auto='.1f'
        )
        fig_growth.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig_growth, use_container_width=True)
    
    # Sales by Month of Year (seasonal patterns)
    st.markdown('<div class="chart-title">Monthly Seasonal Patterns (Quantity)</div>', unsafe_allow_html=True)
    
    # Create month ordering for proper display without using month_num
    month_display_order = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    seasonal_quantity = filtered_df.groupby(['year', 'month_name'])['total_quantity'].sum().reset_index()
    
    # Custom sorting function for months
    def sort_month(x):
        return month_display_order.index(x) if x in month_display_order else -1
    
    # Sort the data by month name according to calendar order
    seasonal_quantity['month_sort'] = seasonal_quantity['month_name'].apply(sort_month)
    seasonal_quantity = seasonal_quantity.sort_values(['year', 'month_sort'])
    
    fig_seasonal = px.line(
        seasonal_quantity,
        x='month_name',
        y='total_quantity',
        color='year',
        markers=True,
        title="Quantity by Month (Year-over-Year Comparison)",
        labels={
            'month_name': 'Month',
            'total_quantity': 'Quantity Sold',
            'year': 'Year'
        },
        category_orders={"month_name": month_display_order}
    )
    st.plotly_chart(fig_seasonal, use_container_width=True)
    
    # Cumulative quantity by year
    st.markdown('<div class="chart-title">Cumulative Quantity by Year</div>', unsafe_allow_html=True)
    
    # Prepare data for cumulative chart without using month_num
    cumulative_quantity = seasonal_quantity.copy()
    
    # Calculate cumulative sum for each year
    cumulative_data = []
    for yr in cumulative_quantity['year'].unique():
        year_data = cumulative_quantity[cumulative_quantity['year'] == yr].copy()
        year_data = year_data.sort_values('month_sort')  # Ensure proper sorting
        year_data['cumulative_quantity'] = year_data['total_quantity'].cumsum()
        cumulative_data.append(year_data)
    
    cumulative_df = pd.concat(cumulative_data)
    
    fig_cumulative = px.line(
        cumulative_df,
        x='month_name',
        y='cumulative_quantity',
        color='year',
        markers=True,
        title="Cumulative Quantity by Year",
        labels={
            'month_name': 'Month',
            'cumulative_quantity': 'Cumulative Quantity',
            'year': 'Year'
        },
        category_orders={"month_name": month_display_order}
    )
    st.plotly_chart(fig_cumulative, use_container_width=True)
    
    # Quantity Distribution Across Months
    st.markdown('<div class="chart-title">Quantity Distribution Across Months</div>', unsafe_allow_html=True)
    
    monthly_distribution = filtered_df.groupby('month_name')['total_quantity'].sum().reset_index()
    monthly_distribution['month_sort'] = monthly_distribution['month_name'].apply(sort_month)
    monthly_distribution = monthly_distribution.sort_values('month_sort')
    
    fig_distribution = px.bar(
        monthly_distribution,
        x='month_name',
        y='total_quantity',
        color='total_quantity',
        color_continuous_scale='Blues',
        title="Quantity Distribution by Month",
        labels={
            'month_name': 'Month',
            'total_quantity': 'Quantity Sold'
        },
        category_orders={"month_name": month_display_order},
        text_auto=True
    )
    fig_distribution.update_layout(coloraxis_showscale=False)
    st.plotly_chart(fig_distribution, use_container_width=True)

# Footer
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown(
    """
    <div style="display: flex; justify-content: space-between; align-items: center; font-size: 0.8rem; color: #666;">
        <div>📊 Retail Analytics Dashboard</div>
        <div>Data Source: https://bookish-winner-seven.vercel.app/api/dashboard</div>
        <div>Last Updated: April 2025</div>
    </div>
    """, 
    unsafe_allow_html=True
)


