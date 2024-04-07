import os
from operator import itemgetter

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableLambda
from langchain_openai.chat_models import ChatOpenAI
from prompts.google_search import FINAL_WEB_ANALYSIS_PROMPT

from data_sources.web_search.google_knowledge_graph import search_knowledge_graph
from data_sources.web_search.google_web_search import google_web_search
from data_sources.web_search.individual_analysis_agent import (
    run_individual_analysis_agent,
)

OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_SMART_LLM = os.getenv("OPENAI_SMART_LLM")

llm = ChatOpenAI(organization=OPENAI_ORG_ID, model=OPENAI_SMART_LLM, temperature=0)


def combine_individual_analyses(individual_analysis: list[str]) -> str:
    """
    Combine individual analyses into a single string.

    Args:
        individual_analysis: List of individual analysis.

    Returns:
        Combined analyses.
    """
    return "\n\n".join(individual_analysis)


def analyze_each_search(_dict) -> list[str]:
    """
    Analyze each search result.

    Args:
        _dict: A dictionary containing search results and context.

    Returns:
        A list of analyses.
    """

    indi_analyses = [
        run_individual_analysis_agent(
            str({"search_result": result, "context": _dict["context"]})
        )
        for result in _dict["search_results"]
    ]
    return combine_individual_analyses(indi_analyses)


def create_search_analysis_chain(search_results):
    """
    Create a chain for generating a search analysis.

    The chain uses an agent to generate individual analyses and then combines them
    into a final analysis.

    Args:
        search_results: A list of search results.

    Returns:
        A LangChain Runnable for generating a search analysis.
    """
    template = FINAL_WEB_ANALYSIS_PROMPT
    prompt = ChatPromptTemplate.from_template(template)

    chain = (
        {
            "analyses": {
                "search_results": itemgetter("search_results"),
                "context": itemgetter("context"),
            }
            | RunnableLambda(analyze_each_search),
            "context": itemgetter("context"),
        }
        | prompt
        | llm
    )
    return chain


async def run_search_analysis_chain(
    raw_search_results: list[str], place_context: str
) -> str:
    """
    Run a search analysis chain.

    Args:
        raw_search_results: A list of raw search results.
        place_context: The context of the place.

    Returns:
        A search analysis.
    """
    search_analysis_chain = create_search_analysis_chain(raw_search_results)
    return await search_analysis_chain.ainvoke(
        {"search_results": raw_search_results, "context": place_context}
    )


async def create_search_engine_analysis(place: dict[str]) -> str:
    """
    Create a search engine analysis.

    Args:
        place: A dictionary containing place information.

    Returns:
        A search engine analysis.
    """
    place_context = search_knowledge_graph(place["name"])
    search_queries = [
        "Klimaschutzmanager",
        "(Kriterienkatalog OR Standortkonzept) (FFPV OR PV-FFA OR Freiflächenphotovoltaik)",
        "Flächennutzungsplan",
        "FFPV or PV-FFA",
    ]
    raw_search_results = []

    if place_context.get("URL"):
        raw_search_results = run_restricted_search(
            place, search_queries, place_context.get("URL")
        )
    raw_search_results += run_general_search(place, search_queries)

    response = await run_search_analysis_chain(raw_search_results, str(place_context))
    return response.content


def run_general_search(place: dict[str], search_queries: list[str]) -> list[str]:
    """
    Run an unrestricted search on a set of search queries.

    Args:
        place: The place to search for.
        search_queries: A list of search queries.

    Returns:
        A list of raw search results.
    """
    raw_search_results = []
    for instruction in search_queries:
        raw_search_results.append(
            google_web_search(instruction + " " + place["name"])
            | {"target": instruction}
        )

    return raw_search_results


def run_restricted_search(
    place: dict[str], search_queries: list[str], url: str
) -> list[str]:
    """
    Run a restricted search on a set of search queries.

    Args:
        place: The place to search for.
        search_queries: A list of search queries.
        url: The URL to restrict the search to.

    Returns:
        A list of raw search results.
    """
    raw_search_results = []
    for instruction in search_queries:
        raw_search_results.append(
            google_web_search(
                instruction + " " + place["name"],
                restrict_to_site=url,
            )
            | {"target": instruction}
        )

    return raw_search_results
