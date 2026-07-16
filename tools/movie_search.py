from __future__ import annotations

import requests


API_URL = "https://itunes.apple.com/search"


def execute(arguments: dict) -> str:
    try:
        query = (arguments.get("query") or arguments.get("title") or "").strip()
        if not query:
            raise ValueError("Missing movie search query.")

        response = requests.get(
            API_URL,
            params={
                "term": query,
                "media": "movie",
                "limit": 5,
            },
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            return f'No movies found for "{query}".'

        lines = [f'Movie search results for "{query}":']
        for index, item in enumerate(results, start=1):
            title = item.get("trackName") or item.get("collectionName") or "Unknown title"
            release_date = item.get("releaseDate", "")
            year = release_date[:4] if release_date else "Unknown year"
            genre = item.get("primaryGenreName", "Unknown genre")
            view_url = item.get("trackViewUrl") or item.get("collectionViewUrl") or ""
            lines.append(f"{index}. {title} ({year}) - {genre}" + (f" - {view_url}" if view_url else ""))

        return "\n".join(lines)
    except Exception as error:
        return f"Movie Search Error: {error}"


if __name__ == "__main__":
    print(execute({"query": "Inception"}))