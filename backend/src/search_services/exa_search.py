import asyncio
import functools
import hashlib
import json
import time

from exa_py import Exa


class ExaSearch:
    def __init__(self, api_key: str):
        self.client = Exa(api_key=api_key)

    async def _run_sync(self, fn, *args, **kwargs):
        """Run a synchronous Exa call in a thread pool."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, functools.partial(fn, *args, **kwargs))

    async def search(
        self,
        query: str,
        search_depth: str = "basic",  # Not mapping directly to Exa yet
        topic: str = "general",
        days: int = 3,
        max_results: int = 5,
    ) -> str:
        """Search the web using Exa."""
        try:
            # Based on user-provided code pattern
            response = await self._run_sync(
                self.client.search,
                query,
                num_results=max_results,
                type="auto",
                contents={"text": True},
            )

            results = []
            for item in response.results:
                results.append(
                    {
                        "title": getattr(item, "title", ""),
                        "url": getattr(item, "url", ""),
                        "text": getattr(item, "text", ""),
                        "published_date": getattr(item, "published_date", None),
                        "author": getattr(item, "author", None),
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
        """Extract clean content from one or more URLs using Exa."""
        try:
            if isinstance(urls, str):
                urls = [urls]

            response = await self._run_sync(self.client.get_contents, urls, text=True)

            results = []
            for item in response.results:
                results.append(
                    {
                        "url": getattr(item, "url", ""),
                        "title": getattr(item, "title", ""),
                        "text": getattr(item, "text", ""),
                    }
                )
            return json.dumps({"results": results}, indent=2)
        except Exception as e:
            return f"Error performing Exa extract: {str(e)}"

    async def create_research_task(self, input: str, model: str = "auto") -> str:
        """Start a research task using Exa search."""
        try:
            response = await self._run_sync(
                self.client.search,
                input,
                num_results=10,
                type="auto",
                contents={"text": True},
            )

            results = []
            for item in response.results:
                results.append(
                    {
                        "title": getattr(item, "title", ""),
                        "url": getattr(item, "url", ""),
                        "text": getattr(item, "text", ""),
                        "published_date": getattr(item, "published_date", None),
                    }
                )

            request_id = hashlib.md5(f"{input}{time.time()}".encode()).hexdigest()

            return json.dumps(
                {"request_id": request_id, "status": "completed", "results": results},
                indent=2,
            )
        except Exception as e:
            return f"Error performing Exa research: {str(e)}"

    async def get_research_task_result(self, request_id: str) -> str:
        """Exa search is synchronous; return a static status message."""
        return json.dumps(
            {
                "request_id": request_id,
                "status": "completed",
                "message": (
                    "Exa research results are returned immediately in the 'create_research_task' call."
                ),
            },
            indent=2,
        )
