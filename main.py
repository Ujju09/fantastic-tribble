import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
from collections import Counter
import json


# Page configuration
st.set_page_config(
    page_title="UNIQ Retail Store Dashboard",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom styling
st.markdown("""
    <style>
    .main {
        padding: 1rem 1rem;
    }
    .stMetric {
        background-color: #000000;
        padding: 15px;
        border-radius: 5px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24);
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 5px;
    }
    [data-testid="stTabContent"] {
        color: black;
    }
    .big-font {
        font-size: 24px;
        font-weight: bold;
        color: #1E88E5;
    }
    </style>
""", unsafe_allow_html=True)

# App title and description
st.title("📊 UNIQ Retail Store Inventory Dashboard")
st.markdown("Interactive visualization of inventory data across retail stores")

# Function to fetch data from API
@st.cache_data(ttl=600)  # Cache data for 10 minutes
def fetch_store_data():
    """Fetch retail store data from the API"""
    api_url = "https://unforus.net/UNIQ/reporting-apis/api_retail_stores.php"
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Raise exception for HTTP errors
        data = response.json()
        if data["status"] == "success":
            # If data["data"] is a JSON string, parse it
            if isinstance(data["data"], str):
                try:
                    return json.loads(data["data"])
                except json.JSONDecodeError as e:
                    st.error(f"Error parsing JSON data: {e}")
                    return {}
            return data["data"]
        else:
            st.error(f"API returned error status: {data['status']}")
            return {}
    except Exception as e:
        st.error(f"Error fetching data: {e}")
        return {}

# Load and process data
with st.spinner("Fetching retail store inventory data..."):
    stores_data = fetch_store_data()

if not stores_data:
    st.error("No data available. Please check the API connection.")
    st.stop()

# Process the data into a DataFrame
def process_store_data(stores_data):
    all_items = []
    
    for store_name, items in stores_data.items():
        for item in items:
            item_dict = item.copy()
            item_dict["store_name"] = store_name.strip()
            all_items.append(item_dict)
    
    df = pd.DataFrame(all_items)
    
    # Handle items that don't have all fields
    if "category" not in df.columns:
        df["category"] = "Unknown"
    if "collection" not in df.columns:
        df["collection"] = "Unknown"
    if "gender" not in df.columns:
        df["gender"] = "Unknown"
    if "size" not in df.columns:
        df["size"] = "Unknown"
    
    # Ensure count is numeric
    df["count"] = pd.to_numeric(df["count"], errors="coerce").fillna(0).astype(int)
    
    return df

df = process_store_data(stores_data)

# Create sidebar filters
st.sidebar.header("Filters")

# Store filter
all_stores = ["All Stores"] + sorted(df["store_name"].unique().tolist())
selected_store = st.sidebar.selectbox("Select Store", all_stores)

# Category filter
all_categories = ["All Categories"] + sorted(df[df["category"].notna()]["category"].unique().tolist())
selected_category = st.sidebar.selectbox("Select Category", all_categories)

# Collection filter
all_collections = ["All Collections"] + sorted(df[df["collection"].notna()]["collection"].unique().tolist())
selected_collection = st.sidebar.selectbox("Select Collection", all_collections)

# Gender filter
all_genders = ["All Genders"] + sorted(df[df["gender"].notna()]["gender"].unique().tolist())
selected_gender = st.sidebar.selectbox("Select Gender", all_genders)

# Apply filters
filtered_df = df.copy()
if selected_store != "All Stores":
    filtered_df = filtered_df[filtered_df["store_name"] == selected_store]
if selected_category != "All Categories":
    filtered_df = filtered_df[filtered_df["category"] == selected_category]
if selected_collection != "All Collections":
    filtered_df = filtered_df[filtered_df["collection"] == selected_collection]
if selected_gender != "All Genders":
    filtered_df = filtered_df[filtered_df["gender"] == selected_gender]

# Create dashboard tabs
tab1, tab2, tab3 = st.tabs(["📈 Overview", "🏬 Store Analysis", "🧥 Product Analysis"])

# Overview Tab
with tab1:
    # Top metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_items = filtered_df["count"].sum()
        st.metric("Total Inventory Items", f"{total_items:,}")
    
    with col2:
        total_stores = filtered_df["store_name"].nunique()
        st.metric("Total Stores", total_stores)
    
    with col3:
        total_categories = filtered_df[filtered_df["category"].notna()]["category"].nunique()
        st.metric("Product Categories", total_categories)
    
    with col4:
        total_collections = filtered_df[filtered_df["collection"].notna()]["collection"].nunique()
        st.metric("Collections", total_collections)
    
    st.markdown("---")
    
    # Main charts 
    col1, col2 = st.columns(2)
    
    with col1:
        # Inventory by Store
        st.subheader("Inventory by Store")
        store_inventory = filtered_df.groupby("store_name")["count"].sum().reset_index()
        store_inventory = store_inventory.sort_values(by="count", ascending=False)
        
        fig = px.bar(
            store_inventory,
            x="store_name",
            y="count",
            text="count",
            title="Total Inventory by Store",
            labels={"count": "Item Count", "store_name": "Store Name"}
        )
        fig.update_traces(texttemplate='%{text:.0f}', textposition='outside')
        fig.update_layout(uniformtext_minsize=8, uniformtext_mode='hide')
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Inventory by Category
        if "category" in filtered_df.columns and filtered_df["category"].notna().any():
            st.subheader("Inventory by Category")
            category_inventory = filtered_df.groupby("category")["count"].sum().reset_index()
            category_inventory = category_inventory.sort_values(by="count", ascending=False)
            
            fig = px.pie(
                category_inventory,
                values="count",
                names="category",
                title="Inventory Distribution by Category",
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label+value')
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No category data available for visualization.")

    # Third chart - Collection distribution
    if "collection" in filtered_df.columns and filtered_df["collection"].notna().any():
        st.subheader("Inventory by Collection")
        collection_inventory = filtered_df.groupby("collection")["count"].sum().reset_index()
        collection_inventory = collection_inventory.sort_values(by="count", ascending=False)
        
        fig = px.bar(
            collection_inventory,
            x="collection",
            y="count",
            title="Inventory by Collection",
            labels={"count": "Item Count", "collection": "Collection"}
        )
        fig.update_layout(xaxis={'categoryorder':'total descending'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No collection data available for visualization.")

    # Gender distribution
    if "gender" in filtered_df.columns and filtered_df["gender"].notna().any():
        st.subheader("Inventory by Gender")
        gender_inventory = filtered_df.groupby("gender")["count"].sum().reset_index()
        
        fig = px.pie(
            gender_inventory,
            values="count",
            names="gender",
            title="Inventory Distribution by Gender",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No gender data available for visualization.")

# Store Analysis Tab
with tab2:
    if filtered_df.empty:
        st.info("No data available with the selected filters.")
    else:
        st.subheader("Store Inventory Analysis")
        
        # Store selection for detailed analysis
        if selected_store == "All Stores":
            store_for_analysis = st.selectbox(
                "Select a store for detailed analysis:",
                sorted(df["store_name"].unique().tolist())
            )
            store_df = df[df["store_name"] == store_for_analysis]
        else:
            store_df = filtered_df
            store_for_analysis = selected_store
        
        # Store metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            store_total = store_df["count"].sum()
            st.metric("Total Inventory", f"{store_total:,}")
        
        with col2:
            store_categories = store_df[store_df["category"].notna()]["category"].nunique()
            st.metric("Categories", store_categories)
        
        with col3:
            store_collections = store_df[store_df["collection"].notna()]["collection"].nunique()
            st.metric("Collections", store_collections)
        
        # Category by collection heatmap
        if "category" in store_df.columns and "collection" in store_df.columns and store_df["category"].notna().any() and store_df["collection"].notna().any():
            st.subheader(f"Category × Collection Heatmap for {store_for_analysis}")
            
            try:
                category_collection_df = store_df.pivot_table(
                    index="category",
                    columns="collection",
                    values="count",
                    aggfunc="sum",
                    fill_value=0
                )
                
                fig = px.imshow(
                    category_collection_df,
                    labels=dict(x="Collection", y="Category", color="Item Count"),
                    text_auto=True,
                    aspect="auto",
                    color_continuous_scale="Viridis"
                )
                fig.update_layout(height=450)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not create heatmap: {e}")
        
        # Top collections in store
        if "collection" in store_df.columns and store_df["collection"].notna().any():
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader(f"Top Collections in {store_for_analysis}")
                top_collections = store_df.groupby("collection")["count"].sum().reset_index()
                top_collections = top_collections.sort_values(by="count", ascending=False).head(10)
                
                fig = px.bar(
                    top_collections,
                    x="collection",
                    y="count",
                    title=f"Top 10 Collections in {store_for_analysis}",
                    labels={"count": "Item Count", "collection": "Collection"}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader(f"Size Distribution in {store_for_analysis}")
                if "size" in store_df.columns and store_df["size"].notna().any():
                    size_dist = store_df.groupby("size")["count"].sum().reset_index()
                    size_dist = size_dist.sort_values(by="count", ascending=False)
                    
                    fig = px.pie(
                        size_dist,
                        values="count",
                        names="size",
                        title=f"Size Distribution in {store_for_analysis}",
                        hole=0.4
                    )
                    fig.update_traces(textposition='inside', textinfo='percent+label')
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No size data available for visualization.")
        
        # Treemap for store inventory
        st.subheader(f"Inventory Hierarchy in {store_for_analysis}")
        
        # Define hierarchical path based on available columns
        treemap_path = ["store_name"]
        if "category" in store_df.columns and store_df["category"].notna().any():
            treemap_path.append("category")
        if "collection" in store_df.columns and store_df["collection"].notna().any():
            treemap_path.append("collection")
        if "gender" in store_df.columns and store_df["gender"].notna().any():
            treemap_path.append("gender")
        if "size" in store_df.columns and store_df["size"].notna().any():
            treemap_path.append("size")
        
        # Group data according to the path
        try:
            treemap_data = store_df.groupby(treemap_path)["count"].sum().reset_index()
            
            fig = px.treemap(
                treemap_data,
                path=treemap_path,
                values="count",
                color="count",
                color_continuous_scale="Blues",
                title=f"Inventory Hierarchy in {store_for_analysis}"
            )
            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.warning(f"Could not create treemap: {e}")

# Product Analysis Tab
with tab3:
    if filtered_df.empty:
        st.info("No data available with the selected filters.")
    else:
        st.subheader("Product Category and Collection Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if "category" in filtered_df.columns and filtered_df["category"].notna().any():
                # Category selection for detailed analysis
                if selected_category == "All Categories":
                    category_options = sorted(filtered_df[filtered_df["category"].notna()]["category"].unique().tolist())
                    if category_options:
                        category_for_analysis = st.selectbox(
                            "Select a category for detailed analysis:",
                            category_options
                        )
                        category_df = filtered_df[filtered_df["category"] == category_for_analysis]
                    else:
                        st.info("No category data available with current filters.")
                        category_df = pd.DataFrame()
                else:
                    category_df = filtered_df
                    category_for_analysis = selected_category
                
                if not category_df.empty:
                    # Stores with this category
                    st.subheader(f"Stores with {category_for_analysis} Products")
                    stores_with_category = category_df.groupby("store_name")["count"].sum().reset_index()
                    stores_with_category = stores_with_category.sort_values(by="count", ascending=False)
                    
                    fig = px.bar(
                        stores_with_category,
                        x="store_name",
                        y="count",
                        title=f"Distribution of {category_for_analysis} Across Stores",
                        labels={"count": "Item Count", "store_name": "Store Name"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Collections in this category
                    if "collection" in category_df.columns and category_df["collection"].notna().any():
                        st.subheader(f"Collections in {category_for_analysis} Category")
                        collections_in_category = category_df.groupby("collection")["count"].sum().reset_index()
                        collections_in_category = collections_in_category.sort_values(by="count", ascending=False)
                        
                        fig = px.pie(
                            collections_in_category,
                            values="count",
                            names="collection",
                            title=f"Collections in {category_for_analysis} Category",
                            hole=0.4
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No category data available for analysis.")
        
        with col2:
            if "collection" in filtered_df.columns and filtered_df["collection"].notna().any():
                # Collection selection for detailed analysis
                if selected_collection == "All Collections":
                    collection_options = sorted(filtered_df[filtered_df["collection"].notna()]["collection"].unique().tolist())
                    if collection_options:
                        collection_for_analysis = st.selectbox(
                            "Select a collection for detailed analysis:",
                            collection_options
                        )
                        collection_df = filtered_df[filtered_df["collection"] == collection_for_analysis]
                    else:
                        st.info("No collection data available with current filters.")
                        collection_df = pd.DataFrame()
                else:
                    collection_df = filtered_df
                    collection_for_analysis = selected_collection
                
                if not collection_df.empty:
                    # Stores with this collection
                    st.subheader(f"Stores with {collection_for_analysis} Collection")
                    stores_with_collection = collection_df.groupby("store_name")["count"].sum().reset_index()
                    stores_with_collection = stores_with_collection.sort_values(by="count", ascending=False)
                    
                    fig = px.bar(
                        stores_with_collection,
                        x="store_name",
                        y="count",
                        title=f"Distribution of {collection_for_analysis} Across Stores",
                        labels={"count": "Item Count", "store_name": "Store Name"}
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Size distribution in this collection
                    if "size" in collection_df.columns and collection_df["size"].notna().any():
                        st.subheader(f"Size Distribution in {collection_for_analysis} Collection")
                        sizes_in_collection = collection_df.groupby("size")["count"].sum().reset_index()
                        sizes_in_collection = sizes_in_collection.sort_values(by="count", ascending=False)
                        
                        fig = px.pie(
                            sizes_in_collection,
                            values="count",
                            names="size",
                            title=f"Size Distribution in {collection_for_analysis}",
                            hole=0.4
                        )
                        fig.update_traces(textposition='inside', textinfo='percent+label')
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("No collection data available for analysis.")
        
        # Sunburst chart for product hierarchy
        st.subheader("Product Hierarchy Visualization")
        
        # Define hierarchical path based on available columns
        sunburst_path = []
        if "category" in filtered_df.columns and filtered_df["category"].notna().any():
            sunburst_path.append("category")
        if "collection" in filtered_df.columns and filtered_df["collection"].notna().any():
            sunburst_path.append("collection")
        if "gender" in filtered_df.columns and filtered_df["gender"].notna().any():
            sunburst_path.append("gender")
        if "size" in filtered_df.columns and filtered_df["size"].notna().any():
            sunburst_path.append("size")
        
        if sunburst_path:
            # Group data according to the path
            try:
                sunburst_data = filtered_df.groupby(sunburst_path)["count"].sum().reset_index()
                
                fig = px.sunburst(
                    sunburst_data,
                    path=sunburst_path,
                    values="count",
                    color="count",
                    color_continuous_scale="Viridis",
                    title="Product Hierarchy Visualization"
                )
                fig.update_layout(height=600)
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not create sunburst chart: {e}")
        else:
            st.info("Not enough hierarchical data available for visualization.")
        
        # Parallel coordinates plot for multi-dimensional analysis
        st.subheader("Multi-Dimensional Product Analysis")
        
        # Select columns for parallel coordinates
        parcoords_cols = []
        
        # Add categorical dimensions
        for col in ["store_name", "category", "collection", "gender", "size"]:
            if col in filtered_df.columns and filtered_df[col].notna().any():
                parcoords_cols.append(col)
        
        # Always include count
        parcoords_cols.append("count")
        
        # Only proceed if we have at least 3 dimensions (2 categorical + count)
        if len(parcoords_cols) >= 3:
            # Prepare data for parallel coordinates
            parallel_data = filtered_df[parcoords_cols].copy()
            
            # Create dimensions list for the plot
            dimensions = []
            
            # Add categorical dimensions
            for col in parcoords_cols:
                if col != "count":
                    # Map categorical values to numeric indices
                    unique_vals = parallel_data[col].unique()
                    val_map = {val: idx for idx, val in enumerate(unique_vals)}
                    
                    dimensions.append(
                        dict(
                            range=[0, len(unique_vals)],
                            tickvals=list(range(len(unique_vals))),
                            ticktext=unique_vals,
                            label=col,
                            values=parallel_data[col].map(val_map)
                        )
                    )
            
            # Add count dimension
            dimensions.append(
                dict(
                    range=[0, parallel_data["count"].max()],
                    label="Item Count",
                    values=parallel_data["count"]
                )
            )
            
            # Create the parallel coordinates plot
            fig = go.Figure(data=
                go.Parcoords(
                    line=dict(
                        color=parallel_data["count"],
                        colorscale="Viridis",
                        showscale=True
                    ),
                    dimensions=dimensions
                )
            )
            
            fig.update_layout(
                plot_bgcolor="white",
                paper_bgcolor="white",
                title="Multi-Dimensional Product Analysis",
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Not enough dimensions available for multi-dimensional analysis.")



# Footer
st.markdown("---")
st.markdown("*Data provided by UNIQ Retail Stores API*")