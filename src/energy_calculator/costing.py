import json
from abc import ABC, abstractmethod
from pathlib import Path

from jsonschema import validate
from jsonschema.exceptions import ValidationError

from energy_calculator.utils.types import CostingType, Weekday


class Costing(ABC):
    costing_type: CostingType
    rates: dict

    @classmethod
    def validate_args(cls, *args, **kwargs) -> tuple[bool, str]:
        base_path = Path(__file__).parent
        schema_file = base_path / f"schema/{cls.costing_type.value}.schema.json"
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

    def calculate_export(self, total_export: float) -> float:
        if self.rates.get("export"):
            return total_export * self.rates["export"]
        return 0.0


class DNPCosting(Costing):
    costing_type = CostingType.day_peak_night
    rates: dict

    def __init__(self, rates: dict, *args, **kwargs):
        self.rates = rates

    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        result = {"day": 0.0, "peak": 0.0, "night": 0.0, "total": 0.0}
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                result[rate_name] += value * self.rates.get(rate_name)
                result["total"] += value * self.rates.get(rate_name)
        return result


class TwentyFourHRCosting(Costing):
    costing_type = CostingType.twenty_four_hour
    rates: dict

    def __init__(self, rates: dict, *args, **kwargs):
        self.rates = rates

    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        result = 0.0
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                result += value * self.rates.get("import")
        return {"total": result}


class CustomCosting(Costing):
    costing_type = CostingType.custom
    rates: dict
    overrides: dict

    def __init__(self, rates: dict, overrides: dict, *args, **kwargs):
        self.rates = rates
        self.overrides = overrides

    def calculate(self, reading_data: dict[str, Weekday]) -> dict:
        result = {"day": 0.0, "peak": 0.0, "night": 0.0, "total": 0.0}
        for weekday_name, weekday_data in reading_data.items():
            for rate_name, value in weekday_data.rates.items():
                override = self.get_override(weekday_name, rate_name)
                if override:
                    result[rate_name] += value * override
                    result["total"] += value * override
                else:
                    result[rate_name] += value * self.rates.get(rate_name)
                    result["total"] += value * self.rates.get(rate_name)
        return result

    def get_override(self, weekday_name: str, rate_name: str) -> float | None:
        weekday_name = weekday_name.lower()
        if self.overrides:
            if self.overrides.get(weekday_name):
                if self.overrides[weekday_name].get("base_rate"):
                    return self.overrides[weekday_name]["base_rate"]
                elif self.overrides[weekday_name].get(rate_name):
                    return self.overrides[weekday_name][rate_name]
        return None


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
