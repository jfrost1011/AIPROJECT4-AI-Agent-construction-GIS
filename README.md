# AI-Powered Construction Research Assistant

A Streamlit web application that combines AI capabilities with GIS mapping to assist construction professionals with research and property analysis.

## Features

- **AI-powered research assistant** for construction-related queries
- **GIS mapping integration** for property analysis
- **Flood zone data** visualization
- **Interactive maps** using Folium

## Prerequisites

- Python 3.7+
- OpenAI API key
- Tavily API key (for web search functionality)

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/yourusername/aiproject4-ai-agent-construction-gis.git
   cd aiproject4-ai-agent-construction-gis
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set up environment variables:
   
   Create a `.env` file in the project root with the following variables:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   TAVILY_API_KEY=your_tavily_api_key_here
   ```

   Or, set them as environment variables in your system.

## Running the App

Start the Streamlit app by running:
```bash
streamlit run streamlit_app.py
```

The app will be available at http://localhost:8501

## Using the App

### General Construction Queries
1. Select "General Construction Query" from the dropdown
2. Enter your construction-related question
3. Click "Get Agent Response" to receive an AI-powered answer

### GIS Mapping Queries
1. Select "GIS Mapping Query" from the dropdown
2. Enter a property address
3. Click "Fetch GIS Data" to view flood zone information and other GIS data
4. Explore the interactive map and raw data output

## Deploying to Streamlit Cloud

1. Push your code to GitHub
2. Create a new app on [Streamlit Cloud](https://share.streamlit.io/)
3. Connect to your GitHub repository
4. Set the required environment variables in Streamlit Cloud's secrets management

## Troubleshooting

If you encounter any issues with missing packages, the app will attempt to install them automatically. If problems persist, try:

```bash
pip install python-dotenv streamlit-folium folium geopandas langchain langchain-openai openai tavily-python
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [OpenAI](https://openai.com/) for the AI capabilities
- [Streamlit](https://streamlit.io/) for the web application framework
- [Folium](https://python-visualization.github.io/folium/) for interactive maps
- [GeoPandas](https://geopandas.org/) for geospatial data processing 