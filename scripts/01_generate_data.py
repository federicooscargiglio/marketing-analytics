"""
Marketing Campaign Data Generator
==================================
Generates realistic marketing campaign data for a mid-size SaaS company
across multiple channels, regions, and time periods.

Author: Federico Giglio
Project: Marketing Campaign Analytics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import os

np.random.seed(42)
random.seed(42)

# --- Configuration ---
START_DATE = datetime(2023, 1, 1)
END_DATE = datetime(2025, 3, 31)
NUM_CAMPAIGNS = 85
NUM_DAILY_RECORDS = None  # calculated per campaign

# --- Dimension Tables ---

channels = {
    'Google Ads': {'avg_cpc': 2.8, 'avg_ctr': 0.035, 'avg_conv_rate': 0.038},
    'Meta Ads': {'avg_cpc': 1.5, 'avg_ctr': 0.012, 'avg_conv_rate': 0.028},
    'LinkedIn Ads': {'avg_cpc': 6.5, 'avg_ctr': 0.008, 'avg_conv_rate': 0.052},
    'Email Marketing': {'avg_cpc': 0.15, 'avg_ctr': 0.22, 'avg_conv_rate': 0.045},
    'TikTok Ads': {'avg_cpc': 0.9, 'avg_ctr': 0.018, 'avg_conv_rate': 0.015},
    'Organic Social': {'avg_cpc': 0.0, 'avg_ctr': 0.005, 'avg_conv_rate': 0.012},
    'Content/SEO': {'avg_cpc': 0.0, 'avg_ctr': 0.028, 'avg_conv_rate': 0.032},
}

regions = ['LATAM', 'North America', 'Europe', 'APAC']
region_weights = [0.30, 0.35, 0.25, 0.10]

campaign_types = ['Brand Awareness', 'Lead Generation', 'Retargeting', 
                  'Product Launch', 'Seasonal Promo', 'Webinar/Event']

audiences = ['Enterprise Decision Makers', 'SMB Owners', 'Marketing Managers',
             'Developers', 'Startup Founders', 'General B2B']

objectives = ['Impressions', 'Clicks', 'Conversions', 'Sign-ups', 'Demo Requests']

# --- Generate Campaign Dimension ---
def generate_campaigns(n):
    campaigns = []
    for i in range(1, n + 1):
        channel = random.choice(list(channels.keys()))
        region = random.choices(regions, weights=region_weights, k=1)[0]
        camp_type = random.choice(campaign_types)
        audience = random.choice(audiences)
        objective = random.choice(objectives)
        
        # Campaign duration: 14 to 120 days
        duration = random.randint(14, 120)
        latest_start = END_DATE - timedelta(days=duration)
        start = START_DATE + timedelta(
            days=random.randint(0, (latest_start - START_DATE).days)
        )
        end = start + timedelta(days=duration)
        
        # Budget: varies by channel and type
        base_budget = random.uniform(500, 25000)
        if channel == 'LinkedIn Ads':
            base_budget *= 1.8
        elif channel in ('Organic Social', 'Content/SEO'):
            base_budget *= 0.3
        
        campaigns.append({
            'campaign_id': f'CMP-{i:04d}',
            'campaign_name': f'{camp_type} - {channel} - {region} - Q{((start.month-1)//3)+1}/{start.year}',
            'channel': channel,
            'region': region,
            'campaign_type': camp_type,
            'target_audience': audience,
            'objective': objective,
            'start_date': start.strftime('%Y-%m-%d'),
            'end_date': end.strftime('%Y-%m-%d'),
            'total_budget': round(base_budget, 2),
            'status': 'Completed' if end < datetime(2025, 3, 1) else 'Active'
        })
    
    return pd.DataFrame(campaigns)


# --- Generate Daily Performance (Fact Table) ---
def generate_daily_performance(campaigns_df):
    records = []
    
    for _, camp in campaigns_df.iterrows():
        ch = channels[camp['channel']]
        start = datetime.strptime(camp['start_date'], '%Y-%m-%d')
        end = datetime.strptime(camp['end_date'], '%Y-%m-%d')
        days = (end - start).days
        daily_budget = camp['total_budget'] / days
        
        for day_offset in range(days):
            date = start + timedelta(days=day_offset)
            dow = date.weekday()
            
            # Seasonality: higher in Q4, lower in Q1
            month_factor = 1.0 + 0.15 * np.sin((date.month - 1) * np.pi / 6)
            
            # Day of week effect (weekdays better for B2B)
            dow_factor = 1.1 if dow < 5 else 0.7
            
            # Random noise
            noise = np.random.normal(1.0, 0.2)
            noise = max(0.3, min(1.8, noise))
            
            # Spend
            spend = daily_budget * dow_factor * noise
            spend = max(0, round(spend, 2))
            
            # Impressions
            if camp['channel'] in ('Organic Social', 'Content/SEO'):
                impressions = int(np.random.poisson(800) * month_factor * dow_factor)
                spend = round(random.uniform(0, 15), 2)  # minimal cost
            else:
                impressions = int(spend / max(ch['avg_cpc'], 0.01) * 
                                random.uniform(30, 80) * month_factor)
            
            impressions = max(10, impressions)
            
            # Clicks
            ctr = ch['avg_ctr'] * noise * dow_factor
            clicks = int(impressions * ctr)
            clicks = max(0, clicks)
            
            # Conversions
            conv_rate = ch['avg_conv_rate'] * noise * month_factor
            conversions = int(clicks * conv_rate)
            conversions = max(0, conversions)
            
            # Revenue per conversion (varies by region and audience)
            rev_base = {'LATAM': 45, 'North America': 120, 'Europe': 95, 'APAC': 70}
            revenue_per_conv = rev_base.get(camp['region'], 80) * random.uniform(0.5, 2.0)
            revenue = round(conversions * revenue_per_conv, 2)
            
            # Engagement metrics
            likes = int(clicks * random.uniform(0.1, 0.4)) if camp['channel'] != 'Email Marketing' else 0
            shares = int(likes * random.uniform(0.05, 0.2))
            
            # Bounce rate
            bounce_rate = round(random.uniform(0.25, 0.75), 4)
            
            # Avg session duration (seconds)
            avg_session = round(random.uniform(15, 300), 1)
            
            records.append({
                'date': date.strftime('%Y-%m-%d'),
                'campaign_id': camp['campaign_id'],
                'impressions': impressions,
                'clicks': clicks,
                'conversions': conversions,
                'spend': spend,
                'revenue': revenue,
                'likes': likes,
                'shares': shares,
                'bounce_rate': bounce_rate,
                'avg_session_duration_sec': avg_session,
            })
    
    return pd.DataFrame(records)


# --- Generate Leads Table ---
def generate_leads(daily_df, campaigns_df):
    leads = []
    lead_id = 1
    
    lead_sources = ['Organic', 'Paid', 'Referral', 'Direct']
    lead_statuses = ['New', 'Contacted', 'Qualified', 'Proposal', 'Won', 'Lost']
    
    for _, row in daily_df.iterrows():
        n_leads = row['conversions']
        if n_leads == 0:
            continue
            
        camp = campaigns_df[campaigns_df['campaign_id'] == row['campaign_id']].iloc[0]
        
        for _ in range(min(n_leads, 5)):  # cap per day for realism
            status_weights = {
                'Lead Generation': [0.15, 0.25, 0.25, 0.15, 0.12, 0.08],
                'Retargeting': [0.10, 0.15, 0.20, 0.25, 0.20, 0.10],
                'Product Launch': [0.20, 0.25, 0.20, 0.15, 0.10, 0.10],
            }
            weights = status_weights.get(camp['campaign_type'], [0.20, 0.20, 0.20, 0.15, 0.15, 0.10])
            
            status = random.choices(lead_statuses, weights=weights, k=1)[0]
            
            deal_value = 0
            if status in ('Proposal', 'Won'):
                base_val = {'Enterprise Decision Makers': 15000, 'SMB Owners': 3000,
                           'Marketing Managers': 5000, 'Developers': 2000,
                           'Startup Founders': 4000, 'General B2B': 3500}
                deal_value = round(base_val.get(camp['target_audience'], 3000) 
                                   * random.uniform(0.5, 2.5), 2)
            
            leads.append({
                'lead_id': f'LEAD-{lead_id:06d}',
                'date': row['date'],
                'campaign_id': row['campaign_id'],
                'channel': camp['channel'],
                'region': camp['region'],
                'lead_source': random.choices(lead_sources, 
                    weights=[0.2, 0.5, 0.15, 0.15], k=1)[0],
                'lead_status': status,
                'deal_value': deal_value,
                'days_to_convert': random.randint(1, 90) if status == 'Won' else None,
            })
            lead_id += 1
    
    return pd.DataFrame(leads)


# --- Main Execution ---
if __name__ == '__main__':
    print("Generating campaigns...")
    campaigns_df = generate_campaigns(NUM_CAMPAIGNS)
    
    print("Generating daily performance data...")
    daily_df = generate_daily_performance(campaigns_df)
    
    print("Generating leads data...")
    leads_df = generate_leads(daily_df, campaigns_df)
    
    # Save raw data
    raw_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'raw')
    os.makedirs(raw_path, exist_ok=True)
    
    campaigns_df.to_csv(os.path.join(raw_path, 'campaigns.csv'), index=False)
    daily_df.to_csv(os.path.join(raw_path, 'daily_performance.csv'), index=False)
    leads_df.to_csv(os.path.join(raw_path, 'leads.csv'), index=False)
    
    print(f"\n✅ Data generated successfully!")
    print(f"   Campaigns: {len(campaigns_df):,} records")
    print(f"   Daily Performance: {len(daily_df):,} records")
    print(f"   Leads: {len(leads_df):,} records")
    print(f"   Date range: {daily_df['date'].min()} to {daily_df['date'].max()}")
    print(f"\n   Files saved to: {os.path.abspath(raw_path)}")
