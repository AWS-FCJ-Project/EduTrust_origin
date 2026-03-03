import json

from src.app_config import app_config
from tavily import AsyncTavilyClient


class TavilySearch:
    def __init__(self, api_key: str):
        self.client = AsyncTavilyClient(api_key=api_key)

    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        days: int = 3,
        max_results: int = 5,
    ) -> str:
        try:
            kwargs = {
                "query": query,
                "search_depth": search_depth,
                "topic": topic,
                "days": days,
                "max_results": max_results,
            }
            response = await self.client.search(**kwargs)
            return json.dumps(response, indent=2)
        except Exception as e:
            return f"Error performing Tavily search: {str(e)}"

    async def extract(
        self,
        urls: list[str] | str,
        extract_depth: str = "basic",
        query: str = None,
        chunks_per_source: int = None,
    ) -> str:
        try:
            kwargs = {
                "urls": urls,
                "extract_depth": extract_depth,
            }
            if query:
                kwargs["query"] = query
            if chunks_per_source:
                kwargs["chunks_per_source"] = chunks_per_source

            response = await self.client.extract(**kwargs)
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error performing Tavily extract: {str(e)}"

    async def create_research_task(self, input: str, model: str = "auto") -> str:
        try:
            kwargs = {
                "input": input,
                "model": model,
            }

            response = await self.client.research(**kwargs)
            return json.dumps(response, indent=2)

        except Exception as e:
            return f"Error performing Tavily research: {str(e)}"

    async def get_research_task_result(
        self,
        request_id: str,
    ) -> str:
        try:
            response = await self.client.get_research(request_id=request_id)
            return json.dumps(response, indent=2)
        except Exception as e:
            return f"Error performing Tavily research: {str(e)}"
