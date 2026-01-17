# backend/tools.py
from tavily import TavilyClient
from config import get_settings

def perform_market_search(query: str) -> str:
    """
    Searches the web for actionable financial data (rates, programs, resources).
    """
    settings = get_settings()
    if not settings.tavily_api_key:
        return "Search disabled (No API Key)."

    try:
        tavily = TavilyClient(api_key=settings.tavily_api_key)
        # We ask for 'advanced' search to get serious financial sources
        response = tavily.search(
            query=query, 
            search_depth="basic", 
            max_results=3,
            include_domains=["nerdwallet.com", "canada.ca", "investopedia.com", "reddit.com"] 
        )
        
        # Format the results into a bulleted string for the LLM
        results = []
        for res in response.get("results", []):
            results.append(f"- {res['title']}: {res['content']} (Source: {res['url']})")
        
        return "\n".join(results)
    except Exception as e:
        return f"Search failed: {str(e)}"