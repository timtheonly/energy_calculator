from csv import DictReader
from datetime import datetime
from typing import TextIO

from energy_calculator.utils.types import (
    HDFData,
    RateName,
    RatePeriod,
    ReadType,
    Weekday,
)


class HDFParser:
    total_import: float = 0.0
    total_export: float = 0.0
    weekday_import_kwh: dict[str, Weekday] = {}
    start: datetime | None
    end: datetime | None
    rates: list[RatePeriod] = [
        RatePeriod(start=8, end=17, rate=RateName.day),
        RatePeriod(start=19, end=23, rate=RateName.day),
        RatePeriod(start=23, end=24, rate=RateName.night),
        RatePeriod(start=0, end=8, rate=RateName.night),
        RatePeriod(start=17, end=19, rate=RateName.peak),
    ]

    def __init__(self, start: datetime | None = None, end: datetime | None = None):
        self.start = start
        self.end = end
        for weekday in [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]:
            self.weekday_import_kwh[weekday] = Weekday()

    def parse(self, filename: str | None = None, file: TextIO | None = None) -> None:
        startDate: datetime | None = self.start
        endDate: datetime | None = self.end

        if not (filename or file):
            raise ValueError

        f: TextIO | None = None
        try:
            if filename:
                f = open(filename, "r+")
            elif file:
                f = file
        except FileNotFoundError:
            raise ValueError

        if not f:
            raise ValueError

        reader = DictReader(
            f,
        )
        for row in reader:
            startDate, endDate = self._parse_row(row, startDate, endDate)
            if not (startDate or endDate):
                continue

        if not self.start:
            self.start = startDate
        if not self.end:
            self.end = endDate

        if filename:
            f.close()

    def _parse_row(
        self, row: dict[str, str], startDate: datetime | None, endDate: datetime | None
    ) -> tuple[datetime | None, datetime | None]:
        hdf_data = HDFData(
            read=float(row["Read Value"]),
            timestamp=row["Read Date and End Time"],
            read_type=row["Read Type"],
        )
        if (self.start and hdf_data.timestamp < self.start) or (
            self.end and hdf_data.timestamp > self.end
        ):
            return None, None
        if not startDate or hdf_data.timestamp < startDate:
            startDate = hdf_data.timestamp
        if not endDate or hdf_data.timestamp > endDate:
            endDate = hdf_data.timestamp

        if hdf_data.read_type == ReadType.IMPORT:
            self.total_import += hdf_data.read
            for rate in self.rates:
                self.weekday_import_kwh[hdf_data.timestamp.strftime("%A")].hours[
                    str(hdf_data.timestamp.hour)
                ] += hdf_data.read
                if (
                    hdf_data.timestamp.hour >= rate.start
                    and hdf_data.timestamp.hour < rate.end
                ):
                    self.weekday_import_kwh[hdf_data.timestamp.strftime("%A")].rates[
                        rate.rate.value
                    ] += hdf_data.read
                    break
        elif hdf_data.read_type == ReadType.EXPORT:
            self.total_export += hdf_data.read
        return startDate, endDate
