# -*- coding: utf-8 -*-
"""
Marketing Analytics Data Pipeline (Plotly-free version)
"""

import pandas as pd
import json
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import numpy as np
import base64
from io import BytesIO

print("="*60)
print("MARKETING ANALYTICS DATA PIPELINE")
print("="*60)

# ============================================
# 1. LOAD DATA DIRECTLY FROM GITHUB
# ============================================
print("\nLoading data from GitHub...")

fb = pd.read_csv('https://raw.githubusercontent.com/ej29-r3d/Marketing-Analytics-Assignments/main/marketing-analyst-assignment/01_facebook_ads.csv')
google = pd.read_csv('https://raw.githubusercontent.com/ej29-r3d/Marketing-Analytics-Assignments/main/marketing-analyst-assignment/02_google_ads.csv')
tiktok = pd.read_csv('https://raw.githubusercontent.com/ej29-r3d/Marketing-Analytics-Assignments/main/marketing-analyst-assignment/03_tiktok_ads.csv')

print(f"✓ Facebook: {len(fb)} rows")
print(f"✓ Google: {len(google)} rows")
print(f"✓ TikTok: {len(tiktok)} rows")

# ============================================
# 2. STANDARDIZE COLUMN NAMES
# ============================================
print("\nStandardizing schemas...")

# Rename date columns to 'Date' (capital D) for consistency
fb = fb.rename(columns={'date': 'Date'})
google = google.rename(columns={'date': 'Date'})
tiktok = tiktok.rename(columns={'date': 'Date'})

# Standardize other columns
fb = fb.rename(columns={
    'spend': 'cost',
    'ad_set_id': 'subcampaign_id',
    'ad_set_name': 'subcampaign_name'
})

google = google.rename(columns={
    'ad_group_id': 'subcampaign_id',
    'ad_group_name': 'subcampaign_name'
})

tiktok = tiktok.rename(columns={
    'adgroup_id': 'subcampaign_id',
    'adgroup_name': 'subcampaign_name'
})

# Add platform identifiers
fb['platform'] = 'Facebook'
google['platform'] = 'Google'
tiktok['platform'] = 'TikTok'

print("✓ Column names standardized")

# ============================================
# 3. CONVERT DATES
# ============================================
print("\nConverting dates...")
fb['Date'] = pd.to_datetime(fb['Date'])
google['Date'] = pd.to_datetime(google['Date'])
tiktok['Date'] = pd.to_datetime(tiktok['Date'])
print("✓ Dates converted")

# ============================================
# 4. CREATE UNIFIED DATAFRAME
# ============================================
print("\nCreating unified table...")

common_cols = ['Date', 'campaign_id', 'campaign_name', 'subcampaign_id', 
               'subcampaign_name', 'impressions', 'clicks', 'cost', 'conversions', 'platform']

unified = pd.concat([
    fb[common_cols],
    google[common_cols],
    tiktok[common_cols]
], ignore_index=True)

print(f"✓ Unified: {len(unified)} rows")
print(f"✓ Date range: {unified['Date'].min().date()} to {unified['Date'].max().date()}")
print(f"✓ Platforms: {', '.join(unified['platform'].unique())}")

# ============================================
# 5. CALCULATE DERIVED METRICS
# ============================================
print("\nCalculating metrics...")

unified['ctr'] = (unified['clicks'] / unified['impressions'] * 100).round(2)
unified['cpc'] = (unified['cost'] / unified['clicks']).round(2)
unified['cpa'] = (unified['cost'] / unified['conversions']).round(2)

# Handle division by zero
unified = unified.replace([float('inf'), -float('inf')], 0).fillna(0)

print("✓ CTR, CPC, CPA calculated")

# ============================================
# 6. EXPORT TO JSON (for Godot)
# ============================================
print("\nExporting to JSON...")

json_data = {
    'metadata': {
        'total_rows': len(unified),
        'platforms': unified['platform'].unique().tolist(),
        'date_start': unified['Date'].min().isoformat(),
        'date_end': unified['Date'].max().isoformat(),
        'generated': datetime.now().isoformat()
    },
    'summary': {
        'total_cost': float(unified['cost'].sum()),
        'total_impressions': int(unified['impressions'].sum()),
        'total_clicks': int(unified['clicks'].sum()),
        'total_conversions': int(unified['conversions'].sum()),
        'avg_ctr': float(unified['ctr'].mean()),
        'avg_cpc': float(unified['cpc'].mean()),
        'avg_cpa': float(unified['cpa'].mean())
    },
    'by_platform': unified.groupby('platform').agg({
        'cost': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum'
    }).round(2).to_dict(),
    'daily_data': unified.groupby(['Date', 'platform']).agg({
        'cost': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum'
    }).reset_index().to_dict('records')
}

with open('unified_ads_data.json', 'w') as f:
    json.dump(json_data, f, indent=2, default=str)

print("✓ Saved: unified_ads_data.json")

# ============================================
# 7. GENERATE MATPLOTLIB DASHBOARD
# ============================================
print("\nGenerating matplotlib dashboard...")

# Aggregate data
daily = unified.groupby(['Date', 'platform'])[['cost', 'conversions']].sum().reset_index()
platform_summary = unified.groupby('platform')['cost'].sum()

# Create figure with subplots
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
fig.suptitle('Cross-Platform Advertising Performance Dashboard', fontsize=16, fontweight='bold')

# Plot 1: Daily Cost by Platform
for platform in daily['platform'].unique():
    data = daily[daily['platform'] == platform]
    axes[0, 0].plot(data['Date'], data['cost'], marker='o', label=platform, linewidth=2)
axes[0, 0].set_title('Daily Cost by Platform')
axes[0, 0].set_xlabel('Date')
axes[0, 0].set_ylabel('Cost (USD)')
axes[0, 0].legend()
axes[0, 0].grid(True, alpha=0.3)
axes[0, 0].xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
plt.setp(axes[0, 0].xaxis.get_majorticklabels(), rotation=45)

# Plot 2: Platform Share of Spend (Pie Chart)
axes[0, 1].pie(platform_summary.values, labels=platform_summary.index, autopct='%1.1f%%', startangle=90)
axes[0, 1].set_title(f'Platform Share of Total Spend (${unified["cost"].sum():,.2f})')

# Plot 3: CTR by Platform (Box Plot)
ctr_data = [unified[unified['platform'] == p]['ctr'].values for p in unified['platform'].unique()]
axes[1, 0].boxplot(ctr_data, labels=unified['platform'].unique())
axes[1, 0].set_title('CTR Distribution by Platform')
axes[1, 0].set_ylabel('CTR (%)')
axes[1, 0].grid(True, alpha=0.3)

# Plot 4: CPA by Platform (Bar Chart)
cpa_by_platform = unified.groupby('platform')['cpa'].mean()
axes[1, 1].bar(cpa_by_platform.index, cpa_by_platform.values, color=['#1877F2', '#EA4335', '#000000'])
axes[1, 1].set_title('Average CPA by Platform')
axes[1, 1].set_ylabel('CPA (USD)')
axes[1, 1].grid(True, alpha=0.3)

plt.tight_layout()

# Save plot to buffer
buffer = BytesIO()
plt.savefig(buffer, format='png', dpi=100, bbox_inches='tight')
plot_data = base64.b64encode(buffer.getvalue()).decode()
plt.close()

# Create HTML dashboard
print("\nCreating HTML dashboard...")

html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Marketing Analytics Dashboard</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 40px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: auto;
            background-color: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            text-align: center;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px,1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }}
        .card h3 {{
            margin: 0 0 10px 0;
            font-size: 14px;
            opacity: 0.9;
        }}
        .card p {{
            margin: 0;
            font-size: 24px;
            font-weight: bold;
        }}
        img {{
            width: 100%;
            height: auto;
            margin: 20px 0;
        }}
        hr {{
            margin: 20px 0;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: right;
        }}
        th {{
            background-color: #667eea;
            color: white;
            text-align: center;
        }}
        td:first-child {{
            text-align: left;
            font-weight: bold;
        }}
    </style>
</head>
<body>
<div class="container">
    <h1>📊 Cross-Platform Advertising Dashboard</h1>
    
    <div class="summary">
        <div class="card"><h3>Total Spend</h3><p>${unified['cost'].sum():,.2f}</p></div>
        <div class="card"><h3>Total Impressions</h3><p>{unified['impressions'].sum():,.0f}</p></div>
        <div class="card"><h3>Total Clicks</h3><p>{unified['clicks'].sum():,.0f}</p></div>
        <div class="card"><h3>Total Conversions</h3><p>{unified['conversions'].sum():,.0f}</p></div>
        <div class="card"><h3>Overall CTR</h3><p>{unified['clicks'].sum() / unified['impressions'].sum() * 100:.2f}%</p></div>
        <div class="card"><h3>Overall CPA</h3><p>${unified['cost'].sum() / unified['conversions'].sum():.2f}</p></div>
    </div>
    
    <hr>
    <img src="data:image/png;base64,{plot_data}" alt="Dashboard Charts">
    
    <hr>
    <h3>Performance by Platform</h3>
    {unified.groupby('platform')[['cost', 'impressions', 'clicks', 'conversions', 'ctr', 'cpc', 'cpa']].agg({
        'cost': 'sum',
        'impressions': 'sum',
        'clicks': 'sum',
        'conversions': 'sum',
        'ctr': 'mean',
        'cpc': 'mean',
        'cpa': 'mean'
    }).round(2).to_html()}
    
    <hr>
    <p><small>Data source: GitHub | Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    <p><small>Dashboard runs locally — data refreshes from source on each execution</small></p>
</div>
</body>
</html>
"""

with open('marketing_dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("✓ Saved: marketing_dashboard.html")

# ============================================
# 8. PRINT SUMMARY
# ============================================
print("\n" + "="*60)
print("CAMPAIGN PERFORMANCE SUMMARY")
print("="*60)
print(f"💰 Total Spend:        ${unified['cost'].sum():,.2f}")
print(f"👁️  Total Impressions:  {unified['impressions'].sum():,.0f}")
print(f"🖱️  Total Clicks:       {unified['clicks'].sum():,.0f}")
print(f"🎯 Total Conversions:  {unified['conversions'].sum():,.0f}")
print(f"📈 Overall CTR:        {unified['clicks'].sum() / unified['impressions'].sum() * 100:.2f}%")
print(f"💵 Overall CPC:        ${unified['cost'].sum() / unified['clicks'].sum():.2f}")
print(f"💸 Overall CPA:        ${unified['cost'].sum() / unified['conversions'].sum():.2f}")

print("\n📊 PERFORMANCE BY PLATFORM:")
print("="*60)
platform_summary = unified.groupby('platform')[['cost', 'impressions', 'clicks', 'conversions']].sum().round(2)
print(platform_summary.to_string())

print("\n" + "="*60)
print("✅ PIPELINE COMPLETE!")
print("="*60)
print("\n📁 OUTPUT FILES:")
print("   1. unified_ads_data.json  → Load this in Godot")
print("   2. marketing_dashboard.html → Open in ANY browser")
print("\n🚀 NEXT STEPS:")
print("   - Double-click marketing_dashboard.html to view your dashboard")
print("   - Upload to GitHub Pages / Itch.io for a live link")
print("   - Use unified_ads_data.json in your Godot project")
print("="*60)