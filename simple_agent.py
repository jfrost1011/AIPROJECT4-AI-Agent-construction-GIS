"""
Simplified agent implementation for the Construction Research Assistant.
This version doesn't require external API services and works as a fallback.
"""
import os
import json
import logging
import sys
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Sample responses for different query types
SAMPLE_RESPONSES = {
    "zoning": "Zoning regulations for residential construction typically include setback requirements, height limitations, lot coverage restrictions, and permitted uses. For specific zones, consult your local planning department.",
    "permits": "Construction permits are typically required for new structures, major renovations, electrical work, plumbing changes, and structural modifications. The process usually involves application submission, plan review, fee payment, and inspections.",
    "materials": "Common construction materials include concrete (foundations), wood (framing), steel (structural support), brick/stone (facades), glass (windows), and various insulation materials. Selection depends on budget, climate, and design requirements.",
    "techniques": "Modern construction techniques include modular construction, prefabrication, 3D printing of components, and use of BIM (Building Information Modeling) for design and project management.",
    "regulations": "Construction regulations typically cover building codes, safety standards, energy efficiency requirements, accessibility guidelines, and environmental impact considerations.",
    "flood": "Flood zone data is categorized by FEMA into zones like A (high risk), B/X (moderate risk), and C/X (minimal risk). Properties in high-risk zones often require flood insurance and special building considerations.",
    "soil": "Soil types significantly impact construction decisions, including foundation design, drainage solutions, and structural requirements. Common soil classifications include clay, sand, silt, loam, and rock.",
    "costs": "Construction costs vary widely based on location, materials, design complexity, labor rates, and market conditions. Current average costs range from $150-$400 per square foot for residential construction, depending on quality level.",
    "timeline": "Typical construction timelines include 3-6 months for small renovations, 6-12 months for custom homes, and 1-3+ years for larger commercial projects. Factors affecting timeline include project size, complexity, permitting, weather, and labor availability."
}

# Different locations for sample GeoJSON data
LOCATIONS = {
    "los angeles": {
        "lat": 34.0522,
        "lon": -118.2437,
        "properties": {
            "address": "123 Main Street, Los Angeles, CA",
            "zone_type": "Residential R1",
            "flood_zone": "X (Minimal Risk)",
            "soil_type": "Urban Land Complex",
            "parcel_id": "LA-1234567890",
            "lot_size": "7,500 sq ft",
            "building_height_limit": "45 feet",
            "setback_front": "20 feet",
            "setback_rear": "15 feet",
            "setback_sides": "5 feet"
        }
    },
    "san francisco": {
        "lat": 37.7749,
        "lon": -122.4194,
        "properties": {
            "address": "456 Market Street, San Francisco, CA",
            "zone_type": "Mixed-Use Commercial",
            "flood_zone": "B (Moderate Risk)",
            "soil_type": "Bay Mud",
            "parcel_id": "SF-9876543210",
            "lot_size": "5,000 sq ft",
            "building_height_limit": "65 feet",
            "setback_front": "10 feet",
            "setback_rear": "10 feet",
            "setback_sides": "5 feet"
        }
    },
    "new york": {
        "lat": 40.7128,
        "lon": -74.0060,
        "properties": {
            "address": "789 Broadway, New York, NY",
            "zone_type": "R8 High-Density Residential",
            "flood_zone": "A (High Risk)",
            "soil_type": "Urban Fill",
            "parcel_id": "NY-5678901234",
            "lot_size": "2,500 sq ft",
            "building_height_limit": "120 feet",
            "setback_front": "0 feet",
            "setback_rear": "30 feet",
            "setback_sides": "0 feet"
        }
    },
    "default": {
        "lat": 39.8283,
        "lon": -98.5795,
        "properties": {
            "address": "123 Main Street, Any City, USA",
            "zone_type": "Residential",
            "flood_zone": "X (Minimal Risk)",
            "soil_type": "Loam",
            "parcel_id": "12345-67890",
            "lot_size": "5,000 sq ft",
            "building_height_limit": "35 feet",
            "setback_front": "20 feet",
            "setback_rear": "15 feet",
            "setback_sides": "5 feet"
        }
    }
}

def get_location_for_address(address):
    """Determine which location data to use based on the address"""
    address_lower = address.lower()
    
    for key in LOCATIONS:
        if key in address_lower:
            return LOCATIONS[key]
    
    # If no match, return default
    return LOCATIONS["default"]

def create_geojson_for_address(address):
    """Create GeoJSON data for a given address"""
    # Get location data based on address
    location = get_location_for_address(address)
    
    # Create a square polygon centered at the location's coordinates
    lat, lon = location["lat"], location["lon"]
    # Create a small square (approximately 100x100 meters)
    delta = 0.001  # roughly 100 meters at most latitudes
    
    # Create GeoJSON
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    # Use the address from the query, but keep the rest of the properties
                    "address": address,
                    **location["properties"]
                },
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [
                        [
                            [lon - delta, lat - delta],
                            [lon + delta, lat - delta],
                            [lon + delta, lat + delta],
                            [lon - delta, lat + delta],
                            [lon - delta, lat - delta]
                        ]
                    ]
                }
            }
        ]
    }
    
    return geojson

def get_best_matching_response(query):
    """Get the best matching response based on keywords in the query"""
    query = query.lower()
    
    # Check for GIS/mapping/property related queries with an address
    address_pattern = r"for ([\w\s,]+)$"
    if any(word in query for word in ["map", "gis", "flood zone", "flood data", "parcel", "property"]):
        # Look for an address in the query
        address_match = re.search(address_pattern, query)
        
        if address_match:
            address = address_match.group(1).strip()
            logger.info(f"Extracted address: {address}")
            geojson = create_geojson_for_address(address)
            return json.dumps(geojson)
        else:
            # Default GeoJSON if no address found
            return json.dumps(create_geojson_for_address("123 Main Street, Any City, USA"))
    
    # Check for keyword matches in other categories
    best_match = None
    max_matches = 0
    
    for topic, response in SAMPLE_RESPONSES.items():
        if topic in query:
            # Direct topic match
            return response
        
        # Count word matches
        matches = sum(1 for word in query.split() if word in topic or topic in word)
        if matches > max_matches:
            max_matches = matches
            best_match = response
    
    # If we found a reasonable match, return it
    if best_match:
        return best_match
    
    # Default response
    return (
        "I understand you're asking about construction, but I don't have specific information on that topic. "
        "For detailed and accurate information, please consult with a local construction professional, "
        "planning department, or building authority in your area."
    )

def research_construction(query):
    """
    Primary function to handle construction research queries.
    This simplified version doesn't use external APIs.
    
    Args:
        query (str): The user's construction-related query
        
    Returns:
        str: Response to the query
    """
    try:
        logger.info(f"Processing query: {query}")
        
        # Check if we have API keys (for logging purposes only in this simplified version)
        if "OPENAI_API_KEY" in os.environ:
            logger.info("OpenAI API key is available")
        else:
            logger.warning("OpenAI API key not found")
            
        if "TAVILY_API_KEY" in os.environ:
            logger.info("Tavily API key is available")
        else:
            logger.warning("Tavily API key not found")
        
        # Get response based on query content
        response = get_best_matching_response(query)
        return response
        
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return f"I encountered an error while processing your request: {str(e)}"

# Test the function if run directly
if __name__ == "__main__":
    test_queries = [
        "What are the zoning regulations for ADUs in Los Angeles?",
        "How do I get a building permit?",
        "What are the best materials for hurricane-resistant construction?",
        "Tell me about modern construction techniques",
        "What flood zone is 123 Main Street in?",
        "Provide flood zone and GIS data for 123 Main Street, Los Angeles, CA",
        "Provide flood zone and GIS data for 456 Market Street, San Francisco, CA"
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        response = research_construction(query)
        print(f"Response: {response[:100]}..." if len(response) > 100 else f"Response: {response}") 