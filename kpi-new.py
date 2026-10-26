import os
import sys
import pandas as pd
import numpy as np
import warnings
warnings.filterwarnings('ignore')

def load_data(file_path):
    """Loads a single combined CSV or Excel file."""
    if not os.path.isfile(file_path):
        print(f"Error: File '{file_path}' not found.")
        sys.exit(1)
        
    ext = os.path.splitext(file_path)[1].lower()
    if ext in ['.xlsx', '.xls', '.xlsm']:
        return pd.read_excel(file_path)
    elif ext == '.csv':
        return pd.read_csv(file_path)
    else:
        raise ValueError("Unsupported format. Please provide a .csv or .xlsx file.")

def analyze_quarter_event_metrics(df, q):
    """Calculates recruiting KPIs for a given calendar quarter using event-based logic."""
    print("=" * 95)
    print(f"  DETAILED RECRUITING REPORT: {q} (Event-Based)")
    print("=" * 95)
    
    # 1. Applications & Positions Active in Quarter
    apps_q = df[df['app_q'] == q]
    total_apps = len(apps_q)
    apps_perm = len(apps_q[~apps_q['is_student']])
    apps_stud = len(apps_q[apps_q['is_student']])
    
    pos_col = 'Position ID' if 'Position ID' in df.columns else 'Position name'
    pos_tot = apps_q[pos_col].nunique() if total_apps > 0 else 0
    pos_p = apps_q[~apps_q['is_student']][pos_col].nunique() if total_apps > 0 else 0
    pos_s = apps_q[apps_q['is_student']][pos_col].nunique() if total_apps > 0 else 0
    
    print(f"[*] Applications Received: {total_apps:,} (Perm: {apps_perm:,} | Student/Intern: {apps_stud:,})")
    print(f"[*] Active Opened Positions: {pos_tot} (Perm: {pos_p} | Student/Intern: {pos_s})")
    
    # 2. Hires Made (Accepted Date in Quarter)
    hires_q = df[df['hire_q'] == q]
    total_hires = len(hires_q)
    hires_perm = len(hires_q[~hires_q['is_student']])
    hires_stud = len(hires_q[hires_q['is_student']])
    
    print(f"[*] Total Hires Made: {total_hires} (Perm: {hires_perm} | Student/Intern: {hires_stud})")
    
    # 3. Median Time-to-Hire (for hires finalized in Quarter)
    if total_hires > 0:
        tth_all = (hires_q['hire_date'] - hires_q['app_date']).dt.days.median()
        tth_perm = (hires_q[~hires_q['is_student']]['hire_date'] - hires_q[~hires_q['is_student']]['app_date']).dt.days.median()
        tth_stud = (hires_q[hires_q['is_student']]['hire_date'] - hires_q[hires_q['is_student']]['app_date']).dt.days.median()
        print(f"[*] Median Time-to-Hire: {tth_all:.0f} days (Perm: {tth_perm:.0f}d | Student/Intern: {tth_stud:.0f}d)")
    else:
        print("[*] Median Time-to-Hire: N/A (0 hires)")
        
    # 4. Offer Acceptance Rate (OAR) - Split by Perm & Student
    offers_q = df[df['offer_q'] == q]
    off_tot = len(offers_q)
    acc_tot = len(offers_q[offers_q['is_hired']])
    oar_tot = (acc_tot / off_tot * 100) if off_tot > 0 else 0
    
    off_p = len(offers_q[~offers_q['is_student']])
    acc_p = len(offers_q[(~offers_q['is_student']) & offers_q['is_hired']])
    oar_p = (acc_p / off_p * 100) if off_p > 0 else 0
    
    off_s = len(offers_q[offers_q['is_student']])
    acc_s = len(offers_q[offers_q['is_student'] & offers_q['is_hired']])
    oar_s = (acc_s / off_s * 100) if off_s > 0 else 0
    
    if off_tot > 0:
        print(f"[*] Offer Acceptance Rate (OAR): {oar_tot:.1f}% ({acc_tot}/{off_tot})")
        print(f"    - Permanent (FTE): {oar_p:.1f}% ({acc_p}/{off_p})")
        print(f"    - Student/Intern : {oar_s:.1f}% ({acc_s}/{off_s})")
    else:
        print("[*] Offer Acceptance Rate (OAR): N/A (0 offers extended)")
        
    # 5. Screening Pass-Through Rate (Screenings held in Quarter)
    if 'Screening Round' in df.columns:
        screen_q = df[df['screen_q'] == q]
        subsequent = [col for col in ['Team Round', 'Management Round', 'Task round', 'Offer', 'Accepted'] if col in df.columns]
        if len(screen_q) > 0 and subsequent:
            passed_mask = screen_q[subsequent[0]].notna()
            for col in subsequent[1:]:
                passed_mask = passed_mask | screen_q[col].notna()
            passed = len(screen_q[passed_mask])
            pass_rate = (passed / len(screen_q)) * 100
            print(f"[*] Screening Pass-Through Rate: {pass_rate:.1f}% ({passed} passed / {len(screen_q)} screened)")
        else:
            print("[*] Screening Pass-Through Rate: N/A")

    # 6. Candidate Withdrawals (Drop-Offs in Quarter)
    withdrawn_q = df[df['withdrawn_q'] == q]
    print(f"[*] Candidate Withdrawals: {len(withdrawn_q)} candidates voluntarily withdrew")

    # 7. Hires by Workplace / City
    if total_hires > 0 and 'Position workplace name' in hires_q.columns:
        print("\n[-] Hires by Workplace:")
        city_counts = hires_q['Position workplace name'].value_counts()
        for city, cnt in city_counts.items():
            city_hires_df = hires_q[hires_q['Position workplace name'] == city]
            tth_city = (city_hires_df['hire_date'] - city_hires_df['app_date']).dt.days.median()
            print(f"    - {city}: {cnt} hires (Median TTH: {tth_city:.0f}d)")

    # 8. Top Channels for Hires Made in Quarter
    if total_hires > 0 and 'Application channel' in hires_q.columns:
        print("\n[-] Top Channels for Hires Made:")
        chan_counts = hires_q['Application channel'].value_counts()
        for chan, cnt in chan_counts.head(5).items():
            print(f"    - {chan}: {cnt} hires ({cnt/total_hires*100:.1f}%)")
    print()

def analyze_all_quarters(file_path):
    print(f"Loading data from: {file_path}...")
    df = load_data(file_path)
    df.columns = df.columns.str.strip()
    
    # 1. Standardize dates
    df['app_date'] = pd.to_datetime(df['Application date'], errors='coerce')
    df['final_status_date'] = pd.to_datetime(df['Final status date'], errors='coerce')
    df['accepted_date'] = pd.to_datetime(df['Accepted'], errors='coerce') if 'Accepted' in df.columns else pd.NaT
    df['offer_date'] = pd.to_datetime(df['Offer'], errors='coerce') if 'Offer' in df.columns else pd.NaT
    df['withdrawn_date'] = pd.to_datetime(df['Withdrawn'], errors='coerce') if 'Withdrawn' in df.columns else pd.NaT
    df['screen_date'] = pd.to_datetime(df['Screening Round'], errors='coerce') if 'Screening Round' in df.columns else pd.NaT

    # 2. Hires & Offers
    status_col = next((c for c in df.columns if c in ['Final status', 'Status'] or 'status' in c.lower()), None)
    is_accepted_status = df[status_col].astype(str).str.strip().str.lower().isin(['accepted', 'hired']) if status_col else False
    is_accepted_col = df['accepted_date'].notna()
    
    df['is_hired'] = is_accepted_status | is_accepted_col
    df['hire_date'] = df['accepted_date'].fillna(df.loc[df['is_hired'], 'final_status_date'])
    
    # Effective offer date
    df['effective_offer_date'] = df['offer_date'].fillna(df['hire_date'])
    
    # 3. Student / Intern classification
    df['is_student'] = df['Position name'].str.contains('Intern|Student', case=False, na=False)

    # 4. Quarters derived from event dates
    df['app_q'] = df['app_date'].dt.to_period('Q')
    df['hire_q'] = df['hire_date'].dt.to_period('Q')
    df['offer_q'] = df['effective_offer_date'].dt.to_period('Q')
    df['withdrawn_q'] = df['withdrawn_date'].dt.to_period('Q')
    df['screen_q'] = df['screen_date'].dt.to_period('Q')

    # Available event quarters
    quarters = sorted(list(set(df['hire_q'].dropna().unique()) | set(df['app_q'].dropna().unique())))
    quarters = [q for q in quarters if str(q).startswith('2026') and str(q) <= '2026Q3']
    
    print("\n" + "#" * 110)
    print("  EXECUTIVE SUMMARY TABLE (EVENT REPORT)")
    print("#" * 110)
    
    summary_rows = []
    pos_col = 'Position ID' if 'Position ID' in df.columns else 'Position name'
    
    for q in quarters:
        apps_q = df[df['app_q'] == q]
        hires_q = df[df['hire_q'] == q]
        offers_q = df[df['offer_q'] == q]
        
        apps_tot = len(apps_q)
        apps_p = len(apps_q[~apps_q['is_student']])
        apps_s = len(apps_q[apps_q['is_student']])
        
        pos_tot = apps_q[pos_col].nunique() if apps_tot > 0 else 0
        pos_p = apps_q[~apps_q['is_student']][pos_col].nunique() if apps_tot > 0 else 0
        pos_s = apps_q[apps_q['is_student']][pos_col].nunique() if apps_tot > 0 else 0
        
        h_tot = len(hires_q)
        h_p = len(hires_q[~hires_q['is_student']])
        h_s = len(hires_q[hires_q['is_student']])
        
        tth_p = (hires_q[~hires_q['is_student']]['hire_date'] - hires_q[~hires_q['is_student']]['app_date']).dt.days.median()
        tth_s = (hires_q[hires_q['is_student']]['hire_date'] - hires_q[hires_q['is_student']]['app_date']).dt.days.median()
        
        # OAR calculations
        off_tot = len(offers_q)
        acc_tot = len(offers_q[offers_q['is_hired']])
        oar_tot = (acc_tot / off_tot * 100) if off_tot > 0 else 0
        
        off_p = len(offers_q[~offers_q['is_student']])
        acc_p = len(offers_q[(~offers_q['is_student']) & offers_q['is_hired']])
        oar_p = (acc_p / off_p * 100) if off_p > 0 else 0
        
        off_s = len(offers_q[offers_q['is_student']])
        acc_s = len(offers_q[offers_q['is_student'] & offers_q['is_hired']])
        oar_s = (acc_s / off_s * 100) if off_s > 0 else 0
        
        summary_rows.append({
            'Quarter': str(q),
            'Applications': f"{apps_tot:,} (P:{apps_p:,} | S:{apps_s:,})",
            'Positions': f"{pos_tot} (P:{pos_p} | S:{pos_s})",
            'Hires Made': f"{h_tot} (P:{h_p} | S:{h_s})",
            'Median TTH': f"P:{tth_p:.0f}d | S:{tth_s:.0f}d",
            'Total OAR': f"{oar_tot:.1f}% ({acc_tot}/{off_tot})",
            'OAR (Perm vs Stud)': f"P:{oar_p:.1f}% ({acc_p}/{off_p}) | S:{oar_s:.1f}% ({acc_s}/{off_s})"
        })
        
    print(pd.DataFrame(summary_rows).to_string(index=False))
    print("#" * 110 + "\n")
    
    for q in quarters:
        analyze_quarter_event_metrics(df, q)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python kpi-new.py <combined_file.xlsx or .csv>")
        sys.exit(1)
    analyze_all_quarters(sys.argv[1])