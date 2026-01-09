from csv import DictReader
from datetime import datetime
from tabulate import tabulate
from enum import Enum
from argparse import ArgumentParser
from typing import Optional

from utils.helper_funcs import squash_data, parse_date_arg, validate_args

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


def main() -> None:
    parser = ArgumentParser(
        prog="EnergyCalculator",
        description="Parses an ESB networks HDF file into a human readable format",
    )
    parser.add_argument("filename", help="File containing HDF csv data")

    parser.add_argument(
        "--start",
        type=parse_date_arg,
        help="Date to start calculations from e.g. 01-01-2025",
    )
    parser.add_argument(
        "--end",
        type=parse_date_arg,
        help="Date to stop calculations at e.g. 01-01-2025",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--rates",
        action="store_true",
        help="Display data in day, peak and night periods",
        default=True,
    )
    group.add_argument(
        "--hours", action="store_true", help="Display data as an hourly breakdown"
    )
    args = parser.parse_args()
    args = validate_args(args)
    totalImportKWH: float = 0
    totalExportKWH: float = 0
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

    startDate: Optional[datetime] = args.start
    endDate: Optional[datetime] = args.end
    with open(args.filename, "r+") as f:
        reader = DictReader(
            f,
        )
        for row in reader:
            timestamp = datetime.strptime(
                row["Read Date and End Time"], "%d-%m-%Y %H:%M"
            )
            if (args.start and timestamp < args.start) or (
                args.end and timestamp >= args.end
            ):
                continue
            if not startDate or timestamp < startDate:
                startDate = timestamp
            if not endDate or timestamp > endDate:
                endDate = timestamp

            if "Import" in row["Read Type"]:
                totalImportKWH += float(row["Read Value"])
                for rate in rates:
                    weekdayRateKWH[timestamp.strftime("%A")].hours[
                        str(timestamp.hour)
                    ] += float(row["Read Value"])
                    if timestamp.hour >= rate["start"] and timestamp.hour < rate["end"]:
                        weekdayRateKWH[timestamp.strftime("%A")].rates[
                            rate["rate"]
                        ] += float(row["Read Value"])
                        break
            elif "Export" in row["Read Type"]:
                totalExportKWH += float(row["Read Value"])
        print(f"Total import KWH {totalImportKWH:.2f}")
        print(f"Total export KWH {totalExportKWH:.2f}")

        squashedWeekDayRate: list = []
        headers: list = []
        if args.rates:
            print("KWH import breakdown by weekday/rate periods")
            squashedWeekDayRate = squash_data(weekdayRateKWH, rate=True, hour=False)
            headers = RateName.get_rate_names()
        elif args.hours:
            print("KWH import breakdown by weekday/hour periods")
            squashedWeekDayRate = squash_data(weekdayRateKWH, rate=False, hour=True)
            headers = [str(i) for i in range(0, 24)]
        print(tabulate(squashedWeekDayRate, headers=headers, tablefmt="grid"))
        if startDate and endDate:
            print(f"start: {startDate.date()} end: {endDate.date()}")


if __name__ == "__main__":
    main()
