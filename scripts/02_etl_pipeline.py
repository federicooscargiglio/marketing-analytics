"""
ETL Pipeline: Marketing Campaign Data
=======================================
Cleans raw data, computes KPIs, and produces analysis-ready tables
optimized for Power BI consumption.

Author: Federico Giglio
Project: Marketing Campaign Analytics
"""

import pandas as pd
import numpy as np
import os
import warnings
warnings.filterwarnings('ignore')

# --- Paths ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW_PATH = os.path.join(BASE_DIR, 'data', 'raw')
PROCESSED_PATH = os.path.join(BASE_DIR, 'data', 'processed')
os.makedirs(PROCESSED_PATH, exist_ok=True)


def load_raw_data():
    """Load raw CSV files."""
    print("📥 Loading raw data...")
    campaigns = pd.read_csv(os.path.join(RAW_PATH, 'campaigns.csv'))
    daily = pd.read_csv(os.path.join(RAW_PATH, 'daily_performance.csv'))
    leads = pd.read_csv(os.path.join(RAW_PATH, 'leads.csv'))
    
    print(f"   Campaigns: {campaigns.shape}")
    print(f"   Daily Performance: {daily.shape}")
    print(f"   Leads: {leads.shape}")
    return campaigns, daily, leads


def clean_campaigns(df):
    """Clean and validate campaign dimension."""
    print("\n🧹 Cleaning campaigns...")
    
    df['start_date'] = pd.to_datetime(df['start_date'])
    df['end_date'] = pd.to_datetime(df['end_date'])
    df['duration_days'] = (df['end_date'] - df['start_date']).dt.days
    df['daily_budget'] = (df['total_budget'] / df['duration_days']).round(2)
    
    # Quarter and year from start
    df['start_quarter'] = df['start_date'].dt.to_period('Q').astype(str)
    df['start_year'] = df['start_date'].dt.year
    
    # Budget tier
    df['budget_tier'] = pd.cut(
        df['total_budget'],
        bins=[0, 1000, 5000, 15000, float('inf')],
        labels=['Low (<1K)', 'Medium (1K-5K)', 'High (5K-15K)', 'Premium (>15K)']
    )
    
    # Validate
    assert df['campaign_id'].is_unique, "Duplicate campaign IDs found!"
    assert (df['duration_days'] > 0).all(), "Invalid campaign durations!"
    
    nulls = df.isnull().sum()
    if nulls.any():
        print(f"   ⚠️  Nulls found:\n{nulls[nulls > 0]}")
    else:
        print("   ✅ No nulls detected")
    
    print(f"   ✅ Added: duration_days, daily_budget, start_quarter, budget_tier")
    return df


def clean_daily_performance(df):
    """Clean and enrich daily performance fact table."""
    print("\n🧹 Cleaning daily performance...")
    
    df['date'] = pd.to_datetime(df['date'])
    
    # Remove negative values
    numeric_cols = ['impressions', 'clicks', 'conversions', 'spend', 'revenue',
                    'likes', 'shares']
    for col in numeric_cols:
        negatives = (df[col] < 0).sum()
        if negatives > 0:
            print(f"   ⚠️  Fixed {negatives} negative values in {col}")
            df[col] = df[col].clip(lower=0)
    
    # Computed KPIs
    df['ctr'] = np.where(df['impressions'] > 0,
                         (df['clicks'] / df['impressions']).round(6), 0)
    df['cpc'] = np.where(df['clicks'] > 0,
                         (df['spend'] / df['clicks']).round(4), 0)
    df['cpa'] = np.where(df['conversions'] > 0,
                         (df['spend'] / df['conversions']).round(4), 0)
    df['roas'] = np.where(df['spend'] > 0,
                          (df['revenue'] / df['spend']).round(4), 0)
    df['conversion_rate'] = np.where(df['clicks'] > 0,
                                     (df['conversions'] / df['clicks']).round(6), 0)
    df['cost_per_impression'] = np.where(df['impressions'] > 0,
                                         (df['spend'] / df['impressions'] * 1000).round(4), 0)
    
    # Time dimensions
    df['year'] = df['date'].dt.year
    df['month'] = df['date'].dt.month
    df['month_name'] = df['date'].dt.strftime('%B')
    df['quarter'] = df['date'].dt.to_period('Q').astype(str)
    df['week_number'] = df['date'].dt.isocalendar().week.astype(int)
    df['day_of_week'] = df['date'].dt.day_name()
    df['is_weekend'] = df['date'].dt.weekday >= 5
    
    print(f"   ✅ Added KPIs: CTR, CPC, CPA, ROAS, conversion_rate, CPM")
    print(f"   ✅ Added time dimensions: year, month, quarter, week, day_of_week")
    return df


def clean_leads(df):
    """Clean leads data."""
    print("\n🧹 Cleaning leads...")
    
    df['date'] = pd.to_datetime(df['date'])
    df['deal_value'] = df['deal_value'].fillna(0)
    df['days_to_convert'] = df['days_to_convert'].fillna(-1).astype(int)
    
    # Lead scoring (simple model)
    status_score = {
        'New': 10, 'Contacted': 25, 'Qualified': 50,
        'Proposal': 75, 'Won': 100, 'Lost': 0
    }
    df['lead_score'] = df['lead_status'].map(status_score)
    
    # Is won flag
    df['is_won'] = (df['lead_status'] == 'Won').astype(int)
    
    # Revenue bucket
    df['deal_size'] = pd.cut(
        df['deal_value'],
        bins=[-1, 0, 2000, 8000, float('inf')],
        labels=['No Deal', 'Small (<2K)', 'Medium (2K-8K)', 'Large (>8K)']
    )
    
    print(f"   ✅ Added: lead_score, is_won, deal_size")
    print(f"   Lead status distribution:\n{df['lead_status'].value_counts().to_string()}")
    return df


def create_aggregated_tables(daily_df, campaigns_df, leads_df):
    """Create pre-aggregated tables for Power BI performance."""
    print("\n📊 Creating aggregated tables...")
    
    # --- Monthly Channel Summary ---
    monthly_channel = daily_df.merge(
        campaigns_df[['campaign_id', 'channel', 'region', 'campaign_type']],
        on='campaign_id', how='left'
    )
    
    monthly_summary = monthly_channel.groupby(
        ['year', 'quarter', 'month', 'month_name', 'channel', 'region']
    ).agg(
        total_impressions=('impressions', 'sum'),
        total_clicks=('clicks', 'sum'),
        total_conversions=('conversions', 'sum'),
        total_spend=('spend', 'sum'),
        total_revenue=('revenue', 'sum'),
        total_likes=('likes', 'sum'),
        total_shares=('shares', 'sum'),
        avg_bounce_rate=('bounce_rate', 'mean'),
        avg_session_duration=('avg_session_duration_sec', 'mean'),
        active_days=('date', 'nunique'),
    ).reset_index()
    
    # Recalculate KPIs at aggregate level
    monthly_summary['ctr'] = (monthly_summary['total_clicks'] / 
                               monthly_summary['total_impressions'].replace(0, np.nan)).round(6)
    monthly_summary['cpc'] = (monthly_summary['total_spend'] / 
                               monthly_summary['total_clicks'].replace(0, np.nan)).round(4)
    monthly_summary['cpa'] = (monthly_summary['total_spend'] / 
                               monthly_summary['total_conversions'].replace(0, np.nan)).round(4)
    monthly_summary['roas'] = (monthly_summary['total_revenue'] / 
                                monthly_summary['total_spend'].replace(0, np.nan)).round(4)
    monthly_summary = monthly_summary.fillna(0)
    
    print(f"   ✅ Monthly Channel Summary: {monthly_summary.shape}")
    
    # --- Campaign Performance Summary ---
    camp_perf = daily_df.groupby('campaign_id').agg(
        total_impressions=('impressions', 'sum'),
        total_clicks=('clicks', 'sum'),
        total_conversions=('conversions', 'sum'),
        total_spend=('spend', 'sum'),
        total_revenue=('revenue', 'sum'),
        avg_ctr=('ctr', 'mean'),
        avg_cpc=('cpc', 'mean'),
        avg_bounce_rate=('bounce_rate', 'mean'),
        days_active=('date', 'nunique'),
    ).reset_index()
    
    camp_perf = camp_perf.merge(campaigns_df, on='campaign_id', how='left')
    camp_perf['roas'] = (camp_perf['total_revenue'] / 
                          camp_perf['total_spend'].replace(0, np.nan)).fillna(0).round(4)
    camp_perf['budget_utilization'] = (camp_perf['total_spend'] / 
                                        camp_perf['total_budget'].replace(0, np.nan)).fillna(0).round(4)
    
    print(f"   ✅ Campaign Performance Summary: {camp_perf.shape}")
    
    # --- Lead Funnel by Channel ---
    lead_funnel = leads_df.groupby(['channel', 'region', 'lead_status']).agg(
        lead_count=('lead_id', 'count'),
        total_deal_value=('deal_value', 'sum'),
        avg_deal_value=('deal_value', 'mean'),
        avg_lead_score=('lead_score', 'mean'),
        won_count=('is_won', 'sum'),
    ).reset_index()
    
    print(f"   ✅ Lead Funnel Summary: {lead_funnel.shape}")
    
    return monthly_summary, camp_perf, lead_funnel


def create_date_dimension(daily_df):
    """Create a date dimension table for Power BI star schema."""
    print("\n📅 Creating date dimension...")
    
    date_range = pd.date_range(
        start=daily_df['date'].min(),
        end=daily_df['date'].max(),
        freq='D'
    )
    
    date_dim = pd.DataFrame({'date': date_range})
    date_dim['year'] = date_dim['date'].dt.year
    date_dim['quarter'] = date_dim['date'].dt.quarter
    date_dim['quarter_label'] = 'Q' + date_dim['quarter'].astype(str) + ' ' + date_dim['year'].astype(str)
    date_dim['month'] = date_dim['date'].dt.month
    date_dim['month_name'] = date_dim['date'].dt.strftime('%B')
    date_dim['month_short'] = date_dim['date'].dt.strftime('%b')
    date_dim['week_number'] = date_dim['date'].dt.isocalendar().week.astype(int)
    date_dim['day_of_week'] = date_dim['date'].dt.day_name()
    date_dim['day_of_week_num'] = date_dim['date'].dt.weekday
    date_dim['is_weekend'] = date_dim['day_of_week_num'] >= 5
    date_dim['year_month'] = date_dim['date'].dt.strftime('%Y-%m')
    
    print(f"   ✅ Date dimension: {date_dim.shape} ({date_dim['date'].min().date()} to {date_dim['date'].max().date()})")
    return date_dim


def save_processed(campaigns, daily, leads, monthly, camp_perf, lead_funnel, date_dim):
    """Save all processed tables."""
    print("\n💾 Saving processed data...")
    
    tables = {
        'dim_campaigns.csv': campaigns,
        'dim_dates.csv': date_dim,
        'fact_daily_performance.csv': daily,
        'fact_leads.csv': leads,
        'agg_monthly_channel.csv': monthly,
        'agg_campaign_performance.csv': camp_perf,
        'agg_lead_funnel.csv': lead_funnel,
    }
    
    for filename, df in tables.items():
        filepath = os.path.join(PROCESSED_PATH, filename)
        df.to_csv(filepath, index=False)
        print(f"   ✅ {filename}: {df.shape[0]:,} rows x {df.shape[1]} cols")
    
    # Also save an Excel workbook with all sheets for Power BI
    excel_path = os.path.join(PROCESSED_PATH, 'marketing_analytics_data.xlsx')
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        for filename, df in tables.items():
            sheet_name = filename.replace('.csv', '')[:31]  # Excel 31 char limit
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    
    print(f"\n   📦 Excel workbook saved: marketing_analytics_data.xlsx")


# --- Main ---
if __name__ == '__main__':
    print("=" * 60)
    print("  ETL PIPELINE - Marketing Campaign Analytics")
    print("=" * 60)
    
    # Extract
    campaigns, daily, leads = load_raw_data()
    
    # Transform
    campaigns = clean_campaigns(campaigns)
    daily = clean_daily_performance(daily)
    leads = clean_leads(leads)
    
    # Aggregate
    monthly, camp_perf, lead_funnel = create_aggregated_tables(daily, campaigns, leads)
    date_dim = create_date_dimension(daily)
    
    # Load
    save_processed(campaigns, daily, leads, monthly, camp_perf, lead_funnel, date_dim)
    
    # Summary
    print("\n" + "=" * 60)
    print("  ETL COMPLETE - Summary")
    print("=" * 60)
    total_spend = daily['spend'].sum()
    total_revenue = daily['revenue'].sum()
    total_leads = len(leads)
    won_leads = leads['is_won'].sum()
    print(f"  Total Spend:      ${total_spend:,.2f}")
    print(f"  Total Revenue:    ${total_revenue:,.2f}")
    print(f"  Overall ROAS:     {total_revenue/total_spend:.2f}x")
    print(f"  Total Leads:      {total_leads:,}")
    print(f"  Won Leads:        {won_leads:,} ({won_leads/total_leads*100:.1f}%)")
    print(f"  Total Deal Value: ${leads['deal_value'].sum():,.2f}")
    print("=" * 60)
