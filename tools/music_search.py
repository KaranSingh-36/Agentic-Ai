from __future__ import annotations

import requests


API_URL = "https://itunes.apple.com/search"


def execute(arguments: dict) -> str:
    try:
        query = (arguments.get("query") or arguments.get("title") or arguments.get("artist") or "").strip()
        if not query:
            raise ValueError("Missing music search query.")

        response = requests.get(
            API_URL,
            params={
                "term": query,
                "media": "music",
                "limit": 5,
            },
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            return f'No music tracks found for "{query}".'

        lines = [f'Music search results for "{query}":']
        for index, item in enumerate(results, start=1):
            track = item.get("trackName") or item.get("collectionName") or "Unknown track"
            artist = item.get("artistName", "Unknown artist")
            album = item.get("collectionName", "Unknown album")
            genre = item.get("primaryGenreName", "Unknown genre")
            release_date = item.get("releaseDate", "")
            year = release_date[:4] if release_date else "Unknown year"
            view_url = item.get("trackViewUrl") or item.get("collectionViewUrl") or ""
            lines.append(
                f"{index}. {track} - {artist} - {album} ({year}) - {genre}"
                + (f" - {view_url}" if view_url else "")
            )

        return "\n".join(lines)
    except Exception as error:
        return f"Music Search Error: {error}"


if __name__ == "__main__":
    print(execute({"query": "Shape of You"}))