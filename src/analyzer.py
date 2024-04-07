import asyncio
import os
from enum import Enum

import streamlit as st
from data_sources.nefino_news.analysis import create_news_analysis
from data_sources.web_search.analysis import create_search_engine_analysis
from dotenv import load_dotenv
from langchain.output_parsers import JsonOutputToolsParser
from langchain.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from prompts.evaluation import ANALYSIS_EVALUATION_PROMPT
from utility.places import validate_place_id

load_dotenv(verbose=True)
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_SMART_LLM = os.getenv("OPENAI_SMART_LLM")
llm = ChatOpenAI(organization=OPENAI_ORG_ID, model=OPENAI_SMART_LLM, temperature=0)


# Step 1: Create a combined analysis from Nefino LI News and Google Search
async def generate_combined_analysis(place: dict[str, str]) -> str:
    """
    Create a combined analysis from Nefino LI News and Google Search.

    Args:
        place: A dictionary containing place information.

    Returns:
        A string that represents the combined analysis.
    """
    # validate place
    validate_place_id(place["id"])

    # gather infos from Nefino LI News
    news_analysis_future = asyncio.create_task(create_news_analysis(place))

    # gather infos from Google Search
    search_engine_analysis_future = asyncio.create_task(
        create_search_engine_analysis(place)
    )

    # Wait for both tasks to complete
    news_analysis, web_analysis = await asyncio.gather(
        news_analysis_future, search_engine_analysis_future
    )

    # combine analyses
    combined_analyses = f"First Analysis based on Newspaper-News:\n{news_analysis.content}\n\nSecond Analysis based on detailed Web Searches:\n{web_analysis}"
    return place, combined_analyses


# Step 2: Evaluate the combined analyses
class EvaluationLabel(str, Enum):
    NEGATIVE = "negative"
    POTENTIALLY_POSITIVE = "potentially positive"
    VERY_POSITIVE = "very positive"


def llm_evaluation_function(
    CF1: str,
    CF2: str,
    CF3: str,
    CF4: str,
    CF5: str,
    concise_thoughts: str,
    attitude_label: EvaluationLabel,
) -> dict[str, str]:
    pass


def create_analyses_evaluation_chain():
    """
    Create a analysis evaluation chain.

    Returns:
        A LangChain Runnable.
    """
    submit_evaluation = StructuredTool.from_function(
        func=llm_evaluation_function,
        name="submit_evaluation",
        description="For the atttitude classification.",
    )
    prompt = ChatPromptTemplate.from_template(ANALYSIS_EVALUATION_PROMPT)

    return (
        {"analyses": RunnablePassthrough()}
        | prompt
        | llm.bind_tools(tools=[submit_evaluation], tool_choice="submit_evaluation")
        | JsonOutputToolsParser()
    )


async def evaluate_attitude(place, analysis: str) -> str:
    """
    Evaluate the attitude towards FFPV.

    Args:
        analysis: A string that represents the analyses to be evaluated.

    Returns:
        A string that represents the evaluation of the analyses.
    """
    # create evaluation chain
    chain = create_analyses_evaluation_chain()

    # evaluate analyses
    evaluation = await chain.ainvoke(analysis)
    return place, evaluation


# Full analysis which combines the above two steps asynchronously
async def run_full_analysis(
    targets: list[dict[str, str]], cancel_flag: asyncio.Event
) -> list[str]:
    total_tasks = (
        len(targets) * 2
    )  # Each target has a analysis task and an evaluation task
    progress_bar = st.progress(0.0)
    completed_tasks = 0
    evaluations = []

    concurrent_tasks_limit = 4
    targets_splits = [
        targets[i : i + concurrent_tasks_limit]
        for i in range(0, len(targets), concurrent_tasks_limit)
    ]

    for split in targets_splits:
        analyses_tasks = [
            asyncio.create_task(generate_combined_analysis(target)) for target in split
        ]
        evaluation_tasks = []
        while (analyses_tasks or evaluation_tasks) and not cancel_flag.is_set():
            if analyses_tasks:
                done, analyses_tasks = await asyncio.wait(
                    analyses_tasks, return_when=asyncio.FIRST_COMPLETED
                )
                completed_tasks += len(done)
                progress_bar.progress(completed_tasks / total_tasks)

                for task in done:
                    target_and_analysis = task.result()
                    target, analysis = target_and_analysis
                    evaluation_task = asyncio.create_task(
                        evaluate_attitude(target, analysis)
                    )
                    evaluation_tasks.append(evaluation_task)

            if evaluation_tasks:
                done_eval, evaluation_tasks = await asyncio.wait(
                    evaluation_tasks, return_when=asyncio.FIRST_COMPLETED
                )
                evaluation_tasks = list(evaluation_tasks)
                completed_tasks += len(done_eval)
                progress_bar.progress(completed_tasks / total_tasks)

                for task in done_eval:
                    evaluations.append(task.result())

    return evaluations
