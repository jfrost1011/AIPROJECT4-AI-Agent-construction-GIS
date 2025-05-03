from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, AgentType
from langchain.agents import Tool
from langchain_community.tools.tavily_search import TavilySearchResults
from config import OPENAI_API_KEY, TAVILY_API_KEY
from gis_tool import fetch_parcel_data

# Initialize OpenAI LLM
llm = ChatOpenAI(api_key=OPENAI_API_KEY, model="gpt-4o", temperature=0)

# Initialize Tavily WebSearch Tool
search_tool = TavilySearchResults(api_key=TAVILY_API_KEY)

# Define GIS tool for agent
gis_tool = Tool(
    name="GIS_Parcel_Info",
    func=fetch_parcel_data,
    description="Fetches GIS parcel, zoning, and flood zone data based on an address. Input should be a complete address string like '123 Main St, City, State'. Returns detailed geographic information including flood zones."
)

# Set up agent with tools
tools = [search_tool, gis_tool]

agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

def research_construction(query):
    response = agent.run(query)
    return response

if __name__ == "__main__":
    query = input("Enter your construction-related query:\n> ")
    result = research_construction(query)
    print("\n🔍 Agent Response:\n", result) 