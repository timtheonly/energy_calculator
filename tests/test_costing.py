import json
import tempfile
import unittest
from pathlib import Path

from energy_calculator.costing import (
    CostingFactory,
    CustomCosting,
    DNPCosting,
    TwentyFourHRCosting,
)


class TestCostingFactory(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp_dir.cleanup)

    def _write_costing_file(self, data: dict, name: str = "costing.json") -> str:
        path = Path(self.tmp_dir.name) / name
        path.write_text(json.dumps(data))
        return str(path)

    def test_missing_file_returns_none(self):
        result = CostingFactory.get_costing_class(
            str(Path(self.tmp_dir.name) / "does_not_exist.json")
        )
        assert result is None

    def test_invalid_json_raises(self):
        costing_file = self._write_costing_file({})
        Path(costing_file).write_text("not valid json")
        with self.assertRaises(ValueError):
            CostingFactory.get_costing_class(costing_file)

    def test_unknown_costing_type_raises(self):
        costing_file = self._write_costing_file(
            {"costing_type": "not_a_real_type", "rates": {}}
        )
        with self.assertRaises(ValueError):
            CostingFactory.get_costing_class(costing_file)

    def test_missing_costing_type_raises(self):
        costing_file = self._write_costing_file({"rates": {"import": 0.2}})
        with self.assertRaises(ValueError):
            CostingFactory.get_costing_class(costing_file)

    def test_24hr_returns_configured_instance(self):
        costing_file = self._write_costing_file(
            {"costing_type": "24hr", "rates": {"import": 0.2837, "export": 0.195}}
        )
        costing = CostingFactory.get_costing_class(costing_file)
        assert isinstance(costing, TwentyFourHRCosting)
        assert costing.rates == {"import": 0.2837, "export": 0.195}

    def test_24hr_missing_required_rate_raises(self):
        costing_file = self._write_costing_file(
            {"costing_type": "24hr", "rates": {"export": 0.195}}
        )
        with self.assertRaises(ValueError):
            CostingFactory.get_costing_class(costing_file)

    def test_day_peak_night_returns_configured_instance(self):
        costing_file = self._write_costing_file(
            {
                "costing_type": "day_peak_night",
                "rates": {
                    "day": 0.2837,
                    "peak": 0.3356,
                    "night": 0.2048,
                    "export": 0.195,
                },
            }
        )
        costing = CostingFactory.get_costing_class(costing_file)
        assert isinstance(costing, DNPCosting)
        assert costing.rates["peak"] == 0.3356

    def test_day_peak_night_missing_required_rate_raises(self):
        costing_file = self._write_costing_file(
            {
                "costing_type": "day_peak_night",
                "rates": {"day": 0.2837, "peak": 0.3356, "export": 0.195},
            }
        )
        with self.assertRaises(ValueError):
            CostingFactory.get_costing_class(costing_file)

    def test_custom_returns_configured_instance_with_overrides(self):
        costing_file = self._write_costing_file(
            {
                "costing_type": "custom",
                "rates": {
                    "day": 0.2837,
                    "peak": 0.3356,
                    "night": 0.2048,
                    "export": 0.195,
                },
                "overrides": {"saturday": {"base_rate": 0.2048}},
            }
        )
        costing = CostingFactory.get_costing_class(costing_file)
        assert isinstance(costing, CustomCosting)
        assert costing.overrides == {"saturday": {"base_rate": 0.2048}}

    def test_custom_invalid_rate_type_raises(self):
        costing_file = self._write_costing_file(
            {
                "costing_type": "custom",
                "rates": {"day": "not-a-number", "peak": 0.3356, "night": 0.2048},
                "overrides": {},
            }
        )
        with self.assertRaises(ValueError):
            CostingFactory.get_costing_class(costing_file)

    def test_custom_override_with_base_rate_and_named_rate_raises(self):
        costing_file = self._write_costing_file(
            {
                "costing_type": "custom",
                "rates": {"day": 0.2837, "peak": 0.3356, "night": 0.2048},
                "overrides": {"saturday": {"base_rate": 0.2048, "day": 0.1}},
            }
        )
        with self.assertRaises(ValueError):
            CostingFactory.get_costing_class(costing_file)
