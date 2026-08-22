# AGENTS.md

## Project overview

`energy_calculator` parses an ESB Networks HDF (Harmonised Downloadable File)
CSV export into a human-readable breakdown of electricity usage, by weekday
and by rate period (day/peak/night) or by hour. It can optionally cost that
usage against a `costing.json` file describing a tariff. Usable as a library
(`energy_calculator.hdf_parser.HDFParser`, `energy_calculator.costing`) or as
a CLI (`energy_calculator`, entry point in `src/energy_calculator/main.py`).

## Setup

This project uses `uv` for dependency management (`uv.lock` present,
`requires-python = ">=3.14"`).

```bash
uv sync
```

## Layout

- `src/energy_calculator/main.py` — CLI entry point (`argparse`).
- `src/energy_calculator/hdf_parser.py` — `HDFParser`, reads the HDF CSV and
  buckets readings into `weekday_import_kwh` (per weekday, per rate period
  and per hour) plus running import/export totals.
- `src/energy_calculator/costing.py` — `Costing` (ABC) and its
  implementations (`DNPCosting`, `TwentyFourHRCosting`, `CustomCosting`) plus
  `CostingFactory`, which loads a `costing.json`-style file, validates it
  against the matching JSON Schema, and instantiates the right class.
- `src/energy_calculator/schema/*.schema.json` — JSON Schemas for the three
  costing types (`24hr`, `day_peak_night`, `custom`); used by
  `Costing.validate_args`.
- `src/energy_calculator/utils/types.py` — enums/dataclasses shared across
  the package (`RateName`, `ReadType`, `RatePeriod`, `Weekday`, `HDFData`,
  `CostingType`).
- `src/energy_calculator/utils/helper_funcs.py` — CLI arg validation/date
  parsing and the `squash_data` helper that flattens per-weekday data for
  `tabulate`.
- `tests/` — pytest suite (`test_hdf_parser.py`, `test_helper_funcs.py`).
- `costing.json` (repo root) — example/default costing file used when
  `--costing` is passed without `--costing-file`.

## Required checks

Before considering any change complete, run:

```bash
uv run pytest
uv run ruff check
uv run ruff format --check
uv run ty check
```

These mirror the local git hooks in `prek.toml` (via `prek`, a Rust
pre-commit-style hook runner) — `ruff-check`, `ruff-format --check`, `ty`,
plus the builtin `trailing-whitespace` / `end-of-file-fixer` / `check-yaml` /
`check-json` / `check-added-large-files` hooks that run on commit. There is
no CI workflow in this repo, so these local checks are the only gate — treat
them as mandatory rather than optional.

## Conventions

- Ruff is configured with `lint.extend-select = ["I"]` (import sorting) on
  top of defaults — keep imports sorted and let `ruff format` own
  formatting; don't hand-format.
- Type-checked with `ty` (not mypy, despite the stale `.mypy_cache/`
  directory in the repo root — that's leftover local state, not config).
  Add/keep type annotations consistent with the existing style (class-level
  attribute annotations, `dict[str, X]`, `X | None`, etc.).
- New costing types must: add a `CostingType` enum member, a corresponding
  `*.schema.json` in `src/energy_calculator/schema/`, a `Costing` subclass
  registered in `CostingFactory.costing_type_to_class`, and validation
  coverage — `Costing.validate_args` resolves the schema filename from
  `costing_type.value`, so the enum value and schema filename must match.

## Notes / open questions for maintainers

- `HDFParser.rates`, `weekday_import_kwh` and `total_import`/`total_export`
  are declared as **class-level** attributes (not set in `__init__`), so
  multiple `HDFParser` instances would share the same dict unless this is
  intentional single-instance-per-process usage. Worth confirming before
  writing code that instantiates more than one `HDFParser` in the same
  process (e.g. tests, or a future library/batch use case).
- `helper_funcs.validate_args` forcing `args.rates = True` whenever `--hours`
  is not passed is intentional: rates output is the default, and `--hours`
  is the only way to opt into hourly output instead.
