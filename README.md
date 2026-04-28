# Marketing Analytics Dashboard

End-to-end analysis of a SaaS company's multi-channel marketing campaigns. From raw data to actionable insights with Python ETL pipeline, exploratory analysis, and Power BI dashboard.

## 🎯 Business Problem
A mid-size SaaS company runs marketing campaigns across 7 channels (Google Ads, Meta, LinkedIn, Email, TikTok, Organic Social, Content/SEO) targeting 4 regions (LATAM, North America, Europe, APAC). The marketing team needs answers to:

- Which channels deliver the best return on ad spend (ROAS)?
- How should budget be reallocated to maximize conversions?
- What's the lead funnel efficiency by channel and region?
- Are there seasonal or day-of-week patterns to exploit?
- Which campaign types generate the highest quality leads?

## 📁 Project Structure

marketing-analytics/
├── data/
│   ├── raw/                          # Original generated datasets
│   │   ├── campaigns.csv
│   │   ├── daily_performance.csv
│   │   └── leads.csv
│   └── processed/                    # Clean, transformed tables
│       ├── dim_campaigns.csv
│       ├── dim_dates.csv
│       ├── fact_daily_performance.csv
│       ├── fact_leads.csv
│       ├── agg_monthly_channel.csv
│       ├── agg_campaign_performance.csv
│       ├── agg_lead_funnel.csv
│       └── marketing_analytics_data.xlsx
├── scripts/
│   ├── 01_generate_data.py
│   ├── 02_etl_pipeline.py
│   └── 03_eda_analysis.py
├── dashboards/
│   └── marketing_dashboard.pbix
├── docs/
│   └── figures/
├── requirements.txt
└── README.md

## 🔧 Tech Stack
| Tool | Purpose |
|------|---------|
| Python 3.10+ | ETL pipeline, data generation, analysis |
| Pandas / NumPy | Data manipulation and transformation |
| Matplotlib / Seaborn | Statistical visualizations |
| Power BI | Interactive dashboard |
| Git / GitHub | Version control |

## 🔄 ETL Pipeline
The pipeline (`02_etl_pipeline.py`) follows a structured Extract → Transform → Load process:

- **Extract:** Reads 3 raw CSV files (campaigns, daily performance, leads)
- **Transform:** Data type casting, null handling, KPI computation (CTR, CPC, CPA, ROAS), time dimension enrichment, lead scoring model, budget tier classification
- **Load:** Outputs 7 analysis-ready tables (CSV + consolidated Excel workbook)

**Data Model (Star Schema)**

dim_campaigns ─────┐
│
dim_dates ─────────┼──── fact_daily_performance
│
└──── fact_leads

## 📊 Power BI Dashboard
The interactive dashboard includes 3 pages:

**1. Executive Summary**
- KPI cards: Total Revenue, Spend, ROAS, Conversions
- ROAS evolution by month
- Spend vs Revenue trend
- Channel performance table

**2. Channel Deep Dive**
- Filterable KPIs by channel
- ROAS and Spend vs Revenue evolution
- Detailed table: Spend, Revenue, ROAS, Conversions, Clicks

**3. Lead Funnel**
- KPIs: Total Leads, Won, Conversion Rate (14.3%)
- Funnel by stage: New → Contacted → Qualified → Proposal → Won
- Leads by channel
- Filter by region

## 🖼️ Dashboard Screenshots

![Executive Summary](docs/figures/Executive%20Summary.png)

![Channel Deep Dive](docs/figures/Channel%20deep%20dive.png)

![Lead Funnel](docs/figures/Lead%20Funnel.png)

📌 To use: Open `dashboards/marketing_dashboard.pbix` in Power BI Desktop and connect to `data/processed/marketing_analytics_data.xlsx`

## 📈 Key Findings
- **Email Marketing** delivers the highest ROAS — most cost-efficient channel
- **LinkedIn Ads** shows the highest conversion rate (5.2%) despite higher CPC — strong for B2B
- **TikTok Ads** has the lowest CPA but lower lead quality
- **North America** generates the highest revenue per conversion
- **LATAM** receives ~30% of spend with competitive ROAS — growth opportunity
- Weekdays consistently outperform weekends for B2B conversions
- Q4 shows seasonal uplift across all channels

## 📌 Recommendations
1. Increase Email Marketing budget — highest ROAS with lowest CPA
2. Scale LinkedIn for enterprise leads — best lead quality and win rate
3. Reduce TikTok spend or reposition — poor funnel conversion
4. Shift weekend budget to weekdays — consistent B2B pattern
5. Invest more in LATAM — competitive ROAS with room for growth

## 🚀 How to Run
```bash
git clone https://github.com/federicooscargiglio/marketing-analytics.git
cd marketing-analytics
pip install -r requirements.txt
python scripts/01_generate_data.py
python scripts/02_etl_pipeline.py
python scripts/03_eda_analysis.py
```

## 👤 Author
**Federico Giglio**
📍 Buenos Aires, Argentina
🎓 Diploma in Data Science (UTN)
💼 Aspiring Data/BI Analyst
[LinkedIn](https://www.linkedin.com/in/federicooscargiglio)

## 📄 License
MIT License
