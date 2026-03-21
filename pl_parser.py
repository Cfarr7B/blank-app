"""
P&L Excel Parser for 7BREW Dashboard
Parses 'PTD Side By Side' format Excel files into the DASH JSON structure.
"""
import pandas as pd
import json
import re
import os

# Row indices for key line items (0-indexed from Excel row 1)
ROW_MAP = {
    'net_sales': 21,
    'gross_sales': 15,
    'discounts': 17,
    'comps': 18,
    'employee_discounts': 19,
    'total_comps_promos': 20,
    'cogs': 32,
    'profit_margin': 33,
    'hourly_labor': 40,
    'management': 44,
    'hourly_and_mgmt': 45,
    'benefits_tax': 51,
    'total_labor': 52,
    'gross_margin': 53,
    'controllable': 67,
    # Utilities sub-categories
    'electricity': 69,
    'gas': 70,
    'water_sewer': 71,
    'waste_removal': 72,
    'utilities': 73,          # Total Utilities
    # R&M sub-categories
    'rm_building': 75,
    'rm_equipment': 76,
    'landscaping': 77,
    'pest_control': 78,
    'rm': 79,                 # Total R&M
    'fixed_expense': 99,
    'occupancy': 103,
    'marketing': 112,
    'ebitdar': 113,
    'rent': 114,
    'store_ebitda': 115,
    'ebitda': 128,
    'net_income': 139,
}

# Default stand metadata (region, age bucket, etc.)
_STAND_META = {}

def load_stand_metadata(json_path):
    """Load stand metadata from existing dashboard data."""
    global _STAND_META
    if os.path.exists(json_path):
        with open(json_path, 'r') as f:
            _STAND_META = json.load(f)

def extract_period_from_filename(filename):
    """Extract period info from filename like "P13'24" or "P1'25"."""
    match = re.search(r"P(\d+)'?(\d{2,4})", filename, re.IGNORECASE)
    if match:
        period_num = int(match.group(1))
        year = int(match.group(2))
        if year < 100:
            year += 2000
        return year, period_num
    return None, None

def extract_period_from_sheet(df):
    """Extract period info from the 'As of' date in the sheet."""
    for i in range(min(5, len(df))):
        val = str(df.iloc[i, 0]) if pd.notna(df.iloc[i, 0]) else ''
        if 'As of' in val:
            date_match = re.search(r'(\w+ \d+,? \d{4})', val)
            if date_match:
                try:
                    dt = pd.to_datetime(date_match.group(1))
                    return dt
                except:
                    pass
        if 'As of Date' in val:
            date_val = df.iloc[i, 1]
            if pd.notna(date_val):
                try:
                    dt = pd.to_datetime(date_val)
                    return dt
                except:
                    pass
    return None

def parse_pl_file(filepath, year=None, period_num=None):
    """
    Parse a 7BREW P&L Excel file and return structured data.

    Returns: dict with keys:
        - period_key: e.g., "2024_P13"
        - year, period, label
        - stands: list of stand-level dicts
        - summary: portfolio-level summary dict
    """
    filename = os.path.basename(filepath)

    if year is None or period_num is None:
        y, p = extract_period_from_filename(filename)
        if y: year = y
        if p: period_num = p

    df = pd.read_excel(filepath, sheet_name=0, header=None)

    if year is None:
        dt = extract_period_from_sheet(df)
        if dt:
            year = dt.year
            period_num = period_num or ((dt.month - 1) + 1)

    if year is None:
        year = 2024
    if period_num is None:
        period_num = 1

    period_key = f"{year}_P{period_num}"
    label = f"P{period_num} '{str(year)[-2:]}"

    # Find stand columns — row 7 has stand names
    stand_cols = {}
    all_stands_col = None

    for c in range(1, df.shape[1]):
        val = df.iloc[7, c] if 7 < df.shape[0] else None
        if pd.notna(val):
            name = str(val).strip()
            if name and name != ' ' and 'PTD' not in name:
                if name == 'All Stands':
                    all_stands_col = c
                elif name == 'All Stands & Offices':
                    continue
                elif 'Corp Office' in name:
                    continue
                else:
                    stand_cols[name] = c

    # Parse each stand's data
    stands_data = []
    for stand_name, col in stand_cols.items():
        pct_col = col + 1 if (col + 1) < df.shape[1] else None
        stand = parse_stand_data(df, stand_name, col, pct_col, year, period_num, period_key)
        if stand and stand.get('Net_Sales', 0) > 0:
            stands_data.append(stand)

    summary = None
    if all_stands_col is not None:
        pct_col = all_stands_col + 1 if (all_stands_col + 1) < df.shape[1] else None
        summary = parse_stand_data(df, 'All Stands', all_stands_col, pct_col, year, period_num, period_key)

    return {
        'period_key': period_key,
        'year': year,
        'period': f"P{period_num}",
        'label': label,
        'stands': stands_data,
        'summary': summary,
    }

def safe_float(val):
    """Safely convert a value to float."""
    if pd.isna(val) or val is None:
        return 0.0
    try:
        v = float(val)
        return v if not pd.isna(v) else 0.0
    except (ValueError, TypeError):
        return 0.0

def parse_stand_data(df, stand_name, val_col, pct_col, year, period_num, period_key):
    """Parse data for a single stand from the dataframe."""
    def get_val(row_key):
        row = ROW_MAP.get(row_key)
        if row is None or row >= df.shape[0]:
            return 0.0
        return safe_float(df.iloc[row, val_col])

    def get_pct(row_key):
        row = ROW_MAP.get(row_key)
        if row is None or row >= df.shape[0] or pct_col is None:
            return 0.0
        return safe_float(df.iloc[row, pct_col])

    net_sales = get_val('net_sales')
    if net_sales <= 0:
        return None

    # Look up metadata: try stand_name first, then fall back to numeric Store_ID
    # (stand_meta.json is keyed by Store_ID string like "134"; stand_name is "000134 Lubbock, TX - 1")
    meta = _STAND_META.get(stand_name, {})
    if not meta:
        id_match = re.match(r'0*(\d+)', stand_name)
        if id_match:
            meta = _STAND_META.get(id_match.group(1), {})

    state = meta.get('State', '')
    if not state:
        state_match = re.search(r',\s*(\w{2})\s*-', stand_name)
        state = state_match.group(1) if state_match else ''

    store_id = meta.get('Store_ID', 0)
    if not store_id:
        id_match = re.match(r'(\d+)', stand_name)
        store_id = int(id_match.group(1)) if id_match else 0

    open_date = meta.get('Open_Date', meta.get('Open Date', ''))

    return {
        'Stand': stand_name,
        'Period': f"P{period_num}",
        'Year': year,
        'Period_Key': period_key,
        'Store_ID': store_id,
        'State': state,
        'Region': meta.get('Region', 'Unknown'),
        'Age_Bucket': meta.get('Age_Bucket', 'Unknown'),
        'RM': meta.get('RM', ''),
        'Open Date': open_date,
        'Age (Yrs)': 0,
        'Net_Sales': net_sales,
        'Total_COGS': get_val('cogs'),
        'Total_COGS_pct': get_pct('cogs'),
        'Total_Hourly': get_val('hourly_labor'),
        'Total_Hourly_pct': get_pct('hourly_labor'),
        'Total_Labor': get_val('total_labor'),
        'Total_Labor_pct': get_pct('total_labor'),
        'Total_RM': get_val('rm'),
        'Total_RM_pct': get_pct('rm'),
        'RM_Equipment': get_val('rm_equipment'),
        'RM_Equipment_pct': get_pct('rm_equipment'),
        'RM_Building': get_val('rm_building'),
        'RM_Building_pct': get_pct('rm_building'),
        'Controllable': get_val('controllable'),
        'Controllable_pct': get_pct('controllable'),
        'Total_Utilities': get_val('utilities'),
        'Total_Utilities_pct': get_pct('utilities'),
        'Electricity': get_val('electricity'),
        'Electricity_pct': get_pct('electricity'),
        'Gas': get_val('gas'),
        'Gas_pct': get_pct('gas'),
        'Water_Sewer': get_val('water_sewer'),
        'Water_Sewer_pct': get_pct('water_sewer'),
        'Waste_Removal': get_val('waste_removal'),
        'Waste_Removal_pct': get_pct('waste_removal'),
        'Total_Fixed': get_val('fixed_expense'),
        'Total_Fixed_pct': get_pct('fixed_expense'),
        'Total_Marketing': get_val('marketing'),
        'Total_Marketing_pct': get_pct('marketing'),
        'Unit_EBITDAR': get_val('ebitdar'),
        'Unit_EBITDAR_pct': get_pct('ebitdar'),
        'Total_Rent': get_val('rent'),
        'Total_Rent_pct': get_pct('rent'),
        'Store_EBITDA': get_val('store_ebitda'),
        'Store_EBITDA_pct': get_pct('store_ebitda'),
        'Discounts': get_val('discounts'),
        'Discounts_pct': get_pct('discounts'),
        'Net_Income': get_val('net_income'),
    }

def build_period_summary(stands, year, period_num, period_key, label):
    """Build a period summary from stand-level data."""
    active_stands = [s for s in stands if s['Net_Sales'] > 0]
    n = len(active_stands)
    if n == 0:
        return None

    total_net = sum(s['Net_Sales'] for s in active_stands)
    avg_sales = total_net / n

    def wavg(field):
        vals = [s.get(field, 0) for s in active_stands]
        return sum(v * s['Net_Sales'] for v, s in zip(vals, active_stands)) / total_net if total_net > 0 else 0

    total_ebitda = sum(s['Store_EBITDA'] for s in active_stands)

    return {
        'period_key': period_key,
        'year': year,
        'period': f"P{period_num}",
        'label': label,
        'stands': n,
        'net_sales': round(total_net, 2),
        'avg_sales': round(avg_sales, 2),
        'cogs_pct': round(wavg('Total_COGS_pct'), 4),
        'labor_pct': round(wavg('Total_Labor_pct'), 4),
        'hourly_pct': round(wavg('Total_Hourly_pct'), 4),
        'rm_pct': round(wavg('Total_RM_pct'), 4),
        'rm_equipment_pct': round(wavg('RM_Equipment_pct'), 4),
        'rm_building_pct': round(wavg('RM_Building_pct'), 4),
        'ebitdar_pct': round(wavg('Unit_EBITDAR_pct'), 4),
        'ebitda': round(total_ebitda, 2),
        'ebitda_pct': round(wavg('Store_EBITDA_pct'), 4),
        'rent_pct': round(wavg('Total_Rent_pct'), 4),
        'discount_pct': round(wavg('Discounts_pct'), 4),
        'utilities_pct': round(wavg('Total_Utilities_pct'), 4),
        'electricity_pct': round(wavg('Electricity_pct'), 4),
        'gas_pct': round(wavg('Gas_pct'), 4),
        'water_sewer_pct': round(wavg('Water_Sewer_pct'), 4),
        'waste_removal_pct': round(wavg('Waste_Removal_pct'), 4),
        'controllable_pct': round(wavg('Controllable_pct'), 4),
        'fixed_pct': round(wavg('Total_Fixed_pct'), 4),
        'marketing_pct': round(wavg('Total_Marketing_pct'), 4),
    }

def build_region_summary(stands):
    """Build region-level summaries from stand data."""
    from collections import defaultdict
    regions = defaultdict(list)
    for s in stands:
        if s['Region'] and s['Region'] != 'Unknown' and s['Region'] != '0':
            regions[s['Region']].append(s)

    result = []
    for region, rstands in regions.items():
        n = len(rstands)
        total_net = sum(s['Net_Sales'] for s in rstands)

        def wavg(field):
            vals = [s.get(field, 0) for s in rstands]
            return sum(v * s['Net_Sales'] for v, s in zip(vals, rstands)) / total_net if total_net > 0 else 0

        result.append({
            'region': region,
            'stands': n,
            'net_sales': round(total_net, 2),
            'avg_sales': round(total_net / n, 2),
            'cogs_pct': round(wavg('Total_COGS_pct'), 4),
            'labor_pct': round(wavg('Total_Labor_pct'), 4),
            'hourly_pct': round(wavg('Total_Hourly_pct'), 4),
            'rm_pct': round(wavg('Total_RM_pct'), 4),
            'ebitda_pct': round(wavg('Store_EBITDA_pct'), 4),
            'ebitda_total': round(sum(s['Store_EBITDA'] for s in rstands), 2),
        })
    return result

def merge_into_dash(dash, parsed_periods):
    """Merge parsed period data into existing DASH structure."""
    existing_keys = {ps['period_key'] for ps in dash['period_summaries']}

    for pp in parsed_periods:
        pk = pp['period_key']

        if pk in existing_keys:
            # Update existing period with new detailed data (utility sub-categories)
            stands = pp['stands']
            if not stands:
                continue
            summary = build_period_summary(
                stands, pp['year'], int(pp['period'].replace('P', '')), pk, pp['label']
            )
            if summary:
                # Update existing period summary with new fields
                idx = next((i for i, ps in enumerate(dash['period_summaries']) if ps['period_key'] == pk), None)
                if idx is not None:
                    dash['period_summaries'][idx].update(summary)
            # Update or append stand records
            dash['stand_records'] = [s for s in dash['stand_records'] if s.get('Period_Key') != pk]
            dash['stand_records'].extend(stands)
            dash['region_by_period'][pk] = build_region_summary(stands)
            continue

        stands = pp['stands']
        if not stands:
            continue

        summary = build_period_summary(
            stands, pp['year'], int(pp['period'].replace('P', '')), pk, pp['label']
        )
        if summary:
            dash['period_summaries'].append(summary)

        dash['stand_records'].extend(stands)
        dash['region_by_period'][pk] = build_region_summary(stands)

        if pk not in dash.get('period_order', []):
            dash.setdefault('period_order', []).append(pk)

    def period_sort_key(pk):
        parts = pk.split('_')
        year = int(parts[0])
        period = int(parts[1].replace('P', ''))
        return (year, period)

    dash['period_summaries'].sort(key=lambda x: period_sort_key(x['period_key']))
    if 'period_order' in dash:
        dash['period_order'].sort(key=period_sort_key)

    return dash
