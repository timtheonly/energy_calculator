from argparse import ArgumentParser
from csv import DictReader
from datetime import datetime
from typing import Optional

from tabulate import tabulate

from costing import CostingFactory
from utils.helper_funcs import parse_date_arg, squash_data, validate_args
from utils.types import HDFData, RateName, ReadType, Weekday

rates: list = [
    {"start": 8, "end": 17, "rate": "day"},
    {"start": 19, "end": 23, "rate": "day"},
    {"start": 23, "end": 24, "rate": "night"},
    {"start": 0, "end": 8, "rate": "night"},
    {"start": 17, "end": 19, "rate": "peak"},
]


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
    parser.add_argument(
        "--costing",
        action="store_true",
        help="calculate cost using rates set out in costing.json",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--rates",
        action="store_true",
        help="Display data in day, peak and night periods",
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
            hdf_data = HDFData(
                read=float(row["Read Value"]),
                timestamp=row["Read Date and End Time"],
                read_type=row["Read Type"],
            )
            if (args.start and hdf_data.timestamp < args.start) or (
                args.end and hdf_data.timestamp >= args.end
            ):
                continue
            if not startDate or hdf_data.timestamp < startDate:
                startDate = hdf_data.timestamp
            if not endDate or hdf_data.timestamp > endDate:
                endDate = hdf_data.timestamp

            if hdf_data.read_type == ReadType.IMPORT:
                totalImportKWH += hdf_data.read
                for rate in rates:
                    weekdayRateKWH[hdf_data.timestamp.strftime("%A")].hours[
                        str(hdf_data.timestamp.hour)
                    ] += hdf_data.read
                    if (
                        hdf_data.timestamp.hour >= rate["start"]
                        and hdf_data.timestamp.hour < rate["end"]
                    ):
                        weekdayRateKWH[hdf_data.timestamp.strftime("%A")].rates[
                            rate["rate"]
                        ] += hdf_data.read
                        break
            elif hdf_data.read_type == ReadType.EXPORT:
                totalExportKWH += hdf_data.read
        if args.costing:
            try:
                costing = CostingFactory.get_costing_class()
                calculated_cost = costing.calculate(weekdayRateKWH)
                print("Calcualted cost:")
                print(
                    tabulate(
                        calculated_cost.items(),
                        headers=["period", "cost"],
                        tablefmt="grid",
                    )
                )
            except ValueError as e:
                print(f"Failed to load costing information: {e}")

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
