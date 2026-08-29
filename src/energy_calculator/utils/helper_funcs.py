from argparse import Namespace
from datetime import datetime

from energy_calculator.utils.types import Weekday


class ProgramArgs(Namespace):
    filename: str
    start: datetime | None
    end: datetime | None
    costing: bool | None
    costing_file: str
    rates: bool | None
    hours: bool | None

    def validate_args(self) -> bool:
        if not self.hours or self.rates:
            self.rates = True  # default to rates if nothing passed
        if self.start and self.end:
            if self.end < self.start:
                print("End must be greater than start")
                return False
        return True


def squash_data(
    data: dict[str, Weekday], rate: bool, hour: bool
) -> list[list[str | float]]:
    squashed_data: list[list[str | float]] = []
    attr = None
    if rate:
        attr = "rates"
    elif hour:
        attr = "hours"
    if not attr:
        raise ValueError
    for weekday in data.keys():
        squashed_row: list[str | float] = [weekday]
        data_frame: dict[str, float] = getattr(data[weekday], attr)
        for period in data_frame.keys():
            squashed_row.append(data_frame[period])
        squashed_data.append(squashed_row)
    return squashed_data


def parse_date_arg(value: str) -> datetime:
    return datetime.strptime(value, "%d-%m-%Y")
