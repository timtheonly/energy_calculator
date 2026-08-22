# energy_calculator
Parses an ESB networks HDF (Harmonised Downloadable File) file into a human readable format. Providing a breakdown by weekday and rate periods e.g. day, night, peak.
Can be used as a library or command line script.

```bash
energy_calculator -h
usage: EnergyCalculator [-h] [--start START] [--end END] [--costing] [--costing-file COSTING_FILE] [--rates | --hours] filename

Parses an ESB networks HDF file into a human readable format

positional arguments:
  filename              File containing HDF csv data

options:
  -h, --help            show this help message and exit
  --start START         Date to start calculations from e.g. 01-01-2025
  --end END             Date to stop calculations at e.g. 01-01-2025
  --costing             calculate cost using rates set out in costing.json
  --costing-file, --cf COSTING_FILE file to use for costing data, overrides costing.json
  --rates               Display data in day, peak and night periods
  --hours               Display data as an hourly breakdown
```

Costing models currently supported:
- 24hr: you pay the same rate all day
- Day night peak: your rate changes depending on the time of day
- Custom: your rate is variable

example 24hr costing.json:
```json
{
    "costing_type": "24hr",
    "import" : 0.2837,
    "export" : 0.195
}
```

example day night peak costing.json:
```json
{
    "costing_type": "day_peak_night",
    "rates" : {
        "day": 0.2837,
        "peak": 0.3356,
        "night": 0.2048,
        "export": 0.195
    }
}
```

example of custom.json where weekends are cheaper than the rest of the week:
```json
{
    "costing_type": "custom",
    "rates" : {
        "day": 0.2837,
        "peak": 0.3356,
        "night": 0.2048,
        "export": 0.195
    },
    "overrides": [
      {
        "saturday": {
          "base_rate": 0.2048
        }
      },
      {
        "sunday": {
          "base_rate": 0.2048
        }
      }
    ]
}
```
