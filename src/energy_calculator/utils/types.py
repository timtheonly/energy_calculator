from dataclasses import dataclass
from datetime import datetime
from enum import Enum


class CostingType(Enum):
    day_peak_night = "day_peak_night"
    twenty_four_hour = "24hr"
    custom = "custom"
    night_boost = "night_boost"

    @classmethod
    def get_costing_types(cls) -> list[str]:
        return [costing_type.value for costing_type in cls]


class RateName(Enum):
    day = "day"
    peak = "peak"
    night = "night"
    night_boost = "night_boost"

    @classmethod
    def get_all_rate_names(cls) -> list[str]:
        return [rate_name.value for rate_name in cls]

    @classmethod
    def get_weekday_rate_names(cls) -> list[str]:
        """
        kinda kludgy but we only care about certain rate names for weekday
        """
        return [
            rate_name.value for rate_name in cls if rate_name.value != "night_boost"
        ]


class ReadType(Enum):
    IMPORT = "import"
    EXPORT = "export"


@dataclass
class RatePeriod:
    start: int
    end: int
    rate: RateName


class Weekday:
    rates: dict[str, float]
    hours: dict[str, float]

    def __init__(self):
        rate_names = RateName.get_weekday_rate_names()
        self.rates = {rate_name: 0 for rate_name in rate_names}
        self.hours = {str(i): 0 for i in range(0, 24)}


class HDFData:
    read: float
    timestamp: datetime
    read_type: ReadType

    def __init__(self, read: float, timestamp: str, read_type: str):
        self.read = read
        self.timestamp = datetime.strptime(timestamp, "%d-%m-%Y %H:%M")
        if "Import" in read_type:
            self.read_type = ReadType.IMPORT
        elif "Export" in read_type:
            self.read_type = ReadType.EXPORT
