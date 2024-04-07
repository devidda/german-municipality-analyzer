import os

from dotenv import load_dotenv
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import Runnable, RunnablePassthrough
from langchain_openai.chat_models import ChatOpenAI
from prompts.bonus_chat import (
    CONTEXTUALIZE_PROMPT,
    QA_CHAT_BOT_PROMPT,
)
from utility.database import establish_clickhouse_connection

load_dotenv(verbose=True)
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")
OPENAI_SMART_LLM = os.getenv("OPENAI_SMART_LLM")
llm = ChatOpenAI(organization=OPENAI_ORG_ID, model=OPENAI_SMART_LLM, temperature=0)


def format_docs(docs) -> str:
    """
    Format documents into a single string.

    Args:
        docs: A list of documents.

    Returns:
        A single string containing all documents.
    """
    return "\n\n".join(doc.page_content for doc in docs)


def create_contextualize_chain() -> Runnable:
    """
    Creates a chain for contextualizing a question.

    Returns:
        A LangChain Runnable.
    """
    contextualize_q_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", CONTEXTUALIZE_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )
    return contextualize_q_prompt | llm | StrOutputParser()


def create_chat_chain() -> Runnable:
    """
    Creates a chain for a chat.

    Returns:
        A LangChain Runnable.
    """
    vs = establish_clickhouse_connection()
    retriever = vs.as_retriever()

    qa_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", QA_CHAT_BOT_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{question}"),
        ]
    )

    def contextualized_question(input: dict) -> Runnable | str:
        if input.get("chat_history"):
            return create_contextualize_chain()
        else:
            return input["question"]

    rag_chain = (
        RunnablePassthrough.assign(
            context=contextualized_question | retriever | format_docs
        )
        | qa_prompt
        | llm
        | StrOutputParser()
    )
    return rag_chain
