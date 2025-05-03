import os
import sys
import streamlit as st
import logging
import json

# Use session state to store data between reruns
if 'has_run_query' not in st.session_state:
    st.session_state.has_run_query = False
if 'response_data' not in st.session_state:
    st.session_state.response_data = None
if 'query_address' not in st.session_state:
    st.session_state.query_address = None

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

    # Define a function to handle GIS query
    def process_gis_query(address):
        """Process a GIS query for the given address"""
        query = f"Provide flood zone and GIS data for {address}"
        
        # Show debugging information in a collapsible section
        with st.expander("Debug Information", expanded=False):
            st.info(f"Query sent to agent: {query}")
        
        # Get response from agent
        response = research_construction(query)
        
        # Save the response and address for state persistence
        st.session_state.has_run_query = True
        st.session_state.response_data = response
        st.session_state.query_address = address
        
        return response

    # Define a function to display map and data from a JSON response
    def display_gis_data(response, address):
        """Display GIS data from the JSON response"""
        # Debug: show raw response
        with st.expander("Raw Response", expanded=False):
            st.code(response, language="json")
        
        try:
            # Try to parse as JSON
            geojson_data = json.loads(response)
            
            # Display basic info about the GeoJSON
            st.success(f"✅ Successfully retrieved GIS data for: {address}")
            
            if "features" in geojson_data and len(geojson_data["features"]) > 0:
                # Show property information
                feature = geojson_data["features"][0]
                if "properties" in feature:
                    props = feature["properties"]
                    st.subheader("Property Information")
                    for key, value in props.items():
                        st.write(f"**{key}:** {value}")
                
                # Check if geometry exists
                if "geometry" in feature and "coordinates" in feature["geometry"]:
                    st.subheader("Location Map")
                    
                    try:
                        # Load GeoJSON into GeoPandas GeoDataFrame
                        gdf = gpd.GeoDataFrame.from_features(geojson_data["features"])
                        
                        # Get centroid for initial map location
                        centroid = gdf.geometry.centroid.iloc[0]
                        
                        # Create map centered at the property
                        m = folium.Map(location=[centroid.y, centroid.x], zoom_start=14)
                        
                        # Add GeoJSON layer
                        folium.GeoJson(
                            geojson_data, 
                            name="GIS Data",
                            style_function=lambda x: {
                                'fillColor': '#3388ff',
                                'color': '#3388ff',
                                'weight': 2,
                                'fillOpacity': 0.4,
                            }
                        ).add_to(m)
                        
                        # Add a marker at the centroid
                        folium.Marker(
                            [centroid.y, centroid.x],
                            popup=address,
                            icon=folium.Icon(color='red', icon='home')
                        ).add_to(m)
                        
                        # Display the map
                        map_data = st_folium(m, width=700, height=500)
                        
                        # Display map interaction info if available
                        if map_data:
                            with st.expander("Map Interaction Data", expanded=False):
                                st.write(map_data)
                                
                    except Exception as map_error:
                        st.error(f"Error displaying map: {str(map_error)}")
                        # Show detailed error info
                        with st.expander("Map Error Details"):
                            st.code(str(map_error))
            else:
                st.warning("The GeoJSON data does not contain any features to display on the map.")
            
            # Display raw GeoJSON data
            with st.expander("View Raw GeoJSON Data"):
                st.json(geojson_data)

        except json.JSONDecodeError as json_error:
            st.error("The response is not valid JSON format.")
            st.info("Here's the raw response received:")
            st.write(response)
            with st.expander("JSON Error Details"):
                st.code(str(json_error))
        except Exception as e:
            st.warning("Error processing GIS data.")
            st.info("Here's the raw response received:")
            st.write(response)
            with st.expander("Error Details"):
                st.code(str(e))

    # Main application
    st.title("🏗️ AI-Powered Construction Research Assistant")

    query_type = st.selectbox("Select Query Type:", ["General Construction Query", "GIS Mapping Query"])

    if query_type == "GIS Mapping Query":
        address = st.text_input("Enter Property Address:", "123 Main Street, Los Angeles, CA")
        
        # Create a button to fetch GIS data
        if st.button("Fetch GIS Data"):
            with st.spinner("Fetching GIS data..."):
                # Process query and update session state
                response = process_gis_query(address)
                # Display the results
                display_gis_data(response, address)
        
        # If we have previously run a query, display the results
        elif st.session_state.has_run_query:
            # Check if the address has changed
            if st.session_state.query_address != address:
                st.info("Click 'Fetch GIS Data' to get information for this address.")
            else:
                # Display previous results
                st.info("Displaying previously fetched results:")
                display_gis_data(st.session_state.response_data, st.session_state.query_address)

    else:  # General Construction Query
        user_query = st.text_area("Enter Your Construction Query:", "What are the current zoning regulations for ADUs in Los Angeles?")

        if st.button("Get Agent Response"):
            with st.spinner("Generating response..."):
                result = research_construction(user_query)
                # Save to session state
                st.session_state.has_run_query = True
                st.session_state.response_data = result
                st.session_state.query_address = user_query
                # Display result
                st.markdown("### 🔍 Agent Response:")
                st.write(result)
        
        # If we have previously run a query, display the results
        elif st.session_state.has_run_query and st.session_state.query_address == user_query:
            st.markdown("### 🔍 Agent Response:")
            st.write(st.session_state.response_data)
                
except ImportError as e:
    st.error(f"❌ Missing required package: {str(e)}")
    st.info("Please make sure all required packages are installed by running: pip install -r requirements.txt")
    st.code("pip install python-dotenv streamlit-folium folium geopandas langchain langchain-openai openai tavily-python requests") 