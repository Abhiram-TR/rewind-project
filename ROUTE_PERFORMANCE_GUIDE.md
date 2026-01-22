# 📊 Route Performance Analytics - User Guide

## 🚀 Getting Started

### 1. **Access the Dashboard**
- **Login** to your KSRTC platform
- From the main dashboard, click the **"Route Performance"** card
- Or visit directly: `http://localhost:8000/performance/`

### 2. **Dashboard Overview**
The main dashboard displays:
- **Industry Metrics**: Average EPKM, total routes, revenue
- **Performance Charts**: Top vs bottom route comparison
- **EPKM Distribution**: High/Medium/Low categories  
- **Top Performers**: Best 5 routes by EPKM
- **Underperformers**: Lowest 5 routes needing attention

---

## 📈 Key Features & How to Use

### **1. Performance Metrics Cards**
- **Industry Avg EPKM**: Overall performance benchmark
- **Total Routes**: Number of active routes analyzed
- **Total Revenue**: Revenue for selected period
- **Best EPKM**: Highest performing route's EPKM

### **2. Interactive Charts**

#### **Performance Comparison Bar Chart**
- Shows **top 10** (green) vs **bottom 10** (red) routes
- Hover over bars to see exact EPKM values
- Use for quick visual comparison

#### **EPKM Distribution Doughnut Chart**
- **High (≥15)**: Excellent performance routes
- **Medium (10-15)**: Average performance routes  
- **Low (<10)**: Routes needing improvement

### **3. Top & Bottom Performers Lists**
- **Green cards**: Top 5 best performing routes
- **Red cards**: Bottom 5 underperforming routes
- Each shows: Route number, total revenue, trip count, EPKM

### **4. Date Range Filtering**
1. **Select Start Date**: Choose beginning of analysis period
2. **Select End Date**: Choose end of analysis period  
3. **Click "Update"**: Refresh dashboard with new data
4. **Default**: Last 30 days from today

### **5. Bulk Recalculation**
- **"Recalculate" Button**: Processes all route performance metrics
- Use when you have new trip/revenue data
- Shows progress notification when complete

---

## 🎯 Understanding EPKM (Earnings Per Kilometer)

### **What is EPKM?**
**EPKM = Total Revenue ÷ Total Distance (km)**

### **EPKM Categories:**
- **High (≥₹15/km)**: Excellent routes - maintain and replicate
- **Medium (₹10-15/km)**: Average routes - room for improvement  
- **Low (<₹10/km)**: Poor routes - needs immediate attention

### **What EPKM Tells You:**
- **Route Profitability**: Higher EPKM = more profitable
- **Efficiency**: Revenue generation per kilometer traveled
- **Performance Trends**: Improving/declining over time

---

## 📊 API Endpoints for Advanced Users

### **Get Route Performance Data**
```
GET /performance/api/performance/?start_date=2024-01-01&end_date=2024-01-31&route_no=123
```

### **Get Top Performers**
```
GET /performance/api/top-performers/?limit=10
```

### **Get Underperformers**
```
GET /performance/api/underperformers/?limit=10
```

### **Get Route Trends**
```
GET /performance/api/trends/?route_no=123&days=30
```

### **Bulk Calculate Metrics**
```
POST /performance/api/bulk-calculate/
{
    "start_date": "2024-01-01",
    "end_date": "2024-01-31",
    "period_type": "daily"
}
```

---

## 🔧 Management Commands

### **Calculate Performance Metrics**
```bash
# Calculate for last 30 days
python manage.py calculate_performance

# Calculate for specific date range
python manage.py calculate_performance --start-date 2024-01-01 --end-date 2024-01-31

# Calculate weekly metrics
python manage.py calculate_performance --period weekly
```

---

## 📈 Best Practices

### **1. Regular Monitoring**
- Check dashboard **weekly** for performance trends
- Monitor **top performers** to understand success factors
- Focus on **underperformers** for improvement opportunities

### **2. Data Analysis**
- Use **30-day periods** for meaningful analysis
- Compare **similar routes** (distance, stops, regions)
- Look for **seasonal patterns** in performance

### **3. Action Items**
- **High EPKM routes**: Study and replicate success factors
- **Low EPKM routes**: Investigate causes (pricing, demand, competition)
- **Declining trends**: Immediate intervention needed

### **4. Performance Improvement**
- **Route optimization**: Adjust stops, timing, frequency
- **Pricing strategy**: Review fare structures
- **Service quality**: Improve punctuality, comfort
- **Demand analysis**: Match capacity with passenger flow

---

## 🚨 Troubleshooting

### **No Data Showing?**
**IMPORTANT**: Your data is available from **2023-12-08 to 2024-10-22** only.

**Quick Fix:**
1. **Click "Load Sample"** button to use available data range (2024-10-15 to 2024-10-22)
2. **Or manually set dates** within the available range
3. **Click "Recalculate"** if needed

**Steps:**
1. Set Start Date: `2024-10-15` 
2. Set End Date: `2024-10-22`
3. Click "Update"
4. If still no data, click "Recalculate"

### **Charts Not Loading?**
1. Refresh the page
2. Check browser console for JavaScript errors
3. Ensure stable internet connection

### **Performance Issues?**
1. Use shorter date ranges (7-30 days)
2. Limit to specific routes when possible
3. Run calculations during off-peak hours

---

## 📞 Support

### **Technical Issues**
- Check Django logs for errors
- Verify database connectivity
- Ensure all migrations are applied

### **Data Questions**
- Verify BigQuery data sync is working
- Check trip revenue data completeness
- Validate EPKM calculations manually for sample routes

---

## 🎯 Quick Start Checklist

- [ ] **Access Dashboard**: Click "Route Performance" from main menu
- [ ] **Set Date Range**: Select last 30 days or specific period
- [ ] **Click Update**: Load performance data
- [ ] **Review Top Performers**: Identify best routes
- [ ] **Check Underperformers**: Find routes needing attention
- [ ] **Analyze Trends**: Look for patterns and insights
- [ ] **Take Action**: Plan improvements for low EPKM routes

**Your route performance analytics are now ready! Use these insights to optimize KSRTC operations and improve profitability.** 📊🚌