import sys
from datetime import datetime
from argparse import Namespace


def validate_args(args: Namespace) -> Namespace:
    if not args.hours or args.rates:
        args.rates = True  # default to rates if nothing passed
    if args.start and args.end:
        if args.end < args.start:
            sys.exit("End must be greater than start")
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


def parse_date_arg(value: str) -> datetime:
    return datetime.strptime(value, "%d-%m-%Y")
