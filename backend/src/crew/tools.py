from datetime import datetime
from crewai.tools import tool
from duckduckgo_search import DDGS


@tool("Get Current Datetime")
async def get_current_datetime():
    """
    Get the current date and time.
    Useful when you need to know the current time or date to answer a question.
    Returns:
        str: The current date and time in YYYY-MM-DD HH:MM:SS format.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

@tool("Web Search")
async def web_search(query: str):
    """
    Search the web for information using DuckDuckGo.
    Useful for finding up-to-date information, news, or specific facts.
    Args:
        query (str): The search query string.
    """
    try:
        results = DDGS().text(keywords=query, max_results=5)
        return results
    except Exception as e:
        return f"Error performing web search: {str(e)}"

def get_tools():
    return [get_current_datetime, web_search]