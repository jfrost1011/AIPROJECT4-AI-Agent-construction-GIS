import os
import sys
from dotenv import load_dotenv
import logging
import streamlit as st
from streamlit_folium import st_folium
import folium
import json

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Check for required API keys in Streamlit secrets
if "OPENAI_API_KEY" not in st.secrets and "OPENAI_API_KEY" not in os.environ:
    st.error("❌ OPENAI_API_KEY not found in secrets or environment variables")
    st.stop()
else:
    # If key is in secrets but not in environment, set it in environment
    if "OPENAI_API_KEY" in st.secrets and "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

if "TAVILY_API_KEY" not in st.secrets and "TAVILY_API_KEY" not in os.environ:
    st.warning("⚠️ TAVILY_API_KEY not found in secrets or environment variables. Web search functionality may be limited.")
else:
    # If key is in secrets but not in environment, set it in environment
    if "TAVILY_API_KEY" in st.secrets and "TAVILY_API_KEY" not in os.environ:
        os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

# Import the application components
try:
    from agent import research_construction
    import geopandas as gpd
except ImportError as e:
    st.error(f"❌ Error importing required modules: {str(e)}")
    st.stop()

# Main application
st.title("🏗️ AI-Powered Construction Research Assistant")

query_type = st.selectbox("Select Query Type:", ["General Construction Query", "GIS Mapping Query"])

if query_type == "GIS Mapping Query":
    address = st.text_input("Enter Property Address:", "123 Main Street, Los Angeles, CA")
    
    if st.button("Fetch GIS Data"):
        with st.spinner("Fetching GIS data..."):
            query = f"Provide flood zone and GIS data for {address}"
            response = research_construction(query)
            
            try:
                geojson_data = json.loads(response)

                # Load GeoJSON into GeoPandas GeoDataFrame
                gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])

                # Get centroid for initial map location
                centroid = gdf.geometry.centroid.iloc[0]
                m = folium.Map(location=[centroid.y, centroid.x], zoom_start=14)

                # Add GeoJSON layer
                folium.GeoJson(geojson_data, name="GIS Data").add_to(m)

                # Display interactive map
                st_folium(m, width=700, height=500)
                
                # Display raw GeoJSON data
                st.json(geojson_data)

            except Exception as e:
                st.warning("No GIS data found or unable to parse data.")
                st.write(response)

else:  # General Construction Query
    user_query = st.text_area("Enter Your Construction Query:", "What are the current zoning regulations for ADUs in Los Angeles?")

    if st.button("Get Agent Response"):
        with st.spinner("Generating response..."):
            result = research_construction(user_query)
            st.markdown("### 🔍 Agent Response:")
            st.write(result) 