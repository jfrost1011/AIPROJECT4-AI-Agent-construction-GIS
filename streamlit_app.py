import os
import sys
import subprocess
import streamlit as st

# Function to check if a package is installed
def is_package_installed(package_name):
    try:
        __import__(package_name.replace("-", "_"))
        return True
    except ImportError:
        return False

# Function to install a package
def install_package(package_name):
    st.info(f"Installing {package_name}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        st.success(f"✅ {package_name} installed successfully!")
        return True
    except Exception as e:
        st.error(f"❌ Failed to install {package_name}: {str(e)}")
        return False

# Check and install required packages
required_packages = [
    "python-dotenv",
    "streamlit-folium",
    "folium",
    "geopandas",
    "langchain",
    "langchain-openai",
    "openai",
    "tavily-python",
    "requests"
]

missing_packages = []
for package in required_packages:
    if not is_package_installed(package.replace("-", "_")):
        missing_packages.append(package)

if missing_packages:
    st.warning("Some required packages are missing. Installing them now...")
    for package in missing_packages:
        if not install_package(package):
            st.error(f"Failed to install {package}. Please try reloading the app.")
            st.stop()
    st.info("Reloading the app with the newly installed packages...")
    st.experimental_rerun()

# Now import the required packages
import logging
import json
from dotenv import load_dotenv
from streamlit_folium import st_folium
import folium

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
try:
    load_dotenv()
    logger.info("Environment variables loaded successfully")
except Exception as e:
    logger.error(f"Error loading environment variables: {str(e)}")

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
    # Try to import from the current directory
    try:
        from agent import research_construction
        import geopandas as gpd
        logger.info("Successfully imported from current directory")
    except ImportError:
        # If not found, try to import from the AIPROJECT4-AI-Agent-construction-GIS directory
        sys.path.append(os.path.join(os.path.dirname(__file__), "AIPROJECT4-AI-Agent-construction-GIS"))
        from agent import research_construction
        import geopandas as gpd
        logger.info("Successfully imported from AIPROJECT4-AI-Agent-construction-GIS directory")
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