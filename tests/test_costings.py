import math
import unittest

from energy_calculator.costing import DNPCosting, NightBoostCosting, TwentyFourHRCosting
from energy_calculator.utils.types import Weekday


class CostingTest(unittest.TestCase):
    data: dict[str, Weekday] = {}

    def setUp(self) -> None:
        weekday = Weekday()
        for hr in range(24):
            weekday.hours[str(hr)] = 1.0

        weekday.rates["peak"] = 2
        weekday.rates["day"] = 13
        weekday.rates["night"] = 9

        self.data = {"Monday": weekday}

    def assert_float_close(self, a: float, b: float, tolerance: float = 0.001) -> None:
        assert math.isclose(a, b, rel_tol=tolerance), (
            f"{a} is not close to {b} within tolerance of {tolerance}"
        )


class TestNightBoost(CostingTest):
    def test_night_boost_base_case(self):
        rates = {
            "day": 1,
            "peak": 2,
            "night": 0.5,
            "night_boost": 0.1,
            "boost_start": 1,
            "boost_end": 3,
        }
        nbc = NightBoostCosting(rates=rates)
        result = nbc.calculate(self.data)
        self.assert_float_close(result["night"], 3.5)
        self.assert_float_close(result["night_boost"], 0.2)
        self.assert_float_close(result["peak"], 4)
        self.assert_float_close(result["day"], 13)
        self.assert_float_close(result["total"], 20.7)

    def test_night_boost_midnight_case(self):
        rates = {
            "day": 1,
            "peak": 2,
            "night": 0.5,
            "night_boost": 0.1,
            "boost_start": 23,
            "boost_end": 1,
        }
        nbc = NightBoostCosting(rates=rates)
        result = nbc.calculate(self.data)
        self.assert_float_close(result["night"], 3.5)
        self.assert_float_close(result["night_boost"], 0.2)
        self.assert_float_close(result["peak"], 4)
        self.assert_float_close(result["day"], 13)
        self.assert_float_close(result["total"], 20.7)

    def test_validate_args_valid(self):
        rates = {
            "day": 1,
            "peak": 2,
            "night": 0.5,
            "night_boost": 0.1,
            "boost_start": 23,
            "boost_end": 1,
        }
        is_valid, validation_error = NightBoostCosting.validate_args(
            costing_type="night_boost", rates=rates
        )
        assert is_valid
        assert not validation_error

    def test_validate_args_invalid(self):
        rates = {
            "day": 1,
            "peak": 2,
            "night": 0.5,
            "night_boost": 0.1,
            "boost_start": 16,
            "boost_end": 19,
        }
        is_valid, validation_error = NightBoostCosting.validate_args(
            costing_type="night_boost", rates=rates
        )
        assert not is_valid
        for error in [
            "boost_end cannot be during daytime hours",
            "boost_start cannot be during daytime hours",
        ]:
            assert error in validation_error


class TestDNP(CostingTest):
    def test_dnp_base_case(self):
        rates = {
            "day": 1,
            "peak": 2,
            "night": 0.5,
        }
        DNPc = DNPCosting(rates=rates)
        result = DNPc.calculate(self.data)
        self.assert_float_close(result["night"], 4.5)
        self.assert_float_close(result["peak"], 4)
        self.assert_float_close(result["day"], 13)
        self.assert_float_close(result["total"], 21.5)


class Test24hr(CostingTest):
    def test_dnp_base_case(self):
        rates = {
            "import": 1.0,
        }
        thc = TwentyFourHRCosting(rates=rates)
        result = thc.calculate(self.data)
        self.assert_float_close(result["total"], 24)
