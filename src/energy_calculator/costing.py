import json
from abc import ABC, abstractmethod
from pathlib import Path

from jsonschema import validate
from jsonschema.exceptions import ValidationError
from typing_extensions import override

from energy_calculator.utils.types import CostingType, RateName, RatePeriod, Weekday


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
    def calculate(self, reading_data: dict[str, Weekday]) -> dict[str, float]:
        pass

    def calculate_export(self, total_export: float) -> float:
        if self.rates.get("export"):
            return total_export * self.rates.get("export", 0.0)
        return 0.0


class DNPCosting(Costing):
    costing_type: CostingType = CostingType.day_peak_night
    rates: dict[str, float]

    def __init__(self, rates: dict[str, float], *args, **kwargs):
        self.rates = rates

    @override
    def calculate(self, reading_data: dict[str, Weekday]) -> dict[str, float]:
        result = {"day": 0.0, "peak": 0.0, "night": 0.0, "total": 0.0}
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                result[rate_name] += value * self.rates.get(rate_name, 0.0)
                result["total"] += value * self.rates.get(rate_name, 0.0)
        return result


class TwentyFourHRCosting(Costing):
    costing_type: CostingType = CostingType.twenty_four_hour
    rates: dict[str, float]

    def __init__(self, rates: dict[str, float], *args, **kwargs):
        self.rates = rates

    @override
    def calculate(self, reading_data: dict[str, Weekday]) -> dict[str, float]:
        result = 0.0
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                result += value * self.rates.get("import", 0.0)
        return {"total": result}


class CustomCosting(Costing):
    costing_type: CostingType = CostingType.custom
    rates: dict[str, float]
    overrides: dict[str, dict[str, float]]

    def __init__(
        self,
        rates: dict[str, float],
        overrides: dict[str, dict[str, float]],
        *args,
        **kwargs,
    ):
        self.rates = rates
        self.overrides = overrides

    @override
    def calculate(self, reading_data: dict[str, Weekday]) -> dict[str, float]:
        result = {"day": 0.0, "peak": 0.0, "night": 0.0, "total": 0.0}
        for weekday_name, weekday_data in reading_data.items():
            for rate_name, value in weekday_data.rates.items():
                override = self.get_override(weekday_name, rate_name)
                if override is not None:
                    result[rate_name] += value * override
                    result["total"] += value * override
                else:
                    result[rate_name] += value * self.rates.get(rate_name, 0.0)
                    result["total"] += value * self.rates.get(rate_name, 0.0)
        return result

    def get_override(self, weekday_name: str, rate_name: str) -> float | None:
        weekday_name = weekday_name.lower()
        if self.overrides:
            if self.overrides.get(weekday_name):
                if self.overrides[weekday_name].get("base_rate") is not None:
                    return self.overrides[weekday_name]["base_rate"]
                elif self.overrides[weekday_name].get(rate_name) is not None:
                    return self.overrides[weekday_name][rate_name]
        return None


class NightBoostCosting(Costing):
    costing_type: CostingType = CostingType.night_boost
    rates: dict[str, int | float]
    night_rates_periods: list[RatePeriod]

    def __init__(self, rates: dict[str, int | float], *args, **kwargs):
        self.rates = rates
        boost_start = int(self.rates.get("boost_start", 0))
        boost_end = int(self.rates.get("boost_end", 0))
        if boost_start == 23:
            self.night_rates_periods = [
                RatePeriod(start=boost_start, end=24, rate=RateName.night_boost),
                RatePeriod(start=0, end=boost_end, rate=RateName.night_boost),
                RatePeriod(start=boost_end, end=8, rate=RateName.night),
            ]
        else:
            self.night_rates_periods = [
                RatePeriod(start=boost_start, end=boost_end, rate=RateName.night_boost),
                RatePeriod(start=23, end=24, rate=RateName.night),
                RatePeriod(start=0, end=8, rate=RateName.night),
            ]

    @override
    def calculate(self, reading_data: dict[str, Weekday]) -> dict[str, float]:
        result = {
            "day": 0.0,
            "peak": 0.0,
            "night": 0.0,
            "night_boost": 0.0,
            "total": 0.0,
        }
        for weekday_data in reading_data.values():
            for rate_name, value in weekday_data.rates.items():
                if rate_name != RateName.night.value:
                    result[rate_name] += value * self.rates.get(rate_name, 0.0)
                    result["total"] += value * self.rates.get(rate_name, 0.0)
            # night boost breaks night rate in 2 so we need to go by hours
            for hour, value in weekday_data.hours.items():
                for rate in self.night_rates_periods:
                    rate_name = rate.rate.value
                    if int(hour) >= rate.start and int(hour) < rate.end:
                        result[rate_name] += value * self.rates.get(rate_name, 0.0)
                        result["total"] += value * self.rates.get(rate_name, 0.0)
                        break
        return result

    @classmethod
    def validate_args(cls, *args, **kwargs) -> tuple[bool, str]:
        valid, error = super().validate_args(*args, **kwargs)
        if kwargs["rates"]["boost_start"] >= 8 and kwargs["rates"]["boost_start"] < 23:
            valid = False
            error = f"{error} \n boost_start cannot be during daytime hours"
        if kwargs["rates"]["boost_end"] > 8 and kwargs["rates"]["boost_end"] < 23:
            valid = False
            error = f"{error} \n boost_end cannot be during daytime hours"
        if error.startswith("\n"):
            error = error[2:]
        return valid, error


class CostingFactory:
    costing_type_to_class: dict[CostingType, type[Costing]] = {
        CostingType.day_peak_night: DNPCosting,
        CostingType.twenty_four_hour: TwentyFourHRCosting,
        CostingType.custom: CustomCosting,
        CostingType.night_boost: NightBoostCosting,
    }

    @classmethod
    def get_costing_class(cls, costing_file: str) -> Costing | None:
        raw_costing_data: dict[str, str | dict[str, str]] = dict()
        try:
            with open(costing_file) as f:
                raw_costing_data = json.load(f)
        except OSError:
            return None
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
