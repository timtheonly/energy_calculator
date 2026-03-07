from csv import DictReader
from datetime import datetime

from energy_calculator.utils.types import HDFData, ReadType, Weekday


class HDFParser:
    total_import: float = 0.0
    total_export: float = 0.0
    weekday_import_kwh: dict = {}
    start: datetime | None
    end: datetime | None
    filename: str
    rates: list = [
        {"start": 8, "end": 17, "rate": "day"},
        {"start": 19, "end": 23, "rate": "day"},
        {"start": 23, "end": 24, "rate": "night"},
        {"start": 0, "end": 8, "rate": "night"},
        {"start": 17, "end": 19, "rate": "peak"},
    ]

    def __init__(
        self, filename: str, start: datetime | None = None, end: datetime | None = None
    ):
        self.filename = filename
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

    def parse(self) -> None:
        startDate: datetime | None = self.start
        endDate: datetime | None = self.end
        with open(self.filename, "r+") as f:
            reader = DictReader(
                f,
            )
            for row in reader:
                hdf_data = HDFData(
                    read=float(row["Read Value"]),
                    timestamp=row["Read Date and End Time"],
                    read_type=row["Read Type"],
                )
                if (self.start and hdf_data.timestamp < self.start) or (
                    self.end and hdf_data.timestamp >= self.end
                ):
                    continue
                if not startDate or hdf_data.timestamp < startDate:
                    startDate = hdf_data.timestamp
                if not endDate or hdf_data.timestamp > endDate:
                    endDate = hdf_data.timestamp

                if hdf_data.read_type == ReadType.IMPORT:
                    self.total_import += hdf_data.read
                    for rate in self.rates:
                        self.weekday_import_kwh[
                            hdf_data.timestamp.strftime("%A")
                        ].hours[str(hdf_data.timestamp.hour)] += hdf_data.read
                        if (
                            hdf_data.timestamp.hour >= rate["start"]
                            and hdf_data.timestamp.hour < rate["end"]
                        ):
                            self.weekday_import_kwh[
                                hdf_data.timestamp.strftime("%A")
                            ].rates[rate["rate"]] += hdf_data.read
                            break
                elif hdf_data.read_type == ReadType.EXPORT:
                    self.total_export += hdf_data.read
            if not self.start:
                self.start = startDate
            if not self.end:
                self.end = endDate
