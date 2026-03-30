import json

from exa_py import Exa


class ExaSearch:
    def __init__(self, api_key: str):
        self.client = Exa(api_key=api_key)

    async def search(
        self,
        query: str,
        search_depth: str = "basic",
        topic: str = "general",
        days: int = 3,
        max_results: int = 5,
    ) -> str:
        """Search the web using Exa."""
        try:
            # Map search_depth to content length
            max_characters = 500 if search_depth == "basic" else 1500

            response = self.client.search_and_contents(
                query,
                type="auto",
                num_results=max_results,
                text={"max_characters": max_characters},
            )

            results = []
            for r in response.results:
                results.append(
                    {
                        "title": r.title,
                        "url": r.url,
                        "content": r.text,
                        "published_date": getattr(r, "published_date", None),
                    }
                )

            return json.dumps({"results": results}, indent=2)
        except Exception as e:
            return f"Error performing Exa search: {str(e)}"

    async def extract(
        self,
        urls: list[str] | str,
        extract_depth: str = "basic",
        query: str = None,
        chunks_per_source: int = None,
    ) -> str:
        """Extract content from URLs using Exa."""
        try:
            if isinstance(urls, str):
                urls = [urls]

            response = self.client.get_contents(
                urls,
                text=True,
            )

            results = []
            for r in response.results:
                results.append(
                    {
                        "url": r.url,
                        "title": r.title,
                        "content": r.text,
                    }
                )

            return json.dumps({"results": results}, indent=2)
        except Exception as e:
            return f"Error performing Exa extract: {str(e)}"

    async def create_research_task(self, input: str, model: str = "auto") -> str:
        """
        Exa doesn't have a native async research task mechanism like Tavily.
        We perform a deep search synchronously and return results directly.
        The 'request_id' returned is a placeholder; call get_research_task_result with it.
        """
        try:
            response = self.client.search_and_contents(
                input,
                type="auto",
                num_results=10,
                text={"max_characters": 2000},
            )

            results = []
            for r in response.results:
                results.append(
                    {
                        "title": r.title,
                        "url": r.url,
                        "content": r.text,
                    }
                )

            # Store result in instance for retrieval
            self._last_research = results
            # Return a fake request_id so the workflow stays compatible
            return json.dumps(
                {"request_id": "exa-research-completed", "status": "completed"},
                indent=2,
            )
        except Exception as e:
            return f"Error performing Exa research: {str(e)}"

    async def get_research_task_result(self, request_id: str) -> str:
        """Retrieve the stored research results."""
        try:
            results = getattr(self, "_last_research", [])
            return json.dumps({"results": results, "status": "completed"}, indent=2)
        except Exception as e:
            return f"Error retrieving Exa research result: {str(e)}"
