import ast
import geopandas as gpd
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
from clickhouse_connect import get_client
from utility.places import iterate_place_files


def plot_for_each_federal_state(streamlit_container: st.container) -> None:
    federal_state_ids = pd.read_csv(
        "/workspaces/thesis/assets/places/1_federal_states.csv"
    )

    for id, name in federal_state_ids[["nuts_code", "name"]].values:
        plot_classified_places_in_state(id, name, streamlit_container)


def plot_classified_places_in_state(
    state_code: str, state_name: str, streamlit_container: st.container
) -> None:
    levels = iterate_place_files()
    places = []
    for level, _ in levels:
        for _, place in level.iterrows():
            places.append(place)
    places = pd.DataFrame.from_records(places)

    # Connect to ClickHouse database
    client = get_client(host="clickhouse")

    # Query to get the classification data
    query = "SELECT (place_id, attitude_label, place_type) FROM ANALYSIS_RESULTS"
    data = client.command(query)

    split_data = [ast.literal_eval(item) for item in data.split("\n") if item]
    nuts_codes, attitudes, place_types = zip(*split_data)
    print(nuts_codes[:5])

    # Create a DataFrame from the split data
    classifications = pd.DataFrame({"nuts_code": nuts_codes, "attitude": attitudes, "place_type": place_types})

    # Merge the place GeoDataFrame with the classifications DataFrame
    merged = pd.merge(places, classifications, on="nuts_code", how="left")

    # Filter the merged GeoDataFrame to only include rows where the 'federal_state_id' is the given state_code
    filtered = merged[merged["federal_state_id"] == state_code]

    # Check for missing values
    if filtered["geom"].isnull().any():
        # Handle missing values (e.g., drop the rows)
        filtered = filtered.dropna(subset=["geom"])

    # Check the format of the data
    if not isinstance(filtered["geom"].iloc[0], gpd.geoseries.GeoSeries):
        # Convert the data to the correct format
        filtered["geom"] = gpd.GeoSeries.from_wkb(filtered["geom"])

    # Set the active geometry column
    filtered = filtered.set_geometry("geom")

    # Plot the geometries of the filtered GeoDataFrame
    fig, ax = plt.subplots()
    filtered.plot(ax=ax, color="lightcyan", edgecolor="black")

    plot_classifications(filtered[filtered["place_type"] == "2_planning_regions"], ax)
    plot_classifications(filtered[filtered["place_type"] == "3_counties"], ax)
    plot_classifications(filtered[filtered["place_type"] == "4_administrative_units"], ax)
    plot_classifications(filtered[filtered["place_type"] == "5_local_administrative_units"], ax)

    ax = ax.set_axis_off()  # Remove axis labels
    fig.suptitle(state_name)
    streamlit_container.pyplot(fig)

def plot_classifications(df, ax):
    df[df["attitude"] == "negative"].plot(
        ax=ax, color="orangered", edgecolor="black"
    )
    df[df["attitude"] == "potentially positive"].plot(
        ax=ax, color="darkseagreen", edgecolor="black"
    )
    df[df["attitude"] == "very positive"].plot(
        ax=ax, color="limegreen", edgecolor="black"
    )
