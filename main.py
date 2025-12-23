from csv import DictReader
from datetime import datetime
from tabulate import tabulate
from enum import Enum
from argparse import ArgumentParser, Namespace
from typing import Optional
import sys

rates: list = [
    {"start": 8, "end": 17, "rate": "day"},
    {"start": 19, "end": 23, "rate": "day"},
    {"start": 23, "end": 24, "rate": "night"},
    {"start": 0, "end": 8, "rate": "night"},
    {"start": 17, "end": 19, "rate": "peak"},
]


class RateName(Enum):
    day = "day"
    peak = "peak"
    night = "night"

    @staticmethod
    def get_rate_names() -> list[str]:
        return ["day", "peak", "night"]


class Weekday:
    rates: dict
    hours: dict

    def __init__(self):
        self.rates = {rate_name: 0 for rate_name in RateName.get_rate_names()}
        self.hours = {str(i): 0 for i in range(0, 24)}


def validate_args(args: Namespace) -> Namespace:
    if args.rates and args.hours:
        sys.exit("Only --rates or --hours can be passed")
    if not (args.rates or args.hours):  # Neither were passed default to rates
        args.rates = True
    return args


def squash_data(data: dict, rate: bool, hour: bool) -> list:
    squashed_data = []
    attr = None
    if rate:
        attr = "rates"
    elif hour:
        attr = "hours"
    if not attr:
        raise ValueError
    for weekday in data.keys():
        squashed_row = [weekday]
        data_frame = getattr(data[weekday], attr)
        for period in data_frame.keys():
            squashed_row.append(data_frame[period])
        squashed_data.append(squashed_row)
    return squashed_data


def main() -> None:
    parser = ArgumentParser(
        prog="EnergyCalculator",
        description="Parses an ESB networks HDF file into a human readable format",
    )
    parser.add_argument("filename")
    parser.add_argument("--rates", action="store_true")
    parser.add_argument("--hours", action="store_true")
    args = parser.parse_args()
    args = validate_args(args)
    totalKWH: float = 0
    weekdayRateKWH: dict = {}
    for weekday in [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ]:
        weekdayRateKWH[weekday] = Weekday()

    startDate: Optional[datetime] = None
    endDate: Optional[datetime] = None
    with open(args.filename, "r+") as f:
        reader = DictReader(
            f,
        )
        for row in reader:
            timestamp = datetime.strptime(
                row["Read Date and End Time"], "%d-%m-%Y %H:%M"
            )
            if not startDate or timestamp < startDate:
                startDate = timestamp
            if not endDate or timestamp > endDate:
                endDate = timestamp
            totalKWH += float(row["Read Value"])
            for rate in rates:
                weekdayRateKWH[timestamp.strftime("%A")].hours[str(timestamp.hour)] += (
                    float(row["Read Value"])
                )
                if timestamp.hour >= rate["start"] and timestamp.hour < rate["end"]:
                    weekdayRateKWH[timestamp.strftime("%A")].rates[rate["rate"]] += (
                        float(row["Read Value"])
                    )
                    break
        print(f"Total KWH {totalKWH:.2f}")

        squashedWeekDayRate: list = []
        headers: list = []
        if args.rates:
            print("KWH breakdown by weekday/rate periods")
            squashedWeekDayRate = squash_data(weekdayRateKWH, rate=True, hour=False)
            headers = RateName.get_rate_names()
        elif args.hours:
            print("KWH breakdown by weekday/hour periods")
            squashedWeekDayRate = squash_data(weekdayRateKWH, rate=False, hour=True)
            headers = [str(i) for i in range(0, 24)]
        print(tabulate(squashedWeekDayRate, headers=headers, tablefmt="grid"))
        if startDate and endDate:
            print(f"start: {startDate.date()} end: {endDate.date()}")


if __name__ == "__main__":
    main()
