from csv import DictReader
from datetime import datetime
from tabulate import tabulate

rates: list = [
        {"start": 8, "end": 17, "rate": "day"},
        {"start": 19, "end": 23, "rate": "day"},
        {"start": 23, "end": 24, "rate": "night"},
        {"start": 0, "end": 8, "rate": "night"},
        {"start": 17, "end": 19, "rate": "peak"},
]

def main():
    values: list[dict] = []
    totalKWH: float = 0
    weekdayRateKWH: dict = {
        "Monday":{
            "day": 0,
            "peak": 0,
            "night":0,
        },
        "Tuesday":{
            "day": 0,
            "peak": 0,
            "night":0,
        },
        "Wednesday":{
            "day": 0,
            "peak": 0,
            "night":0,
        },
        "Thursday":{
            "day": 0,
            "peak": 0,
            "night":0,
        },
        "Friday":{
            "day": 0,
            "peak": 0,
            "night":0,
        },
        "Saturday":{
            "day": 0,
            "peak": 0,
            "night":0,
        },
        "Sunday":{
            "day": 0,
            "peak": 0,
            "night":0,
        },
    }
    startDate: datetime = None
    endDate: datetime = None
    with open("HDF_kW_10000905318_17-12-2025.csv", "r+") as f:
        reader = DictReader(f, )
        for row in reader:
            timestamp = datetime.strptime(row['Read Date and End Time'], "%d-%m-%Y %H:%M")
            if not startDate or timestamp < startDate:
                startDate = timestamp
            if not endDate or timestamp > endDate:
                endDate = timestamp
            totalKWH += float(row['Read Value'])
            for rate in rates:
                if timestamp.hour >= rate["start"] and timestamp.hour < rate["end"]:
                    weekdayRateKWH[timestamp.strftime("%A")][rate["rate"]] += float(row['Read Value'])
                    break
            values.append(row)
        print(f"Total KWH {totalKWH:.2f}")
        print("KWH breakdown by weekday/rate periods")
        squashedWeekDayRate: list[list] = []
        for weekday in weekdayRateKWH.keys():
            row = [weekday]
            for rate in weekdayRateKWH[weekday].keys():
                row.append(weekdayRateKWH[weekday][rate])
            squashedWeekDayRate.append(row)
        print(tabulate(squashedWeekDayRate, headers=["Day", "Peak", "Night"], tablefmt="grid"))
        print(f"start: {startDate.date()} end: {endDate.date()}")


if __name__ == "__main__":
    main()
