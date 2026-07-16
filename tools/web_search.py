from __future__ import annotations

import html
import os
import re
from typing import Any
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

import requests


GOOGLE_SEARCH_URL = "https://www.google.com/search"
GOOGLE_CSE_URL = "https://www.googleapis.com/customsearch/v1"
DEFAULT_TIMEOUT = 10


def _strip_html_tags(text: str) -> str:
    without_tags = re.sub(r"<[^>]+>", "", text)
    return html.unescape(without_tags).strip()


def _extract_google_result_url(raw_href: str) -> str:
    if raw_href.startswith("/url?"):
        parsed = urlparse(raw_href)
        query_data = parse_qs(parsed.query)
        candidate = query_data.get("q", [""])[0] or query_data.get("url", [""])[0]
        return unquote(candidate)

    if raw_href.startswith("http://") or raw_href.startswith("https://"):
        return raw_href

    return ""


def _is_valid_result_url(url: str) -> bool:
    if not url:
        return False

    blocked_domains = (
        "google.com",
        "webcache.googleusercontent.com",
        "accounts.google.com",
    )

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if any(domain in host for domain in blocked_domains):
        return False

    return parsed.scheme in {"http", "https"}


def google_search(query: str, limit: int = 5) -> list[dict[str, Any]]:
    if not query.strip():
        raise ValueError("Missing web search query.")

    cse_results = _search_google_via_cse(query, limit)
    if cse_results:
        return cse_results

    response = requests.get(
        GOOGLE_SEARCH_URL,
        params={
            "q": query,
            "num": max(1, min(limit * 2, 10)),
            "hl": "en",
            "gbv": "1",
        },
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0.0.0 Safari/537.36"
            )
        },
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()

    results = _parse_google_html(response.text, limit)
    if results:
        return results

    try:
        return _search_google_via_jina(query, limit)
    except Exception:
        return []


def _search_google_via_cse(query: str, limit: int) -> list[dict[str, Any]]:
    api_key = os.getenv("GOOGLE_CSE_API_KEY", "").strip()
    cx = os.getenv("GOOGLE_CSE_CX", "").strip()

    if not api_key or not cx:
        return []

    response = requests.get(
        GOOGLE_CSE_URL,
        params={
            "key": api_key,
            "cx": cx,
            "q": query,
            "num": max(1, min(limit, 10)),
        },
        timeout=DEFAULT_TIMEOUT,
    )
    response.raise_for_status()

    data = response.json()
    items = data.get("items", [])

    results: list[dict[str, Any]] = []
    for item in items[:limit]:
        title = (item.get("title") or "").strip()
        url = (item.get("link") or "").strip()
        if not title or not _is_valid_result_url(url):
            continue
        results.append({"title": title, "url": url})

    return results


def _parse_google_html(html_doc: str, limit: int) -> list[dict[str, Any]]:
    anchors = re.findall(r"<a[^>]+href=['\"]([^'\"]+)['\"][^>]*>(.*?)</a>", html_doc, flags=re.IGNORECASE | re.DOTALL)

    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for raw_href, raw_anchor in anchors:
        url = _extract_google_result_url(raw_href)
        if not _is_valid_result_url(url) or url in seen:
            continue

        title = _strip_html_tags(raw_anchor)
        if not title:
            continue

        seen.add(url)
        results.append({"title": title, "url": url})

        if len(results) >= limit:
            break

    return results


def _search_google_via_jina(query: str, limit: int) -> list[dict[str, Any]]:
    mirror_url = f"https://r.jina.ai/http://www.google.com/search?q={quote_plus(query)}"
    response = requests.get(mirror_url, timeout=DEFAULT_TIMEOUT)
    response.raise_for_status()

    matches = re.findall(r"\[([^\]]+)\]\((https?://[^)]+)\)", response.text)
    results: list[dict[str, Any]] = []
    seen: set[str] = set()

    for title, url in matches:
        clean_url = url.strip()
        if not _is_valid_result_url(clean_url) or clean_url in seen:
            continue

        seen.add(clean_url)
        results.append({"title": title.strip(), "url": clean_url})
        if len(results) >= limit:
            break

    return results


def execute(arguments: dict[str, Any]) -> str:
    query = (arguments.get("query") or "").strip()
    limit = int(arguments.get("limit", 5))

    if not query:
        return "Web Search Error: Missing search query."

    try:
        results = google_search(query, limit=limit)
    except Exception as error:
        return f"Web Search Error: {error}"

    if not results:
        return f'No web results found for "{query}".'

    lines = [f'Google search results for "{query}":']
    for index, item in enumerate(results, start=1):
        lines.append(f"{index}. {item['title']} - {item['url']}")

    return "\n".join(lines)


if __name__ == "__main__":
    print(execute({"query": "Inception movie"}))