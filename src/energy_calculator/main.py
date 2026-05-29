import sys
from argparse import ArgumentParser

from tabulate import tabulate

from energy_calculator.costing import CostingFactory
from energy_calculator.hdf_parser import HDFParser
from energy_calculator.utils.helper_funcs import (
    parse_date_arg,
    squash_data,
    validate_args,
)
from energy_calculator.utils.types import RateName


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
    parser.add_argument(
        "--costing-file",
        "--cf",
        help="file to use for costing data",
        type=str,
        default="costing.json",
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
    hdfParser = HDFParser(args.start, args.end)
    hdfParser.parse(filename=args.filename)
    if args.costing:
        try:
            costing = CostingFactory.get_costing_class(args.costing_file)
            if not costing:
                print("Unable to setup costing")
                sys.exit()
            calculated_cost = costing.calculate(hdfParser.weekday_import_kwh)
            print("Calcualted cost:")
            print(
                tabulate(
                    calculated_cost.items(),
                    headers=["period", "cost"],
                    tablefmt="grid",
                )
            )
            if hdfParser.total_export > 0.0:
                export_value = costing.calculate_export(hdfParser.total_export)
                print(f"Value of export: {export_value:.2f}")
        except ValueError as e:
            print(f"Failed to load costing information: {e}")

    print(f"Total import KWH {hdfParser.total_import:.2f}")
    print(f"Total export KWH {hdfParser.total_export:.2f}")

    squashedWeekDayRate: list = []
    headers: list = []
    if args.rates:
        print("KWH import breakdown by weekday/rate periods")
        squashedWeekDayRate = squash_data(
            hdfParser.weekday_import_kwh, rate=True, hour=False
        )
        headers = RateName.get_rate_names()
    elif args.hours:
        print("KWH import breakdown by weekday/hour periods")
        squashedWeekDayRate = squash_data(
            hdfParser.weekday_import_kwh, rate=False, hour=True
        )
        headers = [str(i) for i in range(0, 24)]
    print(tabulate(squashedWeekDayRate, headers=headers, tablefmt="grid"))
    if hdfParser.start and hdfParser.end:
        print(f"start: {hdfParser.start.date()} end: {hdfParser.end.date()}")


if __name__ == "__main__":
    main()
