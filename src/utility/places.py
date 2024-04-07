import os

import pandas as pd


def iterate_place_files():
    """
    Generator function that iterates over all CSV files in a specific directory.

    Yields:
        A dictionary representing a place.

    """
    for file in os.scandir("/workspaces/thesis/assets/places"):
        if file.name.endswith(".csv"):
            with open(file.path, "r") as f:
                if os.stat(file.path).st_size == 0:
                    continue
                if file.name.split(".")[0] == "1_federal_states":
                    continue
                yield pd.read_csv(file.path), file.name.split(".")[0]


def validate_place_id(place_id: str) -> bool:
    """
    Validates a given place ID by checking if it exists in any of the place files.

    Args:
        place_id: The place ID to validate.

    Returns:
        True if the place ID is valid, False otherwise.

    Raises:
        ValueError: If the place ID is not found in any of the place files.
    """
    for places, place_type in iterate_place_files():
        for _, place in places.iterrows():
            if place_id == place["nuts_code"]:
                return True
    raise ValueError("Invalid place id")


def get_selection_targets() -> list[dict[str]]:
    """
    Retrieves a list of all places from the place files.
    Each place is represented as a dictionary with an "id" and "name" field.

    Returns:
        A list of dictionaries, each representing a place.
    """
    targets: list[dict[str]] = []
    for places, place_type in iterate_place_files():
        for _, place in places.iterrows():
            place = {
                "id": place["nuts_code"],
                "name": place["name"],
                "place_type": place_type,
            }
            targets.append(place)
    return targets


def get_random_samples(seed: int) -> list[dict[str, list[dict[str, str]]]]:
    """
    Retrieves random samples of places from the place files.
    Each sample-list of a single place type is represented as a dictionary with a "place_type" and "samples" field.
    The "samples" field contains a list of dictionaries, each representing a place with it's id and name.

    Args:
        seed: The random seed to use for sampling.

    Returns:
        A list of dictionaries, each representing a sample of places.

    Raises:
        ValueError: If the seed is not between 0 and 1000.
    """
    if seed > 1000 or seed < 0:
        raise ValueError("Seed must be between 0 and 1000")
    sample_sizes = {
        "2_planning_regions": 26,
        "3_counties": 31,
        "4_administrative_units": 33,
        "5_local_administrative_units": 33,
    }
    samples = []
    for places_df, place_type in iterate_place_files():
        # Select random samples
        sample_size = sample_sizes[place_type]
        places_df = places_df.sample(n=sample_size, random_state=seed)
        samples.extend(
            places_df.apply(
                lambda place: {
                    "id": place["nuts_code"],
                    "name": place["name"],
                    "place_type": place_type,
                },
                axis=1,
            )
            .to_dict()
            .values(),
        )
    return samples
