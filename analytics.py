import numpy as np
import pandas as pd

"""Public-safe workforce analytics example.

This script expects a sanitized employee export and does not require any
company-specific identifiers. The default sample file is generic and safe to
share.
"""

# =============================================================
# 1. Load Data
# =============================================================
file_path = "sample_employee_export.csv"
df = pd.read_csv(file_path)

df["Hire date"] = pd.to_datetime(df["Hire date"])
df["Termination date"] = pd.to_datetime(df["Termination date"])
df["Birth date"] = pd.to_datetime(df["Birth date"])

# Interns vs. FTEs Logic
# Headcount = 1, FTE = 0.0
# FTE = Wochenstunden / 40.0
df["is_intern"] = df["Position"].isin(["Intern", "Student"])
df["FTE"] = np.where(df["is_intern"], 0.0, df["Weekly hours"] / 40.0)


# My Snapshot
def map_slide_category(row):
    div = str(row["Division"])
    dept = str(row["Department"])
    if "People & Culture" in dept or "HR" in dept:
        return "HR"
    elif "TECH" in div or "Technology" in dept or "IT" in dept:
        return "Tech"
    elif "Index Operations" in div:
        return "Operations"
    elif "Index" in div or "Index" in dept:
        return "Index"
    return "Other Functions"


df["Slide_Category"] = df.apply(map_slide_category, axis=1)

# Active + Leave
df_active = df[df["Status"].isin(["Active", "Leave"])].copy()

# Gender
df_active["Gender_Clean"] = (
    df_active["Gender"].fillna("Others").replace({"Undefined": "Others"})
)

# =============================================================
# 2. DOB Calculation
# =============================================================
ref_date = pd.to_datetime("2026-10-18")


def get_age(birth_date, ref):
    if pd.isnull(birth_date):
        return np.nan
    return (
        ref.year
        - birth_date.year
        - ((ref.month, ref.day) < (birth_date.month, birth_date.day))
    )


df_active["Calculated_Age"] = df_active["Birth date"].apply(
    lambda b: get_age(b, ref_date)
)

avg_age = df_active["Calculated_Age"].mean()
median_age = df_active["Calculated_Age"].median()

df_active["Age_Bracket"] = pd.cut(
    df_active["Calculated_Age"],
    bins=[0, 25, 35, 45, 150],
    labels=["18-25", "26-35", "36-45", "45+"],
    right=True,
)
df_active["Age_Bracket_Display"] = (
    df_active["Age_Bracket"].astype(str).replace({"nan": "Unknown / Missing"})
)

# =============================================================
# Headcount & FTE KPIs
# =============================================================
tot_active_workforce = int(len(df_active))
tot_regular_staff = int((~df_active["is_intern"]).sum())
tot_interns_students = int(df_active["is_intern"].sum())
tot_active_only = int((df["Status"] == "Active").sum())
tot_on_leave = int((df["Status"] == "Leave").sum())
tot_all_records = int(len(df))
tot_ftes = int(round(df_active["FTE"].sum()))

t0_total_summary = pd.DataFrame(
    {
        "Workforce Metric": [
            "Total Active Workforce Headcount (Active + Leave)",
            "  - Regular Staff Headcount (Eligible for FTE)",
            "  - Interns & Working Students Headcount",
            "Active Status Only (Excluding Leave)",
            "On Leave Headcount",
            "Total Calculated FTEs (Regular Staff - Rounded)",
            "Average Age of Workforce (Years)",
            "Median Age of Workforce (Years)",
            "Total Recorded in File (Including Inactive/Past)",
        ],
        "Count / Value": [
            tot_active_workforce,
            tot_regular_staff,
            tot_interns_students,
            tot_active_only,
            tot_on_leave,
            tot_ftes,
            round(avg_age, 2),
            round(median_age, 1),
            tot_all_records,
        ],
    }
)

# =============================================================
# Headcount for Map-Chart
# =============================================================
iso3_translation = {
    "Deutschland": "DEU",
    "Indien": "IND",
    "Russische Föderation": "RUS",
    "Italien": "ITA",
    "Marokko": "MAR",
    "Türkei": "TUR",
    "Frankreich": "FRA",
    "Pakistan": "PAK",
    "Iran": "IRN",
    "Ceuta": "ESP",
    "Tibet": "CHN",
    "Hongkong": "HKG",
    "Vereinigte Staaten": "USA",
    "Kanada": "CAN",
    "Kolumbien": "COL",
    "Bulgarien": "BGR",
    "Armenien": "ARM",
    "Österreich": "AUT",
    "Albanien": "ALB",
    "Ecuador": "ECU",
    "Mexiko": "MEX",
    "Brasilien": "BRA",
    "Schweiz": "CHE",
    "Vietnam": "VNM",
    "Nigeria": "NGA",
    "Rumänien": "ROU",
    "Irland": "IRL",
    "Südafrika": "ZAF",
    "Niederlande": "NLD",
    "Kirgisistan": "KGZ",
    "Jordanien": "JOR",
    "Australien": "AUS",
    "Weißrussland": "BLR",
    "Syrien": "SYR",
    "Bolivien": "BOL",
    "Aserbaidschan": "AZE",
    "Ruanda": "RWA",
    "Tunesien": "TUN",
    "Griechenland": "GRC",
    "Libanon": "LBN",
    "Palästinensische Gebiete": "PSE",
    "Philippinen": "PHL",
    "Polen": "POL",
    "Bangladesch": "BGD",
    "Schweden": "SWE",
    "Estland": "EST",
    "Norwegen": "NOR",
    "Kuba": "CUB",
    "Kroatien": "HRV",
    "Taiwan": "TWN",
}

df_active["Country_ISO3"] = df_active["Nationality"].map(iso3_translation)
t1_nationality = df_active["Country_ISO3"].value_counts().reset_index()
t1_nationality.columns = ["Country_ISO3", "Headcount"]

# =============================================================
# Historical Data
# =============================================================
locations = [
    "City A",
    "City B",
    "City C",
    "City D",
    "City E",
    "City F",
]
dates = [("2024", "2024-12-31"), ("2025", "2025-12-31"), ("YTD", "2026-09-30")]


def get_historical_snapshot(as_of_date):
    sub = df[
        (df["Hire date"] <= as_of_date)
        & (
            (df["Termination date"].isna())
            | (df["Termination date"] > as_of_date)
        )
    ].copy()
    return sub


t2_rows = []
for loc in locations:
    for yr_label, dt in dates:
        snap = get_historical_snapshot(dt)
        loc_snap = snap[snap["Workplace"] == loc]
        t2_rows.append(
            {
                "Location": loc,
                "Year": yr_label,
                "FTEs": int(round(loc_snap["FTE"].sum())),
                "Interns": int(loc_snap["is_intern"].sum()),
                "Total Headcount": int(len(loc_snap)),
            }
        )
t2_location_trend = pd.DataFrame(t2_rows)

# =============================================================
# Divisions (FTEs, Interns, Headcount)
# =============================================================
t3_division = (
    df_active.groupby(df_active["Division"].fillna("Unassigned"))
    .agg(
        FTEs=("FTE", lambda x: int(round(x.sum()))),
        Interns=("is_intern", "sum"),
        Total_Headcount=("Status", "count"),
    )
    .reset_index()
    .rename(columns={"Division": "Division / Function"})
)

total_div_row = pd.DataFrame(
    {
        "Division / Function": ["Total"],
        "FTEs": [int(round(t3_division["FTEs"].sum()))],
        "Interns": [int(t3_division["Interns"].sum())],
        "Total_Headcount": [int(t3_division["Total_Headcount"].sum())],
    }
)
t3_division = pd.concat([t3_division, total_div_row], ignore_index=True)

# =============================================================
# Gender Data
# =============================================================
t5_gender = df_active["Gender_Clean"].value_counts().reset_index()
t5_gender.columns = ["Gender", "Headcount"]
total_gender_row = pd.DataFrame(
    {"Gender": ["Total"], "Headcount": [int(t5_gender["Headcount"].sum())]}
)
t5_gender = pd.concat([t5_gender, total_gender_row], ignore_index=True)

# =============================================================
# Age Matrix
# =============================================================
t6_age_gender = (
    pd.crosstab(
        df_active["Age_Bracket_Display"],
        df_active["Gender_Clean"],
        margins=True,
        margins_name="Total",
    )
    .reset_index()
    .rename(columns={"Age_Bracket_Display": "Age Bracket"})
)

for col in ["Female", "Male", "Others"]:
    if col not in t6_age_gender.columns:
        t6_age_gender[col] = 0
t6_age_gender = t6_age_gender[
    ["Age Bracket", "Female", "Male", "Others", "Total"]
]

# =============================================================
# Workforce Share (FTEs vs. Interns)
# =============================================================
t7_share = pd.DataFrame(
    {
        "Category": ["FTEs", "Interns", "Total Active Workforce"],
        "Count / Value": [tot_ftes, tot_interns_students, tot_active_workforce],
        "Share (%)": [
            int(round((tot_ftes / (tot_ftes + tot_interns_students)) * 100)),
            int(
                round(
                    (tot_interns_students / (tot_ftes + tot_interns_students))
                    * 100
                )
            ),
            100,
        ],
    }
)

# =============================================================
# Quarterly Snapshot (People Joined & People Left)
# =============================================================
q3_start = "2026-07-01"
q3_end = "2026-09-30"

joined_q3 = df[
    (df["Hire date"] >= q3_start) & (df["Hire date"] <= q3_end)
].copy()
left_q3 = df[
    (df["Termination date"] >= q3_start) & (df["Termination date"] <= q3_end)
].copy()

categories_order = ["Index", "Tech", "HR", "Operations", "Other Functions"]

t8_joined = (
    joined_q3.groupby("Slide_Category")
    .agg(
        Interns=("is_intern", lambda x: int(x.sum())),
        FTEs=("FTE", lambda x: int(round(x.sum()))),
    )
    .reindex(categories_order)
    .fillna(0)
    .astype(int)
    .reset_index()
    .rename(columns={"Slide_Category": "Department"})
)

t9_left = (
    left_q3.groupby("Slide_Category")
    .agg(
        Interns=("is_intern", lambda x: int(x.sum())),
        FTEs=("FTE", lambda x: int(round(x.sum()))),
    )
    .reindex(categories_order)
    .fillna(0)
    .astype(int)
    .reset_index()
    .rename(columns={"Slide_Category": "Department"})
)

# =============================================================
# Quick Report
# =============================================================
tables = {
    "0. TOTAL HEADCOUNT & KPI SUMMARY": t0_total_summary,
    "1. COUNTRY HEADCOUNT (ISO-3 CODES)": t1_nationality,
    "2. LOCATION BY YEAR & YTD": t2_location_trend,
    "3 & 4. DIVISION BREAKDOWN": t3_division,
    "5. GENDER BREAKDOWN": t5_gender,
    "6. AGE BY GENDER MATRIX": t6_age_gender,
    "7. FTEs VS INTERNS SHARE": t7_share,
    f"8. Q3 2026 PEOPLE JOINED (Total: {len(joined_q3)})": t8_joined,
    f"9. Q3 2026 PEOPLE LEFT (Total: {len(left_q3)})": t9_left,
}

for title, tbl in tables.items():
    print(f"\n{'='*25} {title} {'='*25}")
    print(tbl.to_string(index=False))

# =============================================================
# Export for Charting (Custom Sol PPT)
# =============================================================
output_excel = "analytics_visualization_tables.xlsx"
with pd.ExcelWriter(output_excel, engine="openpyxl") as writer:
    t0_total_summary.to_excel(
        writer, sheet_name="Headcount_KPIs", index=False
    )
    t1_nationality.to_excel(writer, sheet_name="Country_Map", index=False)
    t2_location_trend.to_excel(
        writer, sheet_name="Location_Trend", index=False
    )
    t3_division.to_excel(writer, sheet_name="Divisions", index=False)
    t5_gender.to_excel(writer, sheet_name="Gender", index=False)
    t6_age_gender.to_excel(writer, sheet_name="Age_by_Gender", index=False)
    t7_share.to_excel(writer, sheet_name="Workforce_Share", index=False)
    t8_joined.to_excel(writer, sheet_name="Q3_Joined", index=False)
    t9_left.to_excel(writer, sheet_name="Q3_Left", index=False)

print(
    f"\n--> Erfolgreich ausgeführt! Alle Tabellen wurden in '{output_excel}' gespeichert."
)