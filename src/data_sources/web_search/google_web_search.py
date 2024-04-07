import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv(
    "GOOGLE_CSE_ID"
)  # https://programmablesearchengine.google.com/controlpanel/all


def google_web_search(query: str, restrict_to_site: str = None) -> dict:
    """
    Perform a web search using the Google Custom Search API.

    Args:
        query: The search query.
        restrict_to_site: A website to restrict the search to.

    Returns:
        Extracted search results.
    """
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": API_KEY,
        "cx": GOOGLE_CSE_ID,
        "gl": "de",
        "hl": "de",
        "q": query,
        "num": 4,
    }

    # Restrict the search to a specific website
    if restrict_to_site:
        params["siteSearch"] = restrict_to_site
        params["siteSearchFilter"] = "i"

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if "items" not in data:
        extracted_results = []
    else:
        results = data["items"]
        extracted_results = [
            {
                "title": result["title"],
                "displayLink": result["link"],
                "snippet": result["snippet"],
                "site_restricted": restrict_to_site if restrict_to_site else False,
            }
            for result in results
        ]

    extracted_data = {
        "query": data["queries"]["request"][0]["searchTerms"],
        "results": extracted_results,
    }
    return extracted_data
