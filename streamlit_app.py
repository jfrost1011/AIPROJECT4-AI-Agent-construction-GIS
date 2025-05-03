import os
import sys
import streamlit as st
import logging
import json

try:
    # Try to import required packages first
    from dotenv import load_dotenv
    from streamlit_folium import st_folium
    import folium
    import geopandas as gpd
    
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
        # Try to import from agent_wrapper
        try:
            # Add the current directory to path
            current_dir = os.path.dirname(os.path.abspath(__file__))
            if current_dir not in sys.path:
                sys.path.insert(0, current_dir)
                
            from agent_wrapper import research_construction
            logger.info("Successfully imported from agent_wrapper")
        except ImportError as e:
            logger.error(f"Error importing from agent_wrapper: {str(e)}")
            
            # Define a fallback function as a last resort
            def research_construction(query):
                return (
                    "Unable to load the agent module. This could be due to missing files or API keys. "
                    "Please check that all required files are present and API keys are configured properly."
                )
            logger.warning("Using fallback research_construction function")
    except Exception as e:
        st.error(f"❌ Error setting up agent module: {str(e)}")
        st.info("The application will continue with limited functionality.")

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
                
except ImportError as e:
    st.error(f"❌ Missing required package: {str(e)}")
    st.info("Please make sure all required packages are installed by running: pip install -r requirements.txt")
    st.code("pip install python-dotenv streamlit-folium folium geopandas langchain langchain-openai openai tavily-python requests") 