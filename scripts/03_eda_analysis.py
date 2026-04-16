"""
Exploratory Data Analysis: Marketing Campaign Performance
==========================================================
Key business questions analyzed:
1. Which channels deliver the best ROAS?
2. How does performance vary by region?
3. What's the lead conversion funnel efficiency?
4. Seasonal trends and day-of-week patterns
5. Budget allocation vs. performance

Author: Federico Giglio
Project: Marketing Campaign Analytics
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# --- Setup ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROCESSED = os.path.join(BASE_DIR, 'data', 'processed')
OUTPUT = os.path.join(BASE_DIR, 'docs', 'figures')
os.makedirs(OUTPUT, exist_ok=True)

plt.style.use('seaborn-v0_8-whitegrid')
COLORS = ['#2563EB', '#10B981', '#F59E0B', '#EF4444', '#8B5CF6', '#EC4899', '#06B6D4']
sns.set_palette(COLORS)

# --- Load Data ---
daily = pd.read_csv(os.path.join(PROCESSED, 'fact_daily_performance.csv'), parse_dates=['date'])
campaigns = pd.read_csv(os.path.join(PROCESSED, 'dim_campaigns.csv'), parse_dates=['start_date', 'end_date'])
leads = pd.read_csv(os.path.join(PROCESSED, 'fact_leads.csv'), parse_dates=['date'])
monthly = pd.read_csv(os.path.join(PROCESSED, 'agg_monthly_channel.csv'))
camp_perf = pd.read_csv(os.path.join(PROCESSED, 'agg_campaign_performance.csv'))

# Merge channel info into daily
daily_full = daily.merge(
    campaigns[['campaign_id', 'channel', 'region', 'campaign_type', 'target_audience']],
    on='campaign_id', how='left'
)


def save_fig(fig, name):
    fig.savefig(os.path.join(OUTPUT, f'{name}.png'), dpi=150, bbox_inches='tight',
                facecolor='white', edgecolor='none')
    plt.close(fig)
    print(f"   ✅ Saved: {name}.png")


# ============================================================
# 1. CHANNEL PERFORMANCE OVERVIEW
# ============================================================
print("\n📊 1. Channel Performance Overview")

channel_summary = daily_full.groupby('channel').agg(
    total_spend=('spend', 'sum'),
    total_revenue=('revenue', 'sum'),
    total_clicks=('clicks', 'sum'),
    total_conversions=('conversions', 'sum'),
    total_impressions=('impressions', 'sum'),
).reset_index()

channel_summary['roas'] = channel_summary['total_revenue'] / channel_summary['total_spend'].replace(0, 1)
channel_summary['cpa'] = channel_summary['total_spend'] / channel_summary['total_conversions'].replace(0, 1)
channel_summary['ctr'] = channel_summary['total_clicks'] / channel_summary['total_impressions'].replace(0, 1) * 100
channel_summary = channel_summary.sort_values('roas', ascending=True)

fig, axes = plt.subplots(1, 3, figsize=(18, 6))

# ROAS by Channel
axes[0].barh(channel_summary['channel'], channel_summary['roas'], color=COLORS[:len(channel_summary)])
axes[0].set_xlabel('ROAS (Revenue / Spend)')
axes[0].set_title('ROAS by Channel', fontsize=14, fontweight='bold')
for i, v in enumerate(channel_summary['roas']):
    axes[0].text(v + 0.5, i, f'{v:.1f}x', va='center', fontsize=10)

# CPA by Channel
cpa_sorted = channel_summary.sort_values('cpa', ascending=True)
axes[1].barh(cpa_sorted['channel'], cpa_sorted['cpa'], color=COLORS[:len(cpa_sorted)])
axes[1].set_xlabel('Cost per Acquisition ($)')
axes[1].set_title('CPA by Channel', fontsize=14, fontweight='bold')
for i, v in enumerate(cpa_sorted['cpa']):
    axes[1].text(v + 0.2, i, f'${v:.2f}', va='center', fontsize=10)

# CTR by Channel
ctr_sorted = channel_summary.sort_values('ctr', ascending=True)
axes[2].barh(ctr_sorted['channel'], ctr_sorted['ctr'], color=COLORS[:len(ctr_sorted)])
axes[2].set_xlabel('Click-Through Rate (%)')
axes[2].set_title('CTR by Channel', fontsize=14, fontweight='bold')
for i, v in enumerate(ctr_sorted['ctr']):
    axes[2].text(v + 0.1, i, f'{v:.2f}%', va='center', fontsize=10)

fig.suptitle('Channel Performance Comparison', fontsize=16, fontweight='bold', y=1.02)
plt.tight_layout()
save_fig(fig, '01_channel_performance')


# ============================================================
# 2. MONTHLY SPEND & REVENUE TREND
# ============================================================
print("📊 2. Monthly Trends")

monthly_trend = daily_full.groupby(daily_full['date'].dt.to_period('M')).agg(
    spend=('spend', 'sum'),
    revenue=('revenue', 'sum'),
    conversions=('conversions', 'sum'),
).reset_index()
monthly_trend['date'] = monthly_trend['date'].dt.to_timestamp()

fig, ax1 = plt.subplots(figsize=(14, 6))
ax2 = ax1.twinx()

ax1.bar(monthly_trend['date'], monthly_trend['spend'], width=20, alpha=0.6,
        color=COLORS[0], label='Spend')
ax2.plot(monthly_trend['date'], monthly_trend['revenue'], color=COLORS[1],
         linewidth=2.5, marker='o', markersize=5, label='Revenue')

ax1.set_xlabel('Month')
ax1.set_ylabel('Spend ($)', color=COLORS[0])
ax2.set_ylabel('Revenue ($)', color=COLORS[1])
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x:,.0f}'))

lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left')

plt.title('Monthly Spend vs Revenue Trend', fontsize=16, fontweight='bold')
plt.tight_layout()
save_fig(fig, '02_monthly_trend')


# ============================================================
# 3. REGION PERFORMANCE
# ============================================================
print("📊 3. Regional Analysis")

region_summary = daily_full.groupby('region').agg(
    spend=('spend', 'sum'),
    revenue=('revenue', 'sum'),
    conversions=('conversions', 'sum'),
).reset_index()
region_summary['roas'] = region_summary['revenue'] / region_summary['spend'].replace(0, 1)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Spend distribution
axes[0].pie(region_summary['spend'], labels=region_summary['region'],
           autopct='%1.1f%%', colors=COLORS[:4], startangle=90,
           textprops={'fontsize': 12})
axes[0].set_title('Spend Distribution by Region', fontsize=14, fontweight='bold')

# ROAS by region
bars = axes[1].bar(region_summary['region'], region_summary['roas'], color=COLORS[:4])
axes[1].set_ylabel('ROAS')
axes[1].set_title('ROAS by Region', fontsize=14, fontweight='bold')
for bar, val in zip(bars, region_summary['roas']):
    axes[1].text(bar.get_x() + bar.get_width()/2., bar.get_height() + 1,
                f'{val:.1f}x', ha='center', fontsize=12, fontweight='bold')

plt.tight_layout()
save_fig(fig, '03_regional_analysis')


# ============================================================
# 4. LEAD FUNNEL ANALYSIS
# ============================================================
print("📊 4. Lead Funnel")

funnel_order = ['New', 'Contacted', 'Qualified', 'Proposal', 'Won', 'Lost']
funnel_data = leads['lead_status'].value_counts().reindex(
    [s for s in funnel_order if s != 'Lost']
)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

# Funnel
colors_funnel = [COLORS[0], COLORS[6], COLORS[1], COLORS[4], COLORS[2]]
bars = axes[0].barh(funnel_data.index[::-1], funnel_data.values[::-1], color=colors_funnel[::-1])
axes[0].set_xlabel('Number of Leads')
axes[0].set_title('Lead Conversion Funnel', fontsize=14, fontweight='bold')
for bar, val in zip(bars, funnel_data.values[::-1]):
    axes[0].text(bar.get_width() + 50, bar.get_y() + bar.get_height()/2.,
                f'{val:,}', va='center', fontsize=11)

# Win rate by channel
win_rate = leads.groupby('channel').agg(
    total=('lead_id', 'count'),
    won=('is_won', 'sum')
).reset_index()
win_rate['win_rate'] = (win_rate['won'] / win_rate['total'] * 100).round(1)
win_rate = win_rate.sort_values('win_rate', ascending=True)

axes[1].barh(win_rate['channel'], win_rate['win_rate'], color=COLORS[:len(win_rate)])
axes[1].set_xlabel('Win Rate (%)')
axes[1].set_title('Lead Win Rate by Channel', fontsize=14, fontweight='bold')
for i, v in enumerate(win_rate['win_rate']):
    axes[1].text(v + 0.3, i, f'{v:.1f}%', va='center', fontsize=10)

plt.tight_layout()
save_fig(fig, '04_lead_funnel')


# ============================================================
# 5. DAY-OF-WEEK HEATMAP
# ============================================================
print("📊 5. Day-of-Week Patterns")

dow_channel = daily_full.groupby(['day_of_week', 'channel']).agg(
    avg_conversions=('conversions', 'mean')
).reset_index()

dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
pivot = dow_channel.pivot(index='channel', columns='day_of_week', values='avg_conversions')
pivot = pivot[dow_order]

fig, ax = plt.subplots(figsize=(12, 6))
sns.heatmap(pivot, annot=True, fmt='.1f', cmap='YlOrRd', ax=ax,
            linewidths=0.5, cbar_kws={'label': 'Avg Daily Conversions'})
ax.set_title('Average Conversions by Channel & Day of Week', fontsize=14, fontweight='bold')
ax.set_ylabel('')
plt.tight_layout()
save_fig(fig, '05_dow_heatmap')


# ============================================================
# 6. CAMPAIGN TYPE EFFICIENCY
# ============================================================
print("📊 6. Campaign Type Analysis")

type_summary = daily_full.groupby('campaign_type').agg(
    spend=('spend', 'sum'),
    revenue=('revenue', 'sum'),
    conversions=('conversions', 'sum'),
    clicks=('clicks', 'sum'),
).reset_index()
type_summary['roas'] = type_summary['revenue'] / type_summary['spend'].replace(0, 1)
type_summary['cpa'] = type_summary['spend'] / type_summary['conversions'].replace(0, 1)

fig, axes = plt.subplots(1, 2, figsize=(14, 6))

type_sorted = type_summary.sort_values('roas', ascending=True)
axes[0].barh(type_sorted['campaign_type'], type_sorted['roas'], color=COLORS[:len(type_sorted)])
axes[0].set_xlabel('ROAS')
axes[0].set_title('ROAS by Campaign Type', fontsize=14, fontweight='bold')
for i, v in enumerate(type_sorted['roas']):
    axes[0].text(v + 0.5, i, f'{v:.1f}x', va='center', fontsize=10)

# Spend vs Revenue bubble
scatter = axes[1].scatter(
    type_summary['spend'], type_summary['revenue'],
    s=type_summary['conversions'] * 0.5,
    c=range(len(type_summary)), cmap='Set2', alpha=0.7, edgecolors='black'
)
for _, row in type_summary.iterrows():
    axes[1].annotate(row['campaign_type'], (row['spend'], row['revenue']),
                    fontsize=8, ha='center', va='bottom')
axes[1].set_xlabel('Total Spend ($)')
axes[1].set_ylabel('Total Revenue ($)')
axes[1].set_title('Spend vs Revenue (bubble = conversions)', fontsize=14, fontweight='bold')
axes[1].xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1000:.0f}K'))
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, p: f'${x/1e6:.1f}M'))

plt.tight_layout()
save_fig(fig, '06_campaign_type_analysis')


# ============================================================
# SUMMARY STATS
# ============================================================
print("\n" + "=" * 60)
print("  KEY FINDINGS")
print("=" * 60)

best_channel = channel_summary.sort_values('roas', ascending=False).iloc[0]
worst_channel = channel_summary.sort_values('roas', ascending=True).iloc[0]
best_region = region_summary.sort_values('roas', ascending=False).iloc[0]

print(f"  Best ROAS Channel:  {best_channel['channel']} ({best_channel['roas']:.1f}x)")
print(f"  Worst ROAS Channel: {worst_channel['channel']} ({worst_channel['roas']:.1f}x)")
print(f"  Best ROAS Region:   {best_region['region']} ({best_region['roas']:.1f}x)")
print(f"  Overall Win Rate:   {leads['is_won'].mean()*100:.1f}%")
print(f"  Avg Deal Value (Won): ${leads[leads['is_won']==1]['deal_value'].mean():,.2f}")
print("=" * 60)
print("\n✅ All visualizations saved to docs/figures/")
