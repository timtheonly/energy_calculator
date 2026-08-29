import unittest
from argparse import ArgumentParser
from datetime import datetime

from energy_calculator.utils.helper_funcs import (
    ProgramArgs,
    parse_date_arg,
    squash_data,
)
from energy_calculator.utils.types import Weekday


class TestValidateArgs(unittest.TestCase):
    def setUp(self):
        self.parser = ArgumentParser()
        self.parser.add_argument(
            "--start",
            type=parse_date_arg,
            help="Date to start calculations from e.g. 01-01-2025",
        )
        self.parser.add_argument(
            "--end",
            type=parse_date_arg,
            help="Date to stop calculations at e.g. 01-01-2025",
        )
        self.parser.add_argument(
            "--rates",
            action="store_true",
            help="Display data in day, peak and night periods",
        )
        self.parser.add_argument(
            "--hours",
            action="store_true",
            help="Display data in hourly breakdown",
        )

    def test_validate_args_nothing_passed(self):
        args = self.parser.parse_args([], namespace=ProgramArgs())
        args.validate_args()
        assert args.rates

    def test_validate_just_hours_passed(self):
        args = self.parser.parse_args(["--hours"], namespace=ProgramArgs())
        args.validate_args()
        assert not args.rates

    def test_validate_start_and_end(self):
        args = self.parser.parse_args(
            ["--start", "01-01-2026", "--end", "02-01-2026"], namespace=ProgramArgs()
        )
        args.validate_args()
        assert args.rates
        assert args.end == datetime(day=2, month=1, year=2026)
        assert args.start == datetime(day=1, month=1, year=2026)

    def test_validate_start_and_end_mismatch(self):
        args = self.parser.parse_args(
            ["--end", "01-01-2026", "--start", "02-01-2026"], namespace=ProgramArgs()
        )
        assert not args.validate_args()


class TestSquashData(unittest.TestCase):
    def test_sqaush_rates(self):
        weekday = Weekday()
        weekday.rates = {"day": 0.1, "night": 0.1, "peak": 0.1}
        data = {"Monday": weekday, "Tuesday": weekday}
        squashed = squash_data(data, True, False)
        assert len(squashed) == 2
        assert squashed[0] == ["Monday", 0.1, 0.1, 0.1]
        assert squashed[1] == ["Tuesday", 0.1, 0.1, 0.1]

    def test_squash_hours(self):
        weekday = Weekday()
        weekday.hours = {"0": 0.1, "1": 0.1, "2": 0.1}
        data = {"Monday": weekday, "Tuesday": weekday}
        squashed = squash_data(data, False, True)
        assert len(squashed) == 2
        assert squashed[0] == ["Monday", 0.1, 0.1, 0.1]
        assert squashed[1] == ["Tuesday", 0.1, 0.1, 0.1]

    def test_invalid_data(self):
        with self.assertRaises(ValueError):
            squash_data({}, False, False)
