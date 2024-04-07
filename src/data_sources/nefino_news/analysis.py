import os
from operator import itemgetter

from dotenv import load_dotenv
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langchain_openai.chat_models import ChatOpenAI
from prompts.news import (
    BASIC_NEWS_PROMPT,
)
from utility.database import establish_clickhouse_connection

load_dotenv(verbose=True)
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_SMART_LLM = os.getenv("OPENAI_SMART_LLM")
llm = ChatOpenAI(organization=OPENAI_ORG_ID, model=OPENAI_SMART_LLM, temperature=0)


def create_news_analysis_chain() -> Runnable:
    """
    Creates a chain for generating a news analysis.

    Returns:
        A LangChain Runnable.
    """
    prompt = ChatPromptTemplate.from_template(BASIC_NEWS_PROMPT)
    vs = establish_clickhouse_connection()
    retriever = vs.as_retriever()

    chain = {
        "context": itemgetter("question") | retriever,
        "place": itemgetter("place"),
    } | prompt | llm
    return chain


async def create_news_analysis(place: dict[str] = None) -> str:
    """
    Creates a news analysis for a given place.

    Args:
        place: A dictionary containing place information.

    Returns:
        A string containing the news analysis.
    """
    ChatPromptTemplate.from_template(BASIC_NEWS_PROMPT)
    search_query = str(
        f'Kriterienkatalog, Flächennutzungsplan, Klimaschutzmanager, Standortkonzept in {place["name"]} {place["id"]}'
    )

    chain = create_news_analysis_chain()
    news_analysis = await chain.ainvoke(
        input={"question": search_query, "place": place["name"]}
    )
    return news_analysis
