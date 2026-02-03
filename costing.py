import json
from abc import ABC, abstractclassmethod, abstractmethod

from utils.types import CostingType, Weekday


class Costing(ABC):
    costing_type: CostingType
    required_args: list[str] = ["type", "rates"]

    @abstractclassmethod
    @classmethod
    def validate_args(cls, *args, **kwargs) -> tuple[bool, list[str]]:
        valid = True
        missing_args = []

        for arg in cls.required_args:
            if arg not in kwargs.keys():
                valid = False
                missing_args.append(arg)
        return valid, missing_args

    @abstractmethod
    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        pass


class DNPCosting(Costing):
    costing_type = CostingType.day_peak_night
    rates: dict

    def __init__(self, rates: dict, *args, **kwargs):
        self.rates = rates

    @classmethod
    def validate_args(cls, *args, **kwargs) -> tuple[bool, list[str]]:
        valid, missing_args = super().validate_args(*args, **kwargs)
        if not valid:
            return valid, missing_args
        if not isinstance(kwargs["rates"], dict):
            return False, ["rates"]
        for period in ["day", "night", "peak"]:
            if period not in kwargs["rates"]:
                valid = False
                missing_args.append(f"rates.{period}")
                break
            if not isinstance(kwargs["rates"][period], float):
                valid = False
                missing_args.append(f"rates.{period}")
        return valid, missing_args

    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        result = {"day": 0.0, "peak": 0.0, "night": 0.0}
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                result[rate_name] += value * self.rates.get(rate_name)
        return result


class TwentyFourHRCosting(Costing):
    costing_type = CostingType.twenty_four_hour
    rate: float

    def __init__(self, rates: float, *args, **kwargs):
        self.rate = rates

    @classmethod
    def validate_args(cls, *args, **kwargs) -> tuple[bool, list[str]]:
        valid, missing_args = super().validate_args(*args, **kwargs)
        if not valid:
            return valid, missing_args

        if type(kwargs["rates"]) is not float:
            valid = False
            missing_args.append("rates")
        return valid, missing_args

    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        result = 0.0
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                result += value * self.rate
        return {"calculated": result}


class CostingFactory:
    costing_type_to_class: dict = {
        CostingType.day_peak_night: DNPCosting,
        CostingType.twenty_four_hour: TwentyFourHRCosting,
        # CostingType.custom: CustomCosting
    }

    @classmethod
    def get_costing_class(cls) -> Costing:
        raw_costing_data: dict = dict()
        with open("costing.json") as f:
            raw_costing_data = json.load(f)
        costing_type = CostingType(raw_costing_data.get("type"))
        costing_class = cls.costing_type_to_class.get(costing_type)
        if not costing_class:
            raise ValueError(f"unknown costing type {raw_costing_data.get('type')}")
        valid_args, error = costing_class.validate_args(**raw_costing_data)
        if not valid_args:
            raise ValueError(error)
        return costing_class(**raw_costing_data)
