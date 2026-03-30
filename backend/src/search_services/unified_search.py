from pydantic_ai import RunContext
from src.app_config import app_config
from src.search_services.exa_search import ExaSearch


class UnifiedSearch:
    def __init__(self, exa_api_key: str = None):
        self.exa_api_key = exa_api_key or app_config.EXA_API_KEY
        self.exa_search = ExaSearch(self.exa_api_key)

    def get_search_tools(self):
        return [
            self.search,
            self.extract,
            self.create_research_task,
            self.get_research_task_result,
        ]

    async def search(
        self,
        ctx: RunContext,
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        days: int = 3,
        max_results: int = 5,
    ) -> str:
        """
        Search the web for real-time information, news, and facts.
        Use this for general questions or finding specific information from the web.
        """
        return await self.exa_search.search(
            query=query,
            search_depth=search_depth,
            topic=topic,
            days=days,
            max_results=max_results,
        )

    async def extract(
        self,
        ctx: RunContext,
        urls: list[str] | str,
        extract_depth: str = "basic",
        query: str = None,
        chunks_per_source: int = None,
    ) -> str:
        """
        Extract clean content and structured data from one or more URLs.
        Use this when you have specific links and want to read their full content.
        """
        return await self.exa_search.extract(
            urls=urls,
            extract_depth=extract_depth,
            query=query,
            chunks_per_source=chunks_per_source,
        )

    async def create_research_task(
        self, ctx: RunContext, input: str, model: str = "auto"
    ) -> str:
        """
        Start a deep research task on a complex topic.
        This provides a comprehensive report instead of just snippets.
        It returns a request_id which must be used with get_research_task_result to see the final report.
        """
        return await self.exa_search.create_research_task(input=input, model=model)

    async def get_research_task_result(self, ctx: RunContext, request_id: str) -> str:
        """
        Retrieve the final results of a research task using its request_id.
        Call this after create_research_task and a short wait (15-30s).
        """
        return await self.exa_search.get_research_task_result(request_id=request_id)
