from __future__ import annotations

import requests


API_URL = "https://openlibrary.org/search.json"


def execute(arguments: dict) -> str:
    try:
        query = (arguments.get("query") or arguments.get("title") or arguments.get("author") or "").strip()
        if not query:
            raise ValueError("Missing book search query.")

        response = requests.get(
            API_URL,
            params={
                "q": query,
                "limit": 5,
            },
            timeout=10,
        )
        response.raise_for_status()

        data = response.json()
        docs = data.get("docs", [])

        if not docs:
            return f'No books found for "{query}".'

        lines = [f'Book search results for "{query}":']
        for index, item in enumerate(docs[:5], start=1):
            title = item.get("title") or "Unknown title"
            authors = ", ".join(item.get("author_name", [])[:3]) if item.get("author_name") else "Unknown author"
            year = item.get("first_publish_year", "Unknown year")
            publisher = ", ".join(item.get("publisher", [])[:2]) if item.get("publisher") else ""
            key = item.get("key", "")
            url = f"https://openlibrary.org{key}" if key else ""
            line = f"{index}. {title} - {authors} - {year}"
            if publisher:
                line += f" - {publisher}"
            if url:
                line += f" - {url}"
            lines.append(line)

        return "\n".join(lines)
    except Exception as error:
        return f"Book Search Error: {error}"


if __name__ == "__main__":
    print(execute({"query": "Atomic Habits"}))