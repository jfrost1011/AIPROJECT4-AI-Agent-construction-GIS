import subprocess
import sys

def check_and_install_packages():
    """Check and install required packages if they're not already installed."""
    required_packages = [
        "python-dotenv",
        "streamlit",
        "streamlit-folium",
        "folium",
        "geopandas",
        "langchain",
        "langchain-openai",
        "openai",
        "tavily-python",
        "requests"
    ]
    
    print("Checking and installing required packages...")
    
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} is already installed")
        except ImportError:
            print(f"⚠️ Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✅ {package} installed successfully")

if __name__ == "__main__":
    check_and_install_packages()
    print("All packages checked and installed successfully!") 