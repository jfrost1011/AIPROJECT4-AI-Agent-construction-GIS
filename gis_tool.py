import requests
import json
import geopandas as gpd
from shapely.geometry import Point
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fetch_parcel_data(address, include_flood_zone=True, include_soil_data=False):
    """
    Fetch GIS data for a specific address.
    
    Args:
        address (str): The address to geocode and fetch data for
        include_flood_zone (bool): Whether to include FEMA flood zone data
        include_soil_data (bool): Whether to include soil data (placeholder for future implementation)
    
    Returns:
        dict: A dictionary containing the geocoded location and any GIS data found
    """
    try:
        # Step 1: Geocode the address to get coordinates
        coordinates = geocode_address(address)
        
        if not coordinates:
            return {"status": "error", "message": "Unable to geocode address"}
        
        # Create result dictionary with location data
        result = {
            "status": "success",
            "location": {
                "address": address,
                "latitude": coordinates["lat"],
                "longitude": coordinates["lon"],
                "confidence": coordinates.get("score", 0)
            },
            "data": {}
        }
        
        # Step 2: Fetch flood zone data if requested
        if include_flood_zone:
            flood_data = fetch_flood_zone_data(coordinates["lat"], coordinates["lon"])
            result["data"]["flood_zone"] = flood_data
        
        # Step 3: Fetch soil data if requested (placeholder for future implementation)
        if include_soil_data:
            soil_data = {"message": "Soil data fetching not implemented yet"}
            result["data"]["soil"] = soil_data
            
        return result
            
    except Exception as e:
        logger.error(f"Error fetching parcel data: {str(e)}")
        return {"status": "error", "message": f"An error occurred: {str(e)}"}

def geocode_address(address):
    """
    Convert an address into geographic coordinates using ArcGIS API.
    
    Args:
        address (str): The address to geocode
    
    Returns:
        dict: Dictionary with lat, lon, and score, or None if geocoding failed
    """
    # ArcGIS geocoding API endpoint
    geocode_url = "https://geocode.arcgis.com/arcgis/rest/services/World/GeocodeServer/findAddressCandidates"
    
    # Geocode parameters
    geocode_params = {
        "SingleLine": address,
        "f": "json",
        "outFields": "score,Addr_type"  # Include score and address type
    }
    
    try:
        logger.info(f"Geocoding address: {address}")
        response = requests.get(geocode_url, params=geocode_params, timeout=10)
        response.raise_for_status()  # Raise exception for HTTP errors
        
        data = response.json()
        
        if not data.get("candidates"):
            logger.warning(f"No geocoding candidates found for address: {address}")
            return None

        # Get the highest-scoring candidate
        best_candidate = data["candidates"][0]
        location = best_candidate["location"]
        
        return {
            "lat": location["y"],
            "lon": location["x"],
            "score": best_candidate.get("score", 0)
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Geocoding request failed: {str(e)}")
        return None
    except (KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error parsing geocoding response: {str(e)}")
        return None

def fetch_flood_zone_data(lat, lon):
    """
    Fetch flood zone data from FEMA's GIS services.
    
    Args:
        lat (float): Latitude of the point
        lon (float): Longitude of the point
    
    Returns:
        dict: Flood zone information or error message
    """
    # FEMA flood zone GIS endpoint
    gis_url = "https://hazards.fema.gov/gis/nfhl/rest/services/public/NFHL/MapServer/28/query"
    
    # Parameters for GIS query
    gis_params = {
        "geometry": f"{lon},{lat}",
        "geometryType": "esriGeometryPoint",
        "inSR": 4326,
        "spatialRel": "esriSpatialRelIntersects",
        "outFields": "*",
        "returnGeometry": "true",
        "f": "geojson"
    }
    
    try:
        logger.info(f"Fetching flood zone data for coordinates: {lat}, {lon}")
        response = requests.get(gis_url, params=gis_params, timeout=15)
        response.raise_for_status()
        
        # Create a temporary file to handle the GeoJSON
        temp_geojson = "temp_flood_data.geojson"
        with open(temp_geojson, 'w') as f:
            f.write(response.text)
        
        # Use geopandas to read the GeoJSON data
        data = gpd.read_file(temp_geojson)
        
        # Clean up the temporary file
        if os.path.exists(temp_geojson):
            os.remove(temp_geojson)
        
        if data.empty:
            return {"status": "no_data", "message": "No flood zone data available for this location"}
        
        # Extract relevant flood zone information
        flood_info = {}
        if 'FLD_ZONE' in data.columns:
            flood_info["zone"] = data.iloc[0]['FLD_ZONE']
        if 'SFHA_TF' in data.columns:
            flood_info["special_flood_hazard_area"] = data.iloc[0]['SFHA_TF']
        if 'ZONE_SUBTY' in data.columns:
            flood_info["zone_subtype"] = data.iloc[0]['ZONE_SUBTY']
            
        # If we didn't extract specific fields, return a simplified version of all data
        if not flood_info:
            # Convert to dictionary and handle non-serializable objects
            flood_info = json.loads(data.drop(columns=['geometry']).to_json(orient='records'))[0]
            
        return {
            "status": "success",
            "flood_zone_data": flood_info
        }
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Flood zone data request failed: {str(e)}")
        return {"status": "error", "message": f"Failed to fetch flood zone data: {str(e)}"}
    except (gpd.io.file.DriverError, ValueError) as e:
        logger.error(f"Error processing GeoJSON data: {str(e)}")
        return {"status": "error", "message": "Failed to process flood zone GeoJSON data"}
    except Exception as e:
        logger.error(f"Unexpected error fetching flood zone data: {str(e)}")
        return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}

def get_point_in_polygon(lat, lon, gdf):
    """
    Check if a point is within any polygon in a GeoDataFrame.
    
    Args:
        lat (float): Latitude of the point
        lon (float): Longitude of the point
        gdf (GeoDataFrame): GeoDataFrame containing polygons
    
    Returns:
        GeoDataFrame row or None: The first polygon containing the point, or None
    """
    point = Point(lon, lat)
    for idx, row in gdf.iterrows():
        if row.geometry.contains(point):
            return row
    return None

if __name__ == "__main__":
    # Example usage
    test_address = "123 Main Street, Los Angeles, CA"
    print(f"Fetching GIS data for: {test_address}")
    
    parcel_info = fetch_parcel_data(test_address)
    print(json.dumps(parcel_info, indent=2))
    
    # Additional example with different address
    flood_prone_address = "1001 Bourbon Street, New Orleans, LA"
    print(f"\nFetching GIS data for: {flood_prone_address}")
    
    parcel_info = fetch_parcel_data(flood_prone_address)
    print(json.dumps(parcel_info, indent=2)) 