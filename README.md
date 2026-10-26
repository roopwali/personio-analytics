# Workforce Analytics Demo

This repository is a public-safe template for HR and recruiting analytics. It demonstrates how to calculate summary metrics from anonymized employee and candidate data without exposing private company information.

## What is included

- analytics.py: employee workforce summary metrics such as headcount, FTE, age bands, and regional breakdowns
- kpi.py: recruiting funnel analysis for CSV or Excel exports
- kpi-new.py: quarter-based recruiting report using event-style logic

## Features

- load HR or recruiting exports from CSV/Excel files
- normalize date and status fields
- calculate headcount and FTE trends
- summarize age, gender, and location distributions
- evaluate hiring funnel performance and conversion rates
- generate reporting tables for analysis or demos

## Requirements

- Python 3.9+
- pandas
- numpy
- openpyxl

Install dependencies:

```bash
pip install pandas numpy openpyxl
```

## Public-safe usage

This project is intended for sanitized demo data. Use an anonymized export or the included sample files.

```bash
python analytics.py
python kpi.py sample_recruiting_export.csv
python kpi-new.py sample_recruiting_export.csv
```

## Sample data

The repository includes public-safe example files for demonstration purposes. These examples use generic values and avoid personal or company-specific details.

## Data privacy note

Do not use real employee or candidate records in this repository unless your environment has strict governance controls.

Avoid publishing:

- names or personal identifiers
- email addresses or phone numbers
- exact birth dates or hire dates
- precise office locations tied to individuals
- salary or compensation details
- candidate records with identifiable metadata

Instead, prefer:

- age bands
- tenure bands
- function groups
- region-level summaries
- aggregated counts and percentages

## License

This project is for demonstration and analytics learning purposes. It is not intended to store or expose real employee records.
