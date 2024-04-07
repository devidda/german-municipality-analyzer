import os
from typing import Any

from dotenv import load_dotenv
from langchain import hub
from langchain.agents import (
    AgentExecutor,
    BaseMultiActionAgent,
    create_openai_tools_agent,
    load_tools,
)
from langchain.chains.combine_documents.stuff import StuffDocumentsChain
from langchain.chains.llm import LLMChain
from langchain.text_splitter import TokenTextSplitter
from langchain.tools import BaseTool, StructuredTool
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_openai.chat_models import ChatOpenAI
from prompts.google_search import AGENT_INSTRUCTIONS, SUMMARY_PROMPT
from utility.web_scraping import Scraper

load_dotenv()
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_SMART_LLM = os.getenv("OPENAI_SMART_LLM")
OPENAI_FAST_LLM = os.getenv("OPENAI_FAST_LLM")

smart_llm = ChatOpenAI(
    organization=OPENAI_ORG_ID, model=OPENAI_SMART_LLM, temperature=0
)
fast_llm = ChatOpenAI(organization=OPENAI_ORG_ID, model=OPENAI_FAST_LLM, temperature=0)

llm = fast_llm

# Basic prompt setup without content from https://smith.langchain.com/hub/hwchase17/openai-tools-agent/c1867281
indi_template = hub.pull("hwchase17/openai-tools-agent:c1867281")


def run_scraper(urls: list[str]) -> list[dict[str, str]]:
    """
    Run the web scraper on the given URLs.

    Args:
        urls: A list of URLs to scrape.

    Returns:
        The scraped data.
    """

    scraper = Scraper(urls)
    scraped_contents = scraper.run()

    # Summarize if more than 5000 characters
    shortened_contents = []
    for scraped in scraped_contents:
        if len(scraped["raw_content"]) > 5000:

            text_splitter = TokenTextSplitter(chunk_size=1024, chunk_overlap=100)
            splitted_content = text_splitter.split_documents(
                [Document(scraped["raw_content"])]
            )

            prompt = PromptTemplate.from_template(SUMMARY_PROMPT)
            llm_chain = LLMChain(llm=llm, prompt=prompt)
            summarizer_chain = StuffDocumentsChain(
                llm_chain=llm_chain, document_variable_name="text"
            )
            shortened_contents.append(
                {
                    "url": scraped["url"],
                    "content": summarizer_chain.run(splitted_content),
                }
            )
        else:
            shortened_contents.append(scraped)
    return shortened_contents


def report(thoughts: str, fazit: str) -> str:
    """
    Function for getting the structure for an LLM Tool.
    """
    return fazit


def get_tools() -> list[BaseTool]:
    """
    Get the tools for the agent.

    Returns:
        A list of tools.
    """
    scrape_urls = StructuredTool.from_function(
        func=run_scraper,
        name="scrape_urls",
        description="A tool for scraping Websites and PDFs. You may ONLY use it if you DO NOT understand a search result and need further information its the website or PDF. Input URLs would need to be valid.",
    )
    submit_report = StructuredTool.from_function(
        func=report,
        name="submit_report",
        description="A tool to submit the final report. It should be called as the last step. If you decide that the search was not successful, you should submit a one liner report in the fazit with a negative conclusion like: 'The search did not yield relevant information for <meaning of keywords> in <place>.'",
    )
    return load_tools(["google-search"]) + [scrape_urls, submit_report]


def create_indi_report_agent() -> BaseMultiActionAgent:
    """
    Create an agent for generating a search report fopr an individual search result.

    The agent is able to trigger web scraping of sub search results. After he has
    all information he needs, he returnes an report for that search query.

    Args:
        search_results: A list of search results.

    Returns:
        A LangChain Runnable for generating a search report.
    """
    indi_template.messages[0].prompt.template = AGENT_INSTRUCTIONS

    agent = create_openai_tools_agent(llm, get_tools(), indi_template)
    return agent


def run_individual_analysis_agent(input: Any) -> str:
    """
    Run the individual analysis agent.

    Args:
        input: The input for the agent.

    Returns:
        The generated report for a single web search result.
    """
    input = str(input)
    agent = create_indi_report_agent()
    # Create an agent executor by passing in the agent and tools
    agent_executor = AgentExecutor(agent=agent, tools=get_tools())
    for step in agent_executor.iter({"input": input}):
        if output := step.get("intermediate_step"):
            action, value = output[0]
            if action.tool == "submit_report":
                return value
    return "Error submitting report."
