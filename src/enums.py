from enum import Enum


class NewsEnergyTypeTable(Enum):
    """
    Enum for the news energy type tables.
    
    Attributes:
        SOLAR: The solar news table.
        SOLAR_AND_WIND: The combined solar and wind news table.
    """
    SOLAR = "nefino_news_solar"
    SOLAR_AND_WIND = "nefino_news"
