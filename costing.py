import json
from abc import ABC, abstractmethod

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from utils.types import CostingType, Weekday


class Costing(ABC):
    costing_type: CostingType
    required_args: list[str] = ["rates"]

    @classmethod
    def validate_args(cls, *args, **kwargs) -> tuple[bool, str]:
        schema_file = f"schema/{cls.costing_type.value}.schema.json"
        schema_data = {}
        with open(schema_file) as f:
            schema_data = json.load(f)
        try:
            validate(kwargs, schema=schema_data)
        except ValidationError as e:
            return False, e.message
        return True, ""

    @abstractmethod
    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        pass


class DNPCosting(Costing):
    costing_type = CostingType.day_peak_night
    rates: dict

    def __init__(self, rates: dict, *args, **kwargs):
        self.rates = rates

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

    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        result = 0.0
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                result += value * self.rate
        return {"calculated": result}


class CustomCosting(Costing):
    costing_type = CostingType.custom
    rates: dict

    def __init__(self, rates, *args, **kwargs):
        self.rates = rates


class CostingFactory:
    costing_type_to_class: dict = {
        CostingType.day_peak_night: DNPCosting,
        CostingType.twenty_four_hour: TwentyFourHRCosting,
        CostingType.custom: CustomCosting,
    }

    @classmethod
    def get_costing_class(cls) -> Costing:
        raw_costing_data: dict = dict()
        with open("costing.json") as f:
            raw_costing_data = json.load(f)
        costing_type = CostingType(raw_costing_data.get("costing_type"))
        costing_class = cls.costing_type_to_class.get(costing_type)
        if not costing_class:
            raise ValueError(
                f"unknown costing type {raw_costing_data.get('costing_type')}"
            )
        valid_args, validation_error = costing_class.validate_args(**raw_costing_data)
        if not valid_args:
            raise ValueError(f"invalid config {validation_error}")
        return costing_class(**raw_costing_data)
