import io
import json
from datetime import datetime, timezone

import pandas as pd
import streamlit as st


# --------------------------------------------------
# DATAMEDIC | DATA QUALITY & REPAIR STUDIO
# --------------------------------------------------

APP_NAME = "DataMedic"
MAX_FILE_SIZE_MB = 50
SUPPORTED_FORMATS = ["csv", "xlsx"]


st.set_page_config(
    page_title="DataMedic | Data Quality Studio",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="expanded",
)


# --------------------------------------------------
# PROFESSIONAL UI STYLING
# --------------------------------------------------

st.markdown(
    """
    <style>
    .stApp {
        background: linear-gradient(135deg, #f7f9fc 0%, #edf3fa 100%);
    }

    [data-testid="stSidebar"] {
        background-color: #101c32;
    }

    [data-testid="stSidebar"] * {
        color: #f1f5f9;
    }

    .hero {
        padding: 1.4rem 1.6rem;
        border-radius: 18px;
        background: linear-gradient(120deg, #142642, #245b73);
        color: white;
        margin-bottom: 1rem;
    }

    .hero h1 {
        margin: 0;
        font-size: 2.2rem;
        font-weight: 750;
    }

    .hero p {
        margin-top: 0.5rem;
        margin-bottom: 0;
        color: #dbeafe;
    }

    div[data-testid="stMetric"] {
        background-color: white;
        padding: 1rem;
        border: 1px solid #e0e8f0;
        border-radius: 14px;
        box-shadow: 0 3px 12px rgba(15, 23, 42, 0.04);
    }

    .stButton button,
    .stDownloadButton button {
        border-radius: 9px;
        font-weight: 600;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# --------------------------------------------------
# SAMPLE DATA FOR DEMONSTRATION
# --------------------------------------------------

def create_demo_data():
    """Create a small dataset containing common data-quality issues."""

    return pd.DataFrame(
        {
            "Order_ID": [
                1001, 1002, 1001, 1004, 1005, 1006, 1007, 1008
            ],
            "Customer": [
                " Arun Kumar ",
                "Priya S",
                "Arun Kumar",
                "Karthik",
                "Meena",
                "",
                "Priya S",
                "Karthik",
            ],
            "City": [
                "chennai",
                "Madurai",
                "CHENNAI",
                "Madurai",
                "Chennai",
                "Coimbatore",
                "MADURAI",
                "Chennai",
            ],
            "Amount": [
                1200, 850, 1200, 450, None, 320, 850, 450
            ],
            "Email": [
                "arun@example.com",
                "priya@example.com",
                "arun@example.com",
                "karthik@example.com",
                "meena@example.com",
                "unknown@example.com",
                "priya@example.com",
                "karthik@example.com",
            ],
            "Order_Date": [
                "2026-10-01",
                "2026-10-02",
                "2026-10-01",
                "2026-10-03",
                "2026-10-04",
                "2026-10-05",
                "2026-10-02",
                "2026-10-03",
            ],
        }
    )


# --------------------------------------------------
# FILE READING
# --------------------------------------------------

def read_uploaded_data(uploaded_file):
    """Read a supported file into a pandas DataFrame."""

    file_bytes = uploaded_file.getvalue()

    if len(file_bytes) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise ValueError(
            f"File is too large. Please upload a file smaller than "
            f"{MAX_FILE_SIZE_MB} MB."
        )

    filename = uploaded_file.name.lower()

    if filename.endswith(".csv"):
        errors = []

        # Try common encodings for CSV files.
        for encoding in ["utf-8-sig", "utf-8", "cp1252"]:
            try:
                return pd.read_csv(
                    io.BytesIO(file_bytes),
                    encoding=encoding,
                    sep=None,
                    engine="python",
                )
            except Exception as error:
                errors.append(str(error))

        raise ValueError(
            "Unable to read this CSV file. Check that the file is valid "
            "and uses a supported text encoding."
        )

    if filename.endswith(".xlsx"):
        workbook = pd.ExcelFile(
            io.BytesIO(file_bytes),
            engine="openpyxl",
        )

        if not workbook.sheet_names:
            raise ValueError("No worksheets were found in this Excel file.")

        sheet_name = st.sidebar.selectbox(
            "Select worksheet",
            options=workbook.sheet_names,
        )

        return pd.read_excel(
            io.BytesIO(file_bytes),
            sheet_name=sheet_name,
            engine="openpyxl",
        )

    raise ValueError("Unsupported format. Upload a CSV or XLSX file.")


# --------------------------------------------------
# DATA PREPARATION AND ANALYSIS
# --------------------------------------------------

def normalize_blank_strings(dataframe):
    """Interpret empty strings and whitespace-only text as missing values."""

    result = dataframe.copy(deep=True)

    for column in result.columns:
        if (
            pd.api.types.is_object_dtype(result[column].dtype)
            or pd.api.types.is_string_dtype(result[column].dtype)
        ):
            result[column] = result[column].map(
                lambda value: (
                    pd.NA
                    if isinstance(value, str) and not value.strip()
                    else value
                )
            )

    return result


def get_text_columns(dataframe):
    """Return columns that contain text values."""

    return [
        column
        for column in dataframe.columns
        if (
            pd.api.types.is_object_dtype(dataframe[column].dtype)
            or pd.api.types.is_string_dtype(dataframe[column].dtype)
        )
    ]


def build_column_profile(dataframe):
    """Build a data-quality profile for every column."""

    profile = []

    for column in dataframe.columns:
        series = dataframe[column]
        missing_count = int(series.isna().sum())

        try:
            unique_count = int(series.nunique(dropna=True))
        except (TypeError, ValueError):
            unique_count = -1

        profile.append(
            {
                "Column": str(column),
                "Data type": str(series.dtype),
                "Missing values": missing_count,
                "Missing (%)": round(
                    missing_count / len(dataframe) * 100, 2
                ) if len(dataframe) else 0,
                "Unique values": unique_count,
            }
        )

    return pd.DataFrame(profile)


# --------------------------------------------------
# CLEANING ENGINE
# --------------------------------------------------

def apply_cleaning(
    source,
    trim_whitespace,
    casing_columns,
    casing_method,
    missing_strategy,
    custom_missing_value,
    remove_duplicates,
    drop_empty_columns,
):
    """
    Apply explicitly selected cleaning rules.

    The original uploaded DataFrame remains unchanged.
    """

    dataframe = normalize_blank_strings(source)
    change_log = []

    change_log.append(
        "Blank and whitespace-only cells were treated as missing values."
    )

    # Rule 1: Trim unnecessary whitespace.
    if trim_whitespace:
        trimmed_cells = 0

        for column in dataframe.columns:
            original_values = dataframe[column].copy()

            dataframe[column] = dataframe[column].map(
                lambda value: value.strip()
                if isinstance(value, str)
                else value
            )

            trimmed_cells += sum(
                1
                for old, new in zip(
                    original_values, dataframe[column]
                )
                if isinstance(old, str)
                and isinstance(new, str)
                and old != new
            )

        change_log.append(
            f"Trimmed surrounding whitespace in {trimmed_cells} cell(s)."
        )

    # Rule 2: Standardize case only in columns selected by the user.
    valid_case_columns = [
        column
        for column in casing_columns
        if column in dataframe.columns
    ]

    changed_case_cells = 0

    for column in valid_case_columns:
        def standardize_case(value):
            if not isinstance(value, str):
                return value

            if casing_method == "Title Case":
                return value.title()

            if casing_method == "lowercase":
                return value.lower()

            if casing_method == "UPPERCASE":
                return value.upper()

            return value

        before_values = dataframe[column].copy()
        dataframe[column] = dataframe[column].map(standardize_case)

        changed_case_cells += sum(
            1
            for old, new in zip(before_values, dataframe[column])
            if isinstance(old, str)
            and isinstance(new, str)
            and old != new
        )

    if valid_case_columns:
        change_log.append(
            f"Standardized text casing in {changed_case_cells} cell(s)."
        )

    # Rule 3: Remove columns that contain no usable values.
    if drop_empty_columns:
        empty_columns = [
            column
            for column in dataframe.columns
            if dataframe[column].isna().all()
        ]

        if empty_columns:
            dataframe = dataframe.drop(columns=empty_columns)
            change_log.append(
                "Removed fully empty column(s): "
                + ", ".join(map(str, empty_columns))
                + "."
            )
        else:
            change_log.append("No fully empty columns were found.")

    # Rule 4: Handle missing values according to the selected strategy.
    missing_before = int(dataframe.isna().sum().sum())

    if missing_strategy == "Fill numeric with median and other columns with mode":
        filled_cells = 0

        for column in dataframe.columns:
            if not dataframe[column].isna().any():
                continue

            missing_in_column = int(dataframe[column].isna().sum())

            if pd.api.types.is_numeric_dtype(dataframe[column]):
                median_value = dataframe[column].median()

                if pd.notna(median_value):
                    dataframe[column] = dataframe[column].fillna(median_value)
                    filled_cells += missing_in_column
            else:
                available_modes = dataframe[column].mode(dropna=True)

                if not available_modes.empty:
                    fill_value = available_modes.iloc[0]
                else:
                    fill_value = "Unknown"

                dataframe[column] = dataframe[column].fillna(fill_value)
                filled_cells += missing_in_column

        change_log.append(
            f"Filled {filled_cells} missing cell(s) using median or mode "
            "where possible."
        )

    elif missing_strategy == "Drop rows containing missing values":
        rows_before = len(dataframe)
        dataframe = dataframe.dropna().reset_index(drop=True)
        rows_removed = rows_before - len(dataframe)

        change_log.append(
            f"Removed {rows_removed} row(s) containing missing values."
        )

    elif missing_strategy == "Fill missing cells with a custom value":
        if custom_missing_value.strip():
            dataframe = dataframe.fillna(custom_missing_value)
            change_log.append(
                "Filled missing cells with the selected custom value."
            )
        else:
            change_log.append(
                "Custom value was empty; missing cells were not changed."
            )

    else:
        change_log.append("Missing values were left unchanged.")

    # Rule 5: Remove exact duplicate records after other selected rules.
    if remove_duplicates:
        duplicates_removed = int(dataframe.duplicated().sum())

        dataframe = dataframe.drop_duplicates().reset_index(drop=True)

        change_log.append(
            f"Removed {duplicates_removed} duplicate row(s)."
        )
    else:
        change_log.append("Duplicate rows were retained.")

    dataframe = dataframe.reset_index(drop=True)

    return dataframe, change_log


# --------------------------------------------------
# SIDEBAR: DATA SOURCE
# --------------------------------------------------

with st.sidebar:
    st.markdown("## 🧪 DataMedic")
    st.caption("Data Quality & Repair Studio")
    st.divider()

    source_mode = st.radio(
        "Choose data source",
        ["Explore demo dataset", "Upload your file"],
    )

    uploaded_file = None

    if source_mode == "Upload your file":
        uploaded_file = st.file_uploader(
            "Upload CSV or Excel",
            type=SUPPORTED_FORMATS,
            help="Supported formats: .csv and .xlsx. Maximum size: 50 MB.",
        )


# --------------------------------------------------
# LOAD DATA
# --------------------------------------------------

if source_mode == "Explore demo dataset":
    raw_dataframe = create_demo_data()
    source_filename = "datamedic_demo.csv"

else:
    if uploaded_file is None:
        st.markdown(
            """
            <div class="hero">
                <h1>🧪 DataMedic</h1>
                <p>Inspect, clean, validate, and export your data with confidence.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.info(
            "Upload a CSV or XLSX file from the sidebar to begin. "
            "You can also select 'Explore demo dataset' to try the features."
        )

        st.stop()

    source_filename = uploaded_file.name

    try:
        raw_dataframe = read_uploaded_data(uploaded_file)
    except Exception as error:
        st.error(f"Could not load the file: {error}")
        st.stop()


if raw_dataframe.empty:
    st.warning("The selected file contains no data rows.")
    st.stop()

if len(raw_dataframe.columns) == 0:
    st.warning("No columns were found in the selected file.")
    st.stop()


# --------------------------------------------------
# SIDEBAR: CLEANING SETTINGS
# --------------------------------------------------

with st.sidebar:
    st.divider()
    st.subheader("⚙️ Cleaning rules")

    trim_whitespace = st.checkbox(
        "Trim surrounding whitespace",
        value=True,
    )

    remove_duplicates = st.checkbox(
        "Remove duplicate rows",
        value=True,
    )

    drop_empty_columns = st.checkbox(
        "Remove fully empty columns",
        value=False,
    )

    text_columns = get_text_columns(raw_dataframe)

    casing_columns = st.multiselect(
        "Columns to standardize",
        options=text_columns,
        default=[],
        help="Select only the text columns you want to standardize.",
    )

    casing_method = st.selectbox(
        "Text format",
        ["Title Case", "lowercase", "UPPERCASE"],
    )

    missing_strategy = st.selectbox(
        "Missing value strategy",
        [
            "Keep missing values",
            "Fill numeric with median and other columns with mode",
            "Drop rows containing missing values",
            "Fill missing cells with a custom value",
        ],
    )

    custom_missing_value = "Not provided"

    if missing_strategy == "Fill missing cells with a custom value":
        custom_missing_value = st.text_input(
            "Replacement value",
            value="Not provided",
        )

    st.caption("Settings update the cleaned preview automatically.")


# --------------------------------------------------
# RUN THE CLEANING ENGINE
# --------------------------------------------------

prepared_raw = normalize_blank_strings(raw_dataframe)

cleaned_dataframe, change_log = apply_cleaning(
    source=raw_dataframe,
    trim_whitespace=trim_whitespace,
    casing_columns=casing_columns,
    casing_method=casing_method,
    missing_strategy=missing_strategy,
    custom_missing_value=custom_missing_value,
    remove_duplicates=remove_duplicates,
    drop_empty_columns=drop_empty_columns,
)


# --------------------------------------------------
# COMPUTE QUALITY METRICS
# --------------------------------------------------

rows_before = int(len(prepared_raw))
rows_after = int(len(cleaned_dataframe))

columns_before = int(len(prepared_raw.columns))
columns_after = int(len(cleaned_dataframe.columns))

missing_before = int(prepared_raw.isna().sum().sum())
missing_after = int(cleaned_dataframe.isna().sum().sum())

duplicates_before = int(prepared_raw.duplicated().sum())
duplicates_after = int(cleaned_dataframe.duplicated().sum())

total_cells = int(prepared_raw.shape[0] * prepared_raw.shape[1])

completeness = (
    round((total_cells - missing_before) / total_cells * 100, 1)
    if total_cells
    else 100.0
)


# --------------------------------------------------
# MAIN HEADER
# --------------------------------------------------

st.markdown(
    """
    <div class="hero">
        <h1>🧪 DataMedic</h1>
        <p>Data Quality & Repair Studio</p>
        <p>Discover data issues. Apply safe corrections. Export cleaner data.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

st.caption(
    f"Source: {source_filename} · "
    f"Format: {source_filename.rsplit('.', 1)[-1].upper()}"
)

st.info(
    "Data handling: this app does not intentionally save uploaded files to "
    "disk or send them to external APIs. When hosted online, files are "
    "processed by the hosting server. Avoid uploading sensitive information "
    "unless you trust the hosting environment."
)


# --------------------------------------------------
# QUALITY SUMMARY
# --------------------------------------------------

metric_1, metric_2, metric_3, metric_4, metric_5 = st.columns(5)

metric_1.metric("Rows", f"{rows_before:,}")
metric_2.metric("Columns", f"{columns_before:,}")
metric_3.metric("Missing cells", f"{missing_before:,}")
metric_4.metric("Duplicate rows", f"{duplicates_before:,}")
metric_5.metric("Completeness", f"{completeness:.1f}%")


# --------------------------------------------------
# TABS
# --------------------------------------------------

overview_tab, preview_tab, results_tab, export_tab = st.tabs(
    [
        "📊 Overview",
        "🔎 Data Preview",
        "🧹 Cleaning Results",
        "📥 Export & Audit",
    ]
)


# --------------------------------------------------
# OVERVIEW TAB
# --------------------------------------------------

with overview_tab:
    st.subheader("Data quality overview")
    st.write(
        "Review the detected data-quality issues before using the cleaned data."
    )

    issue_count = 0

    if missing_before:
        st.warning(
            f"Found {missing_before:,} missing cell(s). "
            "Choose a missing-value strategy in the sidebar."
        )
        issue_count += 1

    if duplicates_before:
        st.warning(
            f"Found {duplicates_before:,} exact duplicate row(s) "
            "before cleaning."
        )
        issue_count += 1

    missing_columns = prepared_raw.columns[
        prepared_raw.isna().any()
    ].tolist()

    if missing_columns:
        with st.expander("Columns containing missing values"):
            for column in missing_columns:
                missing_count = int(prepared_raw[column].isna().sum())
                st.write(f"**{column}** — {missing_count} missing value(s)")

    if issue_count == 0:
        st.success(
            "No missing cells or exact duplicate rows were detected "
            "in the loaded dataset."
        )

    st.subheader("Column profile")

    profile_dataframe = build_column_profile(prepared_raw)

    st.dataframe(
        profile_dataframe,
        use_container_width=True,
        hide_index=True,
    )

    if not profile_dataframe.empty:
        missing_chart_data = (
            profile_dataframe
            .set_index("Column")["Missing values"]
        )

        missing_chart_data = missing_chart_data[
            missing_chart_data > 0
        ].sort_values(ascending=False)

        if not missing_chart_data.empty:
            st.subheader("Missing values by column")
            st.bar_chart(missing_chart_data)
        else:
            st.caption("There are no missing values to chart.")


# --------------------------------------------------
# DATA PREVIEW TAB
# --------------------------------------------------

with preview_tab:
    st.subheader("Before and after")

    st.caption(
        "The original data remains unchanged. Cleaning rules are applied "
        "to a separate working copy."
    )

    before_column, after_column = st.columns(2)

    with before_column:
        st.markdown("**Original data**")
        st.dataframe(
            raw_dataframe.head(100),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            f"Showing up to 100 rows · {len(raw_dataframe):,} total rows"
        )

    with after_column:
        st.markdown("**Cleaned preview**")
        st.dataframe(
            cleaned_dataframe.head(100),
            use_container_width=True,
            hide_index=True,
        )
        st.caption(
            f"Showing up to 100 rows · {len(cleaned_dataframe):,} total rows"
        )


# --------------------------------------------------
# CLEANING RESULTS TAB
# --------------------------------------------------

with results_tab:
    st.subheader("Cleaning summary")

    result_1, result_2, result_3, result_4 = st.columns(4)

    result_1.metric(
        "Rows removed",
        f"{max(rows_before - rows_after, 0):,}",
    )

    result_2.metric(
        "Columns removed",
        f"{max(columns_before - columns_after, 0):,}",
    )

    result_3.metric(
        "Missing before",
        f"{missing_before:,}",
    )

    result_4.metric(
        "Missing after",
        f"{missing_after:,}",
        delta=missing_before - missing_after,
        delta_color="normal",
    )

    st.markdown("### Applied rules")

    for log_entry in change_log:
        st.markdown(f"- {log_entry}")

    if cleaned_dataframe.empty:
        st.warning(
            "The current rules produced an empty dataset. "
            "Review the missing-value and duplicate settings."
        )
    else:
        st.markdown("### Cleaned data")
        st.dataframe(
            cleaned_dataframe.head(100),
            use_container_width=True,
            hide_index=True,
        )


# --------------------------------------------------
# EXPORT AND AUDIT TAB
# --------------------------------------------------

with export_tab:
    st.subheader("Export cleaned data")

    st.write(
        "Download the cleaned dataset and an audit report describing "
        "the selected cleaning rules and before/after counts."
    )

    audit_report = {
        "application": APP_NAME,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source_file": source_filename,
        "source_format": source_filename.rsplit(".", 1)[-1].lower(),
        "rows_before": rows_before,
        "rows_after": rows_after,
        "columns_before": columns_before,
        "columns_after": columns_after,
        "missing_cells_before": missing_before,
        "missing_cells_after": missing_after,
        "duplicate_rows_before": duplicates_before,
        "duplicate_rows_after": duplicates_after,
        "cleaning_rules": change_log,
    }

    csv_bytes = cleaned_dataframe.to_csv(
        index=False
    ).encode("utf-8-sig")

    excel_buffer = io.BytesIO()

    cleaned_dataframe.to_excel(
        excel_buffer,
        index=False,
        engine="openpyxl",
    )

    json_bytes = json.dumps(
        audit_report,
        indent=2,
        ensure_ascii=False,
    ).encode("utf-8")

    download_1, download_2, download_3 = st.columns(3)

    with download_1:
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name="datamedic_cleaned.csv",
            mime="text/csv",
            use_container_width=True,
        )

    with download_2:
        st.download_button(
            label="⬇️ Download Excel",
            data=excel_buffer.getvalue(),
            file_name="datamedic_cleaned.xlsx",
            mime=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    with download_3:
        st.download_button(
            label="⬇️ Download audit report",
            data=json_bytes,
            file_name="datamedic_audit_report.json",
            mime="application/json",
            use_container_width=True,
        )

    with st.expander("View audit report"):
        st.json(audit_report)

st.divider()

st.caption(
    "DataMedic · Data Quality & Repair Studio · "
    "Built with Python, Pandas and Streamlit"
)
