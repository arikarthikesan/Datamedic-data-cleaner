# DataMedic — Data Quality & Repair Studio

## Project Overview

DataMedic is a data quality and repair application designed to simplify the process of identifying, cleaning, and managing inconsistent datasets. It helps users improve data reliability by detecting missing values, identifying duplicate records, standardizing text formats, and applying configurable data-cleaning rules.

Developed using Python, Pandas, and Streamlit, DataMedic provides an interactive web interface that enables users to upload CSV and Excel files, inspect their data, review quality metrics, and apply cleaning operations without manually editing every record.

## Key Features

* **CSV and Excel File Support:** Upload datasets in CSV and XLSX formats for analysis and cleaning.
* **Data Quality Profiling:** Examine column data types, missing values, unique values, and overall data completeness.
* **Duplicate Detection and Removal:** Identify and remove exact duplicate records based on the selected cleaning settings.
* **Text Standardization:** Trim surrounding whitespace and standardize text values using title case, lowercase, or uppercase formatting.
* **Missing Value Management:** Retain missing values, fill them using selected strategies, or remove rows containing missing data.
* **Before-and-After Preview:** Compare the original dataset with the cleaned version before exporting the results.
* **Multiple Export Formats:** Download cleaned datasets as CSV or Excel files.
* **Audit Reporting:** Generate a JSON report containing cleaning operations and before-and-after data quality statistics.
* **Interactive Dashboard:** Access data profiles, cleaning summaries, and missing-value visualizations through a user-friendly interface.

## Technology Stack

* **Programming Language:** Python
* **Data Processing:** Pandas
* **Web Framework:** Streamlit
* **Excel Processing:** OpenPyXL
* **Data Formats:** CSV, XLSX, JSON
* **Version Control:** Git and GitHub

## How It Works

1. Upload a CSV or Excel dataset, or explore the included demonstration dataset.
2. Review the data quality profile and identify missing values or duplicate records.
3. Select the required cleaning rules and missing-value strategy.
4. Preview the changes and review the cleaning summary.
5. Export the cleaned dataset and its audit report for further analysis.

## Project Objective

The primary objective of DataMedic is to reduce repetitive manual data-cleaning work and make data quality issues easier to understand and manage. The project demonstrates practical applications of data processing, interactive web development, data validation concepts, and file handling.

## Future Enhancements

Potential improvements include advanced validation rules, configurable duplicate-matching techniques, reversible cleaning operations, automated test coverage, and support for additional file formats.

## Conclusion

DataMedic provides a practical foundation for data preparation and quality management. By combining configurable cleaning operations, visual data profiling, and downloadable audit reports, the application helps users prepare more consistent datasets for reporting, analytics, and other data-driven tasks.
