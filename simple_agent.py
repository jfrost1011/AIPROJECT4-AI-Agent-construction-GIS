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
    "timeline": "Typical construction timelines include 3-6 months for small renovations, 6-12 months for custom homes, and 1-3+ years for larger commercial projects. Factors affecting timeline include project size, complexity, permitting, weather, and labor availability.",
    "measure backyard": "To measure your backyard for an ADU (Accessory Dwelling Unit), follow these steps:\n1. Use a long measuring tape to determine the length and width of your yard.\n2. Mark the property boundaries clearly.\n3. Note the distance from your main house and property lines.\n4. Check local setback requirements (typically 5-15 feet from property lines).\n5. Measure and note any obstructions like trees, utility lines, or existing structures.\n6. Calculate the total square footage to ensure it meets minimum ADU size requirements.\n7. Consider creating a scale drawing on graph paper or using a digital design tool.",
    "adu": "Accessory Dwelling Units (ADUs) are secondary housing units on residential properties. Key considerations include: local zoning regulations, minimum/maximum size requirements (typically 150-1,200 sq ft), setbacks from property lines, height restrictions, parking requirements, utility connections, and design compatibility with the primary residence. Many municipalities have recently relaxed ADU restrictions to address housing shortages.",
    "foundation": "Residential foundations typically include slab-on-grade, crawlspace, or basement options. Selection depends on soil conditions, climate, budget, and building design. Proper foundation construction requires excavation, forming, reinforcement placement, concrete pouring, waterproofing, and insulation. Consult with a structural engineer for specific requirements based on your location and building type.",
    "electrical": "Residential electrical work must comply with the National Electrical Code (NEC) and local amendments. This includes proper sizing of service panels (typically 100-200 amps for homes), appropriate wire gauges, GFCI protection in wet areas, AFCI protection in living spaces, grounding systems, and dedicated circuits for major appliances. Always hire a licensed electrician for safety and code compliance.",
    "plumbing": "Residential plumbing systems include water supply, drainage, and venting components. Materials typically include copper, PEX, or CPVC for supply lines and PVC or ABS for drains. Proper installation requires appropriate pipe sizing, slope for drainage (typically 1/4 inch per foot), venting for each fixture, and accessibility for maintenance. Most jurisdictions require permits and inspections for new plumbing work.",
    "insulation": "Proper insulation improves energy efficiency and comfort. Common types include fiberglass batts (R-13 to R-21 for walls, R-30 to R-60 for attics), spray foam (highest R-value per inch), cellulose (environmentally friendly), and rigid foam board (ideal for basements). Recommended R-values vary by climate zone, with higher values needed in colder regions. Don't forget to insulate floors, crawlspaces, and around windows and doors.",
    "roofing": "Common residential roofing materials include asphalt shingles (20-30 year lifespan), metal (40-70 years), clay/concrete tile (50+ years), slate (100+ years), and various synthetic options. Selection factors include climate, roof pitch, structural support, aesthetics, and budget. Proper installation requires appropriate underlayment, flashing at all penetrations and transitions, and adequate ventilation to prevent moisture damage.",
    "windows": "Window selection factors include energy efficiency (look for ENERGY STAR ratings and low U-values), frame material (vinyl, wood, fiberglass, aluminum), style (double-hung, casement, sliding), glass type (double or triple pane), and local building code requirements. Proper installation with correct flashing and sealing is crucial to prevent water intrusion and air leakage.",
    "hvac": "HVAC (Heating, Ventilation, and Air Conditioning) systems should be properly sized using Manual J calculations. Oversized systems cycle too frequently, while undersized systems run constantly. Consider energy efficiency ratings (SEER for cooling, AFUE for heating), zoning options for temperature control in different areas, and indoor air quality components like filtration and ventilation. Regular maintenance is essential for optimal performance and longevity.",
    "painting": "Proper painting preparation includes cleaning surfaces, repairing damage, sanding, and priming. Use appropriate paints for each application: latex-based for most interior walls, oil or acrylic for trim, moisture-resistant for bathrooms and kitchens, and exterior-grade for outdoor surfaces. Quality matters—premium paints typically offer better coverage, durability, and washability, often making them more cost-effective in the long run.",
    "flooring": "Flooring options include hardwood (durable, adds value), engineered wood (more stable in humid conditions), laminate (budget-friendly, scratch-resistant), luxury vinyl (waterproof, easy maintenance), tile (ideal for wet areas), and carpet (comfortable but harder to clean). Consider the room's function, moisture exposure, traffic levels, maintenance requirements, and installation method when selecting flooring."
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
    
    # Extract city name from address if possible
    city_match = None
    
    # Try to identify city from address by looking for common patterns
    # Pattern 1: City before state (e.g., "Los Angeles, CA")
    city_state_pattern = re.search(r'([A-Za-z\s]+),\s*[A-Z]{2}', address)
    if city_state_pattern:
        potential_city = city_state_pattern.group(1).strip().lower()
        # Check if the potential city matches any of our location keys
        for key in LOCATIONS:
            if key != "default" and key in potential_city:
                city_match = key
                break
    
    # If we found a city match, use that location data
    if city_match:
        return LOCATIONS[city_match]
    
    # Otherwise check each location key against the full address
    for key in LOCATIONS:
        if key != "default" and key in address_lower:
            return LOCATIONS[key]
    
    # If no match found, use custom location data with the provided address
    # but keeping default coordinates for demo purposes
    custom_location = LOCATIONS["default"].copy()
    # We'll keep the original location's properties but update it with the user's address
    # This will be overridden in create_geojson_for_address anyway
    return custom_location

def create_geojson_for_address(address):
    """Create GeoJSON data for a given address"""
    # Instead of trying to match with predefined locations, we'll directly 
    # use coordinates for West Hills, CA for our demo application
    # These are the approximate coordinates for West Hills, CA
    lat = 34.2000  # West Hills latitude
    lon = -118.6100  # West Hills longitude
    
    # Create a small square (approximately 100x100 meters)
    delta = 0.001  # roughly 100 meters at most latitudes
    
    # Create GeoJSON with the user's address and demo property data
    geojson = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    # Use the user's exact address
                    "address": address,
                    "zone_type": "Residential R1",
                    "flood_zone": "X (Minimal Risk)",
                    "soil_type": "Sandy Loam",
                    "parcel_id": "WH-" + str(hash(address) % 10000000),
                    "lot_size": "8,500 sq ft",
                    "building_height_limit": "35 feet",
                    "setback_front": "20 feet",
                    "setback_rear": "15 feet",
                    "setback_sides": "5 feet"
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
    
    # Final check to absolutely ensure the address is set correctly
    geojson["features"][0]["properties"]["address"] = address
    
    return geojson

def get_best_matching_response(query):
    """Get the best matching response based on keywords in the query"""
    query = query.lower().strip()
    
    # Check for GIS/mapping/property related queries with an address
    # Improved address pattern matching - look for addresses in different formats
    address_patterns = [
        r"for ([\w\s,\.]+)$",  # "... for 123 Main St, City, State"
        r"([\d]+[\w\s,\.]+?)(?:\s+in\s+|$)",  # Starts with number: "123 Main St, City, State"
        r"address[:\s]+([\w\s,\.]+)(?:\s+in\s+|$)"  # "address: 123 Main St, City, State"
    ]
    
    if any(word in query for word in ["map", "gis", "flood zone", "flood data", "parcel", "property"]):
        # Try each address pattern
        address = None
        for pattern in address_patterns:
            address_match = re.search(pattern, query)
            if address_match:
                address = address_match.group(1).strip()
                logger.info(f"Extracted address: {address}")
                break
        
        if address:
            # Create GeoJSON with the extracted address
            logger.info(f"Creating GeoJSON for address: {address}")
            geojson = create_geojson_for_address(address)
            # Double-check that the address is set correctly in the output GeoJSON
            geojson["features"][0]["properties"]["address"] = address
            return json.dumps(geojson)
        else:
            # If no address was found in the query, do a direct pass-through of any address
            # that was provided as a separate parameter (common in the UI)
            direct_address_match = re.search(r'^\d+.*', query.strip())
            if direct_address_match:
                direct_address = query.strip()
                logger.info(f"Using direct address: {direct_address}")
                geojson = create_geojson_for_address(direct_address)
                # Double-check that the address is set correctly
                geojson["features"][0]["properties"]["address"] = direct_address
                return json.dumps(geojson)
            else:
                # Default GeoJSON if no address found
                logger.warning("No address found in query, using default")
                default_address = "123 Main Street, Any City, USA"
                return json.dumps(create_geojson_for_address(default_address))
    
    # Check for exact phrase matches first
    query_phrases = {
        "how do i measure": "measure backyard",
        "measuring": "measure backyard",
        "backyard measurement": "measure backyard",
        "how big": "measure backyard",
        "adu": "adu",
        "accessory dwelling unit": "adu",
        "granny flat": "adu",
        "in-law unit": "adu",
        "mother-in-law": "adu",
        "foundation": "foundation",
        "electrical": "electrical",
        "wiring": "electrical",
        "circuit": "electrical",
        "plumbing": "plumbing",
        "pipes": "plumbing",
        "water line": "plumbing",
        "insulation": "insulation",
        "insulate": "insulation",
        "r-value": "insulation",
        "roof": "roofing",
        "shingles": "roofing",
        "windows": "windows",
        "hvac": "hvac",
        "heating": "hvac",
        "air conditioning": "hvac",
        "ventilation": "hvac",
        "paint": "painting",
        "painting": "painting",
        "floor": "flooring",
        "flooring": "flooring"
    }
    
    # Check for phrase matches
    for phrase, topic in query_phrases.items():
        if phrase in query:
            logger.info(f"Phrase match found: '{phrase}' → {topic}")
            return SAMPLE_RESPONSES[topic]
    
    # Check for direct topic matches in our SAMPLE_RESPONSES
    for topic in SAMPLE_RESPONSES:
        if topic in query:
            # Direct topic match
            logger.info(f"Direct topic match found: {topic}")
            return SAMPLE_RESPONSES[topic]
    
    # More sophisticated keyword matching
    topic_scores = {}
    for topic, response in SAMPLE_RESPONSES.items():
        # Initialize score
        score = 0
        
        # Score each word in the query
        for word in query.split():
            # Exact matches are worth more
            if word == topic or word in topic.split():
                score += 3
            # Partial matches (word is part of topic or topic is part of word)
            elif word in topic or topic in word:
                score += 1
        
        if score > 0:
            topic_scores[topic] = score
    
    # If we found matches, return the highest scoring one
    if topic_scores:
        best_topic = max(topic_scores.items(), key=lambda x: x[1])[0]
        logger.info(f"Best keyword match: {best_topic} with score {topic_scores[best_topic]}")
        return SAMPLE_RESPONSES[best_topic]
    
    # Default response if no good matches found
    logger.info("No good matches found, returning default response")
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
        
        # Check for special case: GIS query with a direct address parameter
        # This is the format used by streamlit_app.py when calling process_gis_query
        if query.startswith("Provide flood zone and GIS data for "):
            address = query.replace("Provide flood zone and GIS data for ", "").strip()
            logger.info(f"Detected GIS query with address: {address}")
            # Create GeoJSON directly with the provided address
            geojson = create_geojson_for_address(address)
            # Ensure address is set correctly
            geojson["features"][0]["properties"]["address"] = address
            return json.dumps(geojson)
        
        # Get response based on query content for other query types
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