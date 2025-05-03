"""
Agent module wrapper for the Construction Research Assistant
This module ensures proper importing of the research_construction function
"""
import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import directly first
try:
    from agent import research_construction
    logger.info("Successfully imported agent module directly")
except ImportError:
    # If that fails, look for the module in the current directory explicitly
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    try:
        from agent import research_construction
        logger.info("Successfully imported agent module from current directory")
    except ImportError as e:
        logger.error(f"Failed to import agent module: {str(e)}")
        
        # As a fallback, define a simple mock function
        def research_construction(query):
            return (
                "Error: Unable to load the agent module. Please check that all files are "
                "in the correct location and the API keys are properly set."
            )
        
        logger.warning("Using mock research_construction function")

# Test if the function works
if __name__ == "__main__":
    test_query = "What are the zoning regulations for residential construction in Los Angeles?"
    result = research_construction(test_query)
    print(f"Result: {result}") 