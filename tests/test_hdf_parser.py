import io
import unittest
from datetime import datetime
from unittest.mock import mock_open, patch

from energy_calculator.hdf_parser import HDFParser


class TestHdfParser(unittest.TestCase):
    def setUp(self) -> None:
        self.parser = HDFParser(
            datetime(year=2026, month=1, day=1, hour=0, minute=0),
            datetime(year=2026, month=1, day=1, hour=1, minute=0),
        )
        self.fake_data = """Read Value,Read Date and End Time,Read Type\n0.010,01-01-2026 00:00,Active Import Interval (kWh)\n0.010,01-01-2026 00:30,Active Import Interval (kWh)\n0.010,01-01-2026 01:00,Active Import Interval (kWh)\n"""
        return super().setUp()

    def test_file_passed(self):
        fake_data = io.StringIO(self.fake_data)
        self.parser.parse(file=fake_data)

        assert self.parser.start == datetime(
            year=2026, month=1, day=1, hour=0, minute=0
        )
        assert self.parser.end == datetime(year=2026, month=1, day=1, hour=1, minute=0)
        assert self.parser.total_import == 0.030
        assert self.parser.total_export == 0.000

    def test_filename_passed(self):
        with patch(
            "energy_calculator.hdf_parser.open", mock_open(read_data=self.fake_data)
        ) as m:
            self.parser.parse(filename="test.csv")
            m.assert_called_once_with("test.csv", "r+")

        assert self.parser.start == datetime(
            year=2026, month=1, day=1, hour=0, minute=0
        )
        assert self.parser.end == datetime(year=2026, month=1, day=1, hour=1, minute=0)
        assert self.parser.total_import == 0.030
        assert self.parser.total_export == 0.000
