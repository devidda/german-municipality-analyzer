import asyncio
import time
from datetime import datetime

import pandas as pd
import streamlit as st
from analyzer import evaluate_attitude, generate_combined_analysis, run_full_analysis
from data_sources.nefino_news.analysis import create_news_analysis
from data_sources.nefino_news.bonus_chat_bot import create_chat_chain
from data_sources.web_search.analysis import (
    create_search_engine_analysis,
    run_general_search,
)
from data_sources.web_search.individual_analysis_agent import (
    run_individual_analysis_agent,
)
from enums import NewsEnergyTypeTable
from langchain_core.messages import AIMessage, HumanMessage
from utility.database import drop_database_table as clear_news_db
from utility.database import (
    get_environment_variable,
    save_analysis_evaluation,
    set_environment_variable,
)
from utility.database import (
    reset_vector_store as clear_and_update_news_vectorstore,
)
from utility.places import get_random_samples, get_selection_targets, validate_place_id
from utility.visualization import plot_for_each_federal_state

# Set the active table to Solar
set_environment_variable("ACTIVE_TABLE", NewsEnergyTypeTable.SOLAR.value)


async def main():
    # Set up the Streamlit interface
    st.title("GAI-based FFPV Attitude Identifier", anchor=False)
    st.markdown(
        """
    This web tool is a part of the bachelor degree thesis in Computer Science at IU Internationale University. 
    The thesis is developed by David Kort under the supervision of M. Hemmer. 
    The software is a methodical tool developed for the task of identifying the stance of municipal planning carriers on ground-mounted photovoltaic systems in Germany.
    """
    )

    # Set up the tabs
    main_control_tab, db_control_tab, visualization_tab, chat_tool_tab = st.tabs(
        ["Main Control", "VS Control", "Visualization", "Bonus Chat Tool"]
    )

    # Set up the vectorstore control tab
    vs_control_container = db_control_tab.container(border=True)
    vs_control_container.header("Vectorstore Control", anchor=False)

    # Set up the energy types select box
    energy_types = vs_control_container.selectbox(
        "Energy Types",
        options=[
            NewsEnergyTypeTable.SOLAR.name,
            NewsEnergyTypeTable.SOLAR_AND_WIND.name,
        ],
        index=0,
    )
    set_environment_variable("ACTIVE_TABLE", NewsEnergyTypeTable[energy_types].value)

    vs_control_col1, vs_control_col2, vs_control_col3 = vs_control_container.columns(3)

    # Set up the danger zone checkbox
    danger_zone = vs_control_col1.checkbox("Danger Zone")

    # Set up the reset vectorstore button
    if vs_control_col2.button("Reset News VS", disabled=danger_zone is not True):
        clear_news_db()
        db_control_tab.write("Vectorstore cleared.")

    # Set up the reset and populate vectorstore button
    if vs_control_col3.button(
        "Reset and Populate News VS",
        disabled=danger_zone is not True,
        help="Add data to Clickhouse, does not reset it.",
    ):
        vectorstore = clear_and_update_news_vectorstore()
        count = vectorstore.client.command(
            f"SELECT total_rows FROM system.tables WHERE name = '{get_environment_variable('ACTIVE_TABLE')}';"
        )
        db_control_tab.write(f"Vectorstore created with {count} entries.")

    # Set up control about the db of analysed results
    pass

    # Set up the main control tab
    operation_container = main_control_tab.container(border=True)
    operation_container.header("Single Operation", anchor=False)

    # Set up the target selection select box
    target = operation_container.selectbox(
        "Target Selection",
        options=get_selection_targets(),
        index=None,
        format_func=lambda x: f'{x["name"]} ({x["id"]})',
        placeholder="Select a target",
    )

    # Set up the operation buttons
    operation_col1, operation_col2, operation_col3, operation_col4 = (
        operation_container.columns(4)
    )

    # Set up the run full intelligence button
    if operation_col1.button(
        "Run full Intelligence", type="primary", disabled=not target
    ):
        if not target or not target["id"]:
            main_control_tab.info("Select a Target first!")
        else:
            with operation_container.status(
                "👀 Analyzing target...", expanded=True
            ) as status:
                start_time = time.time()

                st.write("📚 Collecting Analyses...")
                _, combined_analysis = await generate_combined_analysis(target)

                st.write("🧠 Evaluating Analyses...")
                _, evaluated_result = await evaluate_attitude(target, combined_analysis)

                st.write("💾 Saving results to database...")
                updated = save_analysis_evaluation(
                    target["id"],
                    target["name"],
                    target["place_type"],
                    evaluated_result[0]["args"]["attitude_label"],
                    evaluated_result[0]["args"]["concise_thoughts"],
                    evaluated_result[0]["args"]["CF1"],
                    evaluated_result[0]["args"]["CF2"],
                    evaluated_result[0]["args"]["CF3"],
                    evaluated_result[0]["args"]["CF4"],
                    evaluated_result[0]["args"]["CF5"],
                )
                if updated:
                    main_control_tab.warning(
                        "Target has been evaluated before. Updated."
                    )

                analysis_time = time.time() - start_time
                analysis_time = (
                    f"{int(analysis_time // 60)}m {int(analysis_time % 60)}s"
                )
                status.update(
                    label=f"💡 Analysis completed in {analysis_time}",
                    state="complete",
                    expanded=False,
                )

                main_control_tab.write("Classified Attitude towards FFPV:")
                main_control_tab.write(evaluated_result)

                main_control_tab.subheader("Combined Analyses:", anchor=False)
                main_control_tab.write(combined_analysis)

    batch_operation_container = main_control_tab.container(border=True)
    batch_operation_container.header("Batch Operation", anchor=False)

    # Set up the batch target selection multiselect
    batch_target = batch_operation_container.multiselect(
        "Target Selection",
        options=get_selection_targets(),
        format_func=lambda x: f'{x["name"]} ({x["id"]})',
        placeholder="Select multiple targets",
    )

    # Set up the random seed number input
    random_seed = batch_operation_container.number_input(
        "Random Seed", min_value=0, max_value=1000, value=42
    )

    # Set up the limit of analyses number input
    analysis_limit = batch_operation_container.number_input(
        "Limit of Analyses", min_value=0, max_value=150, value=0
    )

    # Set up the print samples based on seed button
    batch_operation_col1, batch_operation_col2 = batch_operation_container.columns(2)
    if batch_operation_col1.button("Print Samples based on Seed"):
        samples = get_random_samples(random_seed)
        main_control_tab.write(samples)

    # Set up the run full intelligence on batch button
    if batch_operation_col2.button(
        "Run full Intelligence on Batch",
        type="primary",
        disabled=(not (batch_target or random_seed) or analysis_limit <= 0),
    ):
        if not (batch_target or random_seed):
            main_control_tab.write("Select Targets or enter a Seed first!")
        else:
            asyncio_cancel_flag = asyncio.Event()
            button_placeholder = batch_operation_container.empty()
            if button_placeholder.button("Break this Batch Operation"):
                asyncio_cancel_flag.set()
            start_time = time.time()
            targets = batch_target if batch_target else get_random_samples(random_seed)
            target_length = len(targets)
            if target_length > analysis_limit:
                st.info(f"Analysis limited to {analysis_limit} targets.", icon="ℹ")
                targets = targets[:analysis_limit]
            target_length = len(targets)
            answer_placeholder = st.empty()
            batch_operation_results = []

            with batch_operation_container.status(
                f"👀 Analyzing {target_length} targets...", expanded=True
            ) as status:
                batch_analysis_results = await run_full_analysis(
                    targets, asyncio_cancel_flag
                )

                for i, target_and_evaluation in enumerate(batch_analysis_results):
                    target, evaluation = target_and_evaluation
                    batch_operation_results.append(
                        [
                            target["id"],
                            target["name"],
                            target["place_type"],
                            evaluation[0]["args"].get("attitude_label", ""),
                            evaluation[0]["args"].get("concise_thoughts", ""),
                            evaluation[0]["args"].get("CF1", ""),
                            evaluation[0]["args"].get("CF2", ""),
                            evaluation[0]["args"].get("CF3", ""),
                            evaluation[0]["args"].get("CF4", ""),
                            evaluation[0]["args"].get("CF5", ""),
                        ]
                    )

                answer_placeholder.empty()
                with answer_placeholder.container():
                    main_control_tab.subheader("Analysis Results", anchor=False)
                    main_control_tab.write(
                        pd.DataFrame(
                            batch_operation_results,
                            columns=[
                                "ID",
                                "Name",
                                "Place Type",
                                "Attitude",
                                "Thoughts",
                                "CF1",
                                "CF2",
                                "CF3",
                                "CF4",
                                "CF5",
                            ],
                        )
                    )

                analysis_time = time.time() - start_time
                analysis_time = (
                    f"{int(analysis_time // 60)}m {int(analysis_time % 60)}s"
                )
                status.update(
                    label=f"Analysis of {target_length} targets completed in {analysis_time}.",
                    state="complete",
                    expanded=False,
                )

                # Save the results to the database
                button_placeholder.empty()
                for index in range(len(batch_operation_results)):
                    result = batch_operation_results[index]
                    updated = save_analysis_evaluation(
                        result[0],
                        result[1],
                        result[2],
                        result[3],
                        result[4],
                        result[5],
                        result[6],
                        result[7],
                        result[8],
                        result[9],
                    )
                    if updated:
                        status.warning(
                            f"Target **{result[1]}** has been evaluated before. Updated.",
                            icon="⚠️",
                        )

    if operation_col2.button(
        "Run only Nefino LI News Analysis", type="secondary", disabled=not target
    ):
        if not target or not target["id"]:
            main_control_tab.info("Select a Target first!")
        else:
            validate_place_id(target["id"])
            news_container = main_control_tab.container(border=True)
            single_news_analysis = await create_news_analysis(target)
            news_container.write(single_news_analysis.content)

    # Set up the run only Search Engine Analysis button
    if operation_col3.button(
        "Run only Search Engine Analysis", type="secondary", disabled=not target
    ):
        if not target or not target["id"]:
            main_control_tab.info("Select a Target first!")
        else:
            search_engine_container = main_control_tab.container(border=True)
            search_engine_analysis = await create_search_engine_analysis(
                {"name": target["name"], "id": target["id"]}
            )
            search_engine_container.write(search_engine_analysis)

    # Set up the test Google Search Agent button
    if operation_col4.button(
        "Test Google Search Agent", type="secondary", disabled=not target
    ):
        if not target or not target["id"]:
            main_control_tab.info("Select a Target first!")
        else:
            search = run_general_search({"name": "FFPV"}, [target["name"]])
            search_engine_container = main_control_tab.container(border=True)
            search_engine_container.write(run_individual_analysis_agent(search))

    # Set up the clear output and break operations button
    if main_control_tab.button("Clear Output and Break Operations"):
        main_control_tab.write("Output cleared.")

    # Set up the bonus chat tool tab
    chat_tool_tab.text(
        body="This is a bonus feature and not fully implemented. Requests may take multiple seconds to process."
    )
    if chat_tool_tab.button("Clear Chat"):
        st.session_state.messages = []
        st.experimental_rerun()

    chat_bot = create_chat_chain()
    today = datetime.now().date().strftime("%B %d, %Y")

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with chat_tool_tab.chat_message(message.type):
            chat_tool_tab.markdown(message.content)

    # React to user input
    if prompt := chat_tool_tab.chat_input("Was geht ab?"):
        # Display user message in chat message container
        chat_tool_tab.chat_message("user").markdown(prompt)

        with chat_tool_tab.chat_message("Nefino"):
            response = chat_tool_tab.write_stream(
                chat_bot.stream(
                    {
                        "question": prompt,
                        "date": today,
                        "chat_history": st.session_state.messages,
                    }
                )
            )

            # Add messages to history
            st.session_state.messages.extend(
                [HumanMessage(content=prompt), AIMessage(content=response)]
            )

    # Set up the visualization tab
    if visualization_tab.button("Generate Maps of Federal States"):
        plot_for_each_federal_state(visualization_tab)


if __name__ == "__main__":
    asyncio.run(main())
