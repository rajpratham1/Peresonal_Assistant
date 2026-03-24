from duckduckgo_search import DDGS

def search_web(query: str, max_results: int = 3) -> str:
    """Performs a live search on DuckDuckGo and returns formatted results."""
    try:
        with DDGS() as ddgs:
            results = [r for r in ddgs.text(query, max_results=max_results)]
            if not results:
                return f"No live search results found for '{query}'."
            
            output = [f"Search results for '{query}':"]
            for i, r in enumerate(results, 1):
                output.append(f"{i}. {r.get('title')}: {r.get('body')} (URL: {r.get('href')})")
            return "\n".join(output)
    except Exception as e:
        return f"Web search failed: {e}"

if __name__ == "__main__":
    print(search_web("latest news about Space X"))
