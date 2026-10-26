import pandas as pd
import numpy as np
import sys
import os
import warnings
warnings.filterwarnings('ignore')

def analyze_pipeline(csv_file):
    if not os.path.isfile(csv_file):
        print(f"Error: The file '{csv_file}' was not found.")
        sys.exit(1)
        
    print(f"--- Analyzing {csv_file} ---\n")
    
    # 0. Load the raw dataset
    df = pd.read_csv(csv_file)
    original_len = len(df)
    results = {}

    # Strip extra whitespace from column headers upfront
    df.columns = df.columns.str.strip()

    # 0.5 Filter out Intern and Student positions
    if 'Position name' in df.columns:
        intern_student_mask = df['Position name'].str.contains('Intern|Student', case=False, na=False)
        df = df[~intern_student_mask].copy() # remove ~ for filtering out Perm roles
        
        filtered_out = original_len - len(df)
        print(f"[*] Filtered out {filtered_out} applications tied to Intern/Student roles.\n")
    else:
        print("[!] Warning: 'Position name' column missing. Could not filter Interns/Students.\n")

    # Clean / Normalize LinkedIn Channels BEFORE creating subset copies
    if 'Application channel' in df.columns:
        df['Application channel_clean'] = df['Application channel'].astype(str).str.strip().replace({
            'Linkedin - organic': 'LinkedIn',
            'LinkedIn': 'LinkedIn'
        })

    # Convert dates to Datetime
    df['Application date'] = pd.to_datetime(df['Application date'], errors='coerce')
    if 'Days in current phase' in df.columns:
        df['Days in current phase'] = pd.to_numeric(df['Days in current phase'], errors='coerce')

    if 'Final status date' in df.columns:
        df['Final status date'] = pd.to_datetime(df['Final status date'], errors='coerce')
        end_date_col = 'Final status date'
    elif 'Final phase date' in df.columns:
        df['Final phase date'] = pd.to_datetime(df['Final phase date'], errors='coerce')
        end_date_col = 'Final phase date'
    else:
        end_date_col = None

    total_applications = len(df)

    # Dynamic status column identification ('Final status', 'Status', or 'Accepted')
    status_col = next((c for c in df.columns if c in ['Final status', 'Status'] or 'status' in c.lower()), None)
    
    cond_status = df[status_col].astype(str).str.strip().str.lower().isin(['accepted', 'hired']) if status_col else False
    cond_accepted = df['Accepted'].notna() if 'Accepted' in df.columns else False

    hired = df[cond_status | cond_accepted].copy()

    total_hires = len(hired)

    # Calculate Total Positions Opened
    if 'Position ID' in df.columns:
        total_positions = df['Position ID'].nunique()
    elif 'Position name' in df.columns:
        total_positions = df['Position name'].nunique()
    else:
        total_positions = "N/A"

    results['Total Applications'] = total_applications
    results['Total Positions Opened'] = total_positions
    results['Total Hires'] = total_hires

    # 1. Median Time-to-Hire
    if not hired.empty and end_date_col:
        hired['Time to Hire'] = (hired[end_date_col] - hired['Application date']).dt.days
        results['Median Time-to-Hire'] = f"{hired['Time to Hire'].median():.1f} days"
    else:
        results['Median Time-to-Hire'] = "N/A"

    # 2. Offer Acceptance Rate (OAR)
    if status_col:
        offers_extended = df[df['Offer'].notna() | (df[status_col].astype(str).str.strip().str.lower() == 'offer') | (df[status_col].astype(str).str.strip().str.lower() == 'accepted')] if 'Offer' in df.columns else df[df[status_col].astype(str).str.strip().str.lower().isin(['offer', 'accepted'])]
    else:
        offers_extended = df[df['Offer'].notna() | df['Accepted'].notna()]

    if len(offers_extended) > 0:
        results['Offer Acceptance Rate (OAR)'] = f"{(len(hired) / len(offers_extended)) * 100:.1f}% ({len(hired)} Hired / {len(offers_extended)} Offers)"
    else:
        results['Offer Acceptance Rate (OAR)'] = "N/A"

    # 3. Candidate Reallocation Rate (Cross-Pollination)
    if 'Initially applied for position' in df.columns and 'Position name' in df.columns:
        mask = df['Initially applied for position'].notna() & df['Position name'].notna()
        reallocated = df[mask][df[mask]['Initially applied for position'] != df[mask]['Position name']]
        realloc_count = len(reallocated)
        if total_applications > 0:
            results['Candidate Reallocation Rate (Cross-Pollination)'] = f"{realloc_count} candidates ({(realloc_count / total_applications) * 100:.2f}% of total applications)"
        else:
            results['Candidate Reallocation Rate (Cross-Pollination)'] = "N/A"
    else:
        results['Candidate Reallocation Rate (Cross-Pollination)'] = "N/A (Missing Position columns)"

    # 4. Screening Pass-Through Rate
    if 'Screening Round' in df.columns:
        entered_screening = df[df['Screening Round'].notna()]
        subsequent_rounds = ['Team Round', 'Management Round', 'Task round', 'Offer', 'Accepted']
        available_rounds = [col for col in subsequent_rounds if col in df.columns]
        
        if len(entered_screening) > 0 and available_rounds:
            passed_mask = entered_screening[available_rounds[0]].notna()
            for round_name in available_rounds[1:]:
                passed_mask = passed_mask | entered_screening[round_name].notna()
                
            passed_screening = entered_screening[passed_mask]
            pass_rate = (len(passed_screening) / len(entered_screening)) * 100
            results['Screening Pass-Through Rate'] = f"{len(passed_screening)} passed / {len(entered_screening)} screened ({pass_rate:.1f}%)"
        else:
            results['Screening Pass-Through Rate'] = "N/A"
    else:
        results['Screening Pass-Through Rate'] = "N/A"

    # 5. Candidate Drop-Off / Withdrawal Rate
    withdrawn_count = 0
    if 'Withdrawn' in df.columns:
        withdrawn_count = df['Withdrawn'].notna().sum()
    elif status_col:
        withdrawn_count = (df[status_col].astype(str).str.strip().str.lower() == 'withdrawn').sum()

    if total_applications > 0:
        withdrawal_rate = (withdrawn_count / total_applications) * 100
        results['Candidate Withdrawal Rate'] = f"{withdrawal_rate:.1f}% ({withdrawn_count} candidates voluntarily withdrew)"
    else:
        results['Candidate Withdrawal Rate'] = "N/A"

    # 6. Source/Channel Effectiveness
    if 'Application channel_clean' in df.columns:
        channel_apps = df['Application channel_clean'].value_counts()
        channel_hires = hired['Application channel_clean'].value_counts() if not hired.empty else pd.Series(dtype=int)
        
        channel_eff = pd.DataFrame({'Apps': channel_apps, 'Hires': channel_hires}).fillna(0)
        channel_eff['Conversion %'] = (channel_eff['Hires'] / channel_eff['Apps'] * 100).round(1)
        
        res_list = []
        for index, row in channel_eff.sort_values(by='Apps', ascending=False).head(10).iterrows():
            if index != 'nan':
                res_list.append(f"{index}: {int(row['Apps'])} Apps -> {int(row['Hires'])} Hires ({row['Conversion %']}%)")
        
        results['Top Sources/Channels'] = res_list
    else:
        results['Top Sources/Channels'] = "N/A"

    # 7. Top 5 Departments by Applications Received
    if 'Position department name' in df.columns:
        dept_counts = df['Position department name'].value_counts()
        dept_res_list = []
        for dept, count in dept_counts.head(5).items():
            pct = (count / total_applications) * 100
            dept_res_list.append(f"{dept}: {count:,} Apps ({pct:.1f}%)")
        results['Top 5 Departments by Applications'] = dept_res_list
    else:
        results['Top 5 Departments by Applications'] = "N/A (Missing Position department name column)"

    # 8. City-Level Metrics
    if 'Position workplace name' in df.columns:
        pos_col = 'Position ID' if 'Position ID' in df.columns else 'Position name'
        
        city_positions = df.groupby('Position workplace name')[pos_col].nunique() if pos_col in df.columns else pd.Series(dtype=int)
        city_apps = df.groupby('Position workplace name').size()
        
        if not hired.empty and end_date_col:
            hired['Time to Hire'] = (hired[end_date_col] - hired['Application date']).dt.days
            city_hires = hired.groupby('Position workplace name').size()
            city_tth = hired.groupby('Position workplace name')['Time to Hire'].median()
        else:
            city_hires = pd.Series(dtype=int)
            city_tth = pd.Series(dtype=float)

        city_stats_df = pd.DataFrame({
            'Positions': city_positions,
            'Applications': city_apps,
            'Filled (Hires)': city_hires,
            'Median TTH (Days)': city_tth
        }).fillna({'Positions': 0, 'Applications': 0, 'Filled (Hires)': 0}).astype({'Positions': int, 'Applications': int, 'Filled (Hires)': int})
        
        city_stats_df = city_stats_df.sort_values(by='Filled (Hires)', ascending=False)
        
        city_res_list = []
        for city, row in city_stats_df.iterrows():
            tth_str = f"{row['Median TTH (Days)']:.1f} median days" if pd.notna(row['Median TTH (Days)']) else "N/A"
            city_res_list.append(
                f"{city}: {row['Positions']} positions | {row['Filled (Hires)']} filled | Time-to-Hire: {tth_str}"
            )
            
        results['City-Level Metrics'] = city_res_list
    else:
        results['City-Level Metrics'] = "N/A (Missing Workplace column)"

    # 9. Location-Specific Bottlenecks
    if 'Position workplace name' in df.columns and 'Final phase' in df.columns:
        top_locs = df['Position workplace name'].value_counts().head(5).index
        loc_b_res = {}
        
        non_rejection_mask = ~df['Final phase'].astype(str).str.contains('reject', case=False, na=False)
        filtered_df = df[non_rejection_mask]

        if 'Days in current phase' in filtered_df.columns:
            for loc in top_locs:
                loc_df = filtered_df[filtered_df['Position workplace name'] == loc]
                top_stage = (
                    loc_df.groupby('Final phase')['Days in current phase']
                    .median()
                    .sort_values(ascending=False)
                    .head(1)
                )
                if not top_stage.empty:
                    loc_b_res[f"{loc} - {top_stage.index[0]}"] = f"{top_stage.iloc[0]:.1f} median days"
        else:
            loc_b_res = {"N/A": "Days in current phase not available in this dataset"}
        
        if loc_b_res:
            results['Location-Specific Bottlenecks (Top 5 Locations by Volume)'] = loc_b_res
        else:
            results['Location-Specific Bottlenecks (Top 5 Locations by Volume)'] = "N/A"
    else:
        results['Location-Specific Bottlenecks (Top 5 Locations by Volume)'] = "N/A"

    # 10. Active Pipeline Summary
    if status_col and 'Final phase' in df.columns:
        active_mask = ~df[status_col].astype(str).str.strip().str.lower().isin(['rejected', 'withdrawn', 'accepted'])
        df_active = df[active_mask].copy()

        if not df_active.empty:
            stage_mapping = {
                'Applications': 'Applications (Initial)',
                'Rejection after Screening': 'Rejection after Screening',
                'Hiring Manager (Screening)': 'Hiring Manager (Screening)',
                'Screening Round': 'Screening Round',
                'Backlog / On-Hold': 'Backlog / On-Hold',
                'Team Round': 'Team Round',
                'TODO (Rejection)': 'TODO (Rejection)'
            }

            if 'Days in current phase' in df_active.columns:
                summary = df_active.groupby('Final phase').agg(
                    Active_Candidates=('Application ID', 'count' if 'Application ID' in df_active.columns else 'size'),
                    Avg_Days_Stuck=('Days in current phase', 'mean'),
                    Max_Days_Stuck=('Days in current phase', 'max'),
                    Stalled_over_14_Days=('Days in current phase', lambda x: (x > 14).sum())
                ).reset_index()
            else:
                summary = df_active.groupby('Final phase').agg(
                    Active_Candidates=('Application ID', 'count' if 'Application ID' in df_active.columns else 'size')
                ).reset_index()
                summary['Avg_Days_Stuck'] = np.nan
                summary['Max_Days_Stuck'] = np.nan
                summary['Stalled_over_14_Days'] = np.nan

            summary = summary[summary['Final phase'].isin(stage_mapping.keys())].copy()
            summary['Pipeline Stage'] = summary['Final phase'].map(stage_mapping)

            if 'Avg_Days_Stuck' in summary.columns:
                summary = summary.rename(columns={
                    'Active_Candidates': 'Active Candidates',
                    'Avg_Days_Stuck': 'Avg. Days Stuck',
                    'Max_Days_Stuck': 'Max Days Stuck',
                    'Stalled_over_14_Days': 'Stalled > 14 Days'
                })
            else:
                summary = summary.rename(columns={
                    'Active_Candidates': 'Active Candidates'
                })

            if not summary.empty:
                if 'Avg. Days Stuck' in summary.columns:
                    summary = summary[['Pipeline Stage', 'Active Candidates', 'Avg. Days Stuck', 'Max Days Stuck', 'Stalled > 14 Days']]
                    summary = summary.sort_values(by='Active Candidates', ascending=False)
                    summary['Avg. Days Stuck'] = summary['Avg. Days Stuck'].round(1)
                    results['Active Pipeline Summary'] = summary.to_string(index=False).split('\n')
                else:
                    summary = summary[['Pipeline Stage', 'Active Candidates']]
                    summary = summary.sort_values(by='Active Candidates', ascending=False)
                    results['Active Pipeline Summary'] = summary.to_string(index=False).split('\n')
            else:
                results['Active Pipeline Summary'] = ["No active candidates found in mapped stages."]
        else:
            results['Active Pipeline Summary'] = ["No active candidates found overall."]

    # Print formatted results
    for key, value in results.items():
        if isinstance(value, dict):
            print(f"{key}:")
            for sub_key, sub_val in value.items():
                print(f"  - {sub_key}: {sub_val}")
        elif isinstance(value, list):
            print(f"-----------------")
            print(f"{key}:")
            for item in value:
                print(f"  {item}")
        else:
            print(f"{key}: {value}")
    print("\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage error. Please provide a CSV filename.")
        print("Example: python pipeline_kpis.py 2026.csv")
        sys.exit(1)
        
    csv_filename = sys.argv[1]
    analyze_pipeline(csv_filename)