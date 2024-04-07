import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")


def search_knowledge_graph(query: str) -> dict[str, str]:
    """
    Search the Google Knowledge Graph for information related to the given query.

    Args:
        query: The query to search for in the Knowledge Graph.

    Returns:
        The extracted data from the Knowledge Graph, including the name, URL, and description.

    Raises:
        requests.exceptions.HTTPError: If there is an error in the HTTP request.
    """
    url = "https://kgsearch.googleapis.com/v1/entities:search"
    params = {
        "query": query,
        "key": API_KEY,
        "types": "AdministrativeArea",
        "languages": "de",
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    if "itemListElement" not in data or len(data["itemListElement"]) == 0:
        return {}

    extracted_data = {
        "name": data["itemListElement"][0]["result"].get("name", "Not found"),
        "url": data["itemListElement"][0]["result"].get("url", "Not found"),
    }
    if data["itemListElement"][0]["result"].get("detailedDescription", None):
        extracted_data["description"] = data["itemListElement"][0]["result"]["detailedDescription"].get(
            "articleBody", "Not found"
        )
    return extracted_data
