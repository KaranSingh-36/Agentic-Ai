from __future__ import annotations

from web_search import google_search


def execute(arguments: dict) -> str:
    try:
        query = (arguments.get("query") or arguments.get("title") or arguments.get("artist") or "").strip()
        if not query:
            raise ValueError("Missing music search query.")

        results = google_search(f"{query} song music", limit=5)

        if not results:
            return f'No music tracks found for "{query}".'

        lines = [f'Music search results for "{query}":']
        for index, item in enumerate(results, start=1):
            title = item.get("title", "Unknown result")
            view_url = item.get("url", "")
            lines.append(f"{index}. {title}" + (f" - {view_url}" if view_url else ""))

        return "\n".join(lines)
    except Exception as error:
        return f"Music Search Error: {error}"


if __name__ == "__main__":
    print(execute({"query": "Shape of You"}))