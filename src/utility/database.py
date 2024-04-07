import os

import streamlit as st
from clickhouse_connect import get_client
from clickhouse_connect.driver.exceptions import DatabaseError
from dotenv import load_dotenv
from enums import NewsEnergyTypeTable
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores.clickhouse import Clickhouse, ClickhouseSettings
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings

load_dotenv(verbose=True)
OPENAI_ORG_ID = os.getenv("OPENAI_ORG_ID")

embedding_model = OpenAIEmbeddings(
    model="text-embedding-3-small", organization=OPENAI_ORG_ID
)


def get_environment_variable(var_name: str) -> str:
    """
    Retrieve the value of an environment variable.

    Args:
        var_name: The name of the environment variable.

    Returns:
        The value of the environment variable.
    """
    return os.getenv(var_name)


def set_environment_variable(var_name: str, value: str) -> None:
    """
    Set the value of an environment variable.

    Args:
        var_name: The name of the environment variable.
        value: The value to set.
    """
    os.environ[var_name] = value


def get_clickhouse_settings() -> ClickhouseSettings:
    """
    Retrieve the configuration settings for Clickhouse.

    Returns:
        The configuration settings for Clickhouse.
    """
    return ClickhouseSettings(
        host="clickhouse",
        table=get_environment_variable("ACTIVE_TABLE"),
        index_type="minmax",
    )


def establish_clickhouse_connection() -> Clickhouse:
    """
    Establish a connection to the Clickhouse vector store.

    Returns:
        The Clickhouse object representing the connection.
    """
    clickhouse_config = get_clickhouse_settings()
    return Clickhouse(embedding=embedding_model, config=clickhouse_config)


def check_table_exists(table: str = get_environment_variable("ACTIVE_TABLE")) -> bool:
    """
    Check if a table exists in the database.

    Args:
        table: The name of the table to check. Defaults to the active table.

    Returns:
        True if the table exists, False otherwise.
    """
    client = get_client(host="clickhouse")
    try:
        client.command(f"CHECK TABLE {table};")
    except DatabaseError:
        return False
    return True


def drop_database_table() -> None:
    """
    Drop the active table from the database.
    """
    active_table = get_environment_variable("ACTIVE_TABLE")
    if not check_table_exists():
        st.error("Table does not exist.")
        return

    vector_store = establish_clickhouse_connection()
    vector_store.drop()
    try:
        vector_store.client.command(f"CHECK TABLE {active_table};")
    except DatabaseError:
        st.write(f'Table "{active_table}" dropped.')
    except Exception as e:
        st.error(f'Failed to drop table "{active_table}".')
        raise e


def reset_vector_store(chunk_size: int = 500, chunk_overlap: int = 20) -> Clickhouse:
    """
    Reset the vector store in Clickhouse.

    Args:
        chunk_size: The size of the chunks to split the text into. Defaults to 500.
        chunk_overlap: The number of characters to overlap between chunks. Defaults to 20.

    Returns:
        The Clickhouse object representing the vectorestore connection.
    """
    active_table = get_environment_variable("ACTIVE_TABLE")
    if check_table_exists():
        st.write(f'Table "{active_table}" already exists and will be reset.')
        drop_database_table()
    documents = generate_documents_from_csv(chunk_size, chunk_overlap)

    clickhouse_config = get_clickhouse_settings()
    return Clickhouse.from_documents(
        documents, embedding_model, config=clickhouse_config
    )


def generate_documents_from_csv(
    chunk_size: int = 500, chunk_overlap: int = 20
) -> list[Document]:
    """
    Generate a list of Document objects from a CSV file.

    Args:
        chunk_size: The size of the chunks to split the text into. Defaults to 500.
        chunk_overlap: The number of characters to overlap between chunks. Defaults to 20.

    Returns:
        A list of Document objects.
    """
    source = ""
    match get_environment_variable("ACTIVE_TABLE"):
        case NewsEnergyTypeTable.SOLAR.value:
            source = "/workspaces/thesis/assets/nefino_solar_news_until_2024_03_28_cleaned.csv"
        case NewsEnergyTypeTable.SOLAR_AND_WIND.value:
            source = "/workspaces/thesis/assets/nefino_solar_and_wind_news_until_2024_03_28_cleaned.csv"
        case _:
            st.error("No active table selected.")
            return []

    csv_loader = CSVLoader(
        file_path=source,
        source_column="place_id",
        metadata_columns=["date", "news_id"],
    )
    documents = csv_loader.load()

    text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )
    return text_splitter.split_documents(documents)


def save_analysis_evaluation(
    place_id: str,
    place_name: str,
    place_type: str,
    attitude_label: str,
    concise_thoughts: str,
    cf1: str,
    cf2: str,
    cf3: str,
    cf4: str,
    cf5: str,
) -> bool:
    """
    Save a analysis evaluation to the database.

    Args:a
        place_id: The ID of the place.
        place_name: The name of the place.
        place_type: The type of the place.
        attitude_label: The attitude towards FFPV.
        concise_thoughts: The concise thoughts about the place's attitude towards FFPV.
        cf1: The classification feature 1.
        cf2: The classification feature 2.
        cf3: The classification feature 3.
        cf4: The classification feature 4.
        cf5: The classification feature 5.

    Returns:
        True if the place has been updated, False if it was a new entry.
    """
    place_has_been_updated = False
    client = get_client(host="clickhouse")

    try:
        client.command("CHECK TABLE ANALYSIS_RESULTS;")
    except DatabaseError:
        st.write("Creating table ANALYSIS_RESULTS...")
        client.command(
            "CREATE TABLE ANALYSIS_RESULTS ("
            "cf1 String, "
            "cf2 String, "
            "cf3 String, "
            "cf4 String, "
            "cf5 String, "
            "attitude_label String, "
            "concise_thoughts String,"
            "place_id String, "
            "place_name String, "
            "place_type String "
            ") ENGINE = MergeTree() "
            "ORDER BY place_id "
            "PRIMARY KEY place_id;"
        )

    # First, check if the record exists
    place_id = place_id.replace("'", "''")
    place_name = place_name.replace("'", "''")
    place_type = place_type.replace("'", "''")
    attitude_label = attitude_label.replace("'", "''")
    concise_thoughts = concise_thoughts.replace("'", "''")
    cf1 = cf1.replace("'", "''")
    cf2 = cf2.replace("'", "''")
    cf3 = cf3.replace("'", "''")
    cf4 = cf4.replace("'", "''")
    cf5 = cf5.replace("'", "''")

    result = client.command(
        f"SELECT count(*) FROM ANALYSIS_RESULTS WHERE place_id = '{place_id}'"
    )

    # If the record exists, update it
    if result > 0:
        client.command(
            (
                "ALTER TABLE ANALYSIS_RESULTS UPDATE ",
                f"attitude_label = '{attitude_label}', ",
                f"concise_thoughts = '{concise_thoughts}', ",
                f"cf1 = '{cf1}', cf2 = '{cf2}', cf3 = '{cf3}', ",
                f"cf4 = '{cf4}', cf5 = '{cf5}' ",
                f"WHERE place_id = '{place_id}'"
            )
        )
        place_has_been_updated = True

    # If the record doesn't exist, insert it
    else:
        client.command((
            "INSERT INTO ANALYSIS_RESULTS (place_id, place_name, place_type, attitude_label, concise_thoughts, cf1, cf2, cf3, cf4, cf5) ",
            f"VALUES ('{place_id}', '{place_name}', '{place_type}', "
            f"'{attitude_label}', '{concise_thoughts}', '{cf1}', '{cf2}', "
            f"'{cf3}', '{cf4}', '{cf5}')"
        ))

    return place_has_been_updated
