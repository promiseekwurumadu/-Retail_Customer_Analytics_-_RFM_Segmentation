 """# 🛒 Retail Customer Analytics & RFM Segmentation
### Project 1 of 3 | Role: Data Analyst | Domain: Retail & Supply Chain

---

## 📌 What This Project Is About

A retail business has customer transactions, product data, and store
information sitting in three separate systems that don't talk to each
other. Column names differ, formats differ, some records are missing.

This project builds a complete retail analytics solution:
1. Loads and cleans messy multi-source data into PostgreSQL
2. Builds a full RFM customer segmentation model in Python
3. Saves results back to PostgreSQL for live reporting
4. Delivers a 3-page interactive Power BI dashboard

---

## 📂 Dataset

- **Source:** Realistic synthetic retail data mirroring UK retail
  transaction structure (ONS Retail Sales format)
- **Customers:** 2,060 records across 10 UK regions
- **Products:** 498 products across 6 categories
- **Stores:** 50 UK retail locations
- **Transactions:** 50,000 records across Jan 2022 — Dec 2023
- **Total:** 52,608 rows across 4 tables in PostgreSQL

---

## 🧹 Real Data Quality Issues Solved

| Problem | Solution |
|---|---|
| Customer names in mixed UPPER/lower case | Title case standardisation |
| Product prices stored as £9.99 strings | Strip £ symbol, cast to float |
| Store dates in DD/MM/YYYY and YYYY-MM-DD | Mixed format parsing with dayfirst |
| Region names inconsistent across systems | Explicit mapping dictionary |
| Missing cost prices (12% of products) | Imputed at 60% of sell price |
| Duplicate customer records (3%) | Deduplication on customer_id |
| Guest checkouts with no customer_id | Retained as NULL — valid data |
| Online orders with no store_id | Retained as NULL — valid data |

---

## 🗄️ Database Design (PostgreSQL)

Four normalised tables loaded via Python SQLAlchemy:

- **customers** — 2,060 rows, demographic and loyalty data
- **products** — 498 rows, category, pricing, supplier
- **stores** — 50 rows, location, size, staffing
- **transactions** — 50,000 rows, fact table linking all dimensions
- **customer_rfm** — 2,060 rows, RFM scores and segments (derived)

---

## 👥 RFM Customer Segmentation

RFM stands for Recency, Frequency, Monetary — the most widely
used customer segmentation technique in retail.

Each customer is scored 1-5 on:
- **Recency** — how recently they bought (5 = most recent)
- **Frequency** — how often they buy (5 = most frequent)
- **Monetary** — how much they spend (5 = highest spender)

### Segments identified:

| Segment | Customers | Strategic Action |
|---|---|---|
| Hibernating | 400 | Win-back campaign — biggest opportunity |
| Loyal Customer | 385 | Upsell premium products |
| New Customer | 283 | Welcome nurture sequence |
| At Risk | 277 | Urgent retention offer this week |
| Potential Loyalist | 241 | Loyalty programme invitation |
| Champion | 239 | VIP rewards, early access |
| Lost | 235 | Final reactivation attempt |

### Key finding:
Loyal Customers — not Champions — drive the highest total revenue.
This suggests the business depends on consistent mid-tier spenders
rather than a small group of high-value customers. A risk if those
customers are lost to a competitor.

---

## 📊 Power BI Dashboard — 3 Pages

Connected live to PostgreSQL database:

**Page 1: Sales Overview**
- 4 KPI cards (Revenue, Transactions, Customers, Avg Order Value)
- Monthly revenue trend line chart
- Revenue by UK region bar chart
- Online vs In-Store donut chart
- Year slicer filtering all visuals

**Page 2: RFM Segmentation**
- Customers per segment bar chart
- Revenue per segment bar chart
- Average RFM score by segment
- Full customer detail table with scores
- Segment slicer filtering all visuals

**Page 3: Product Performance**
- Revenue by category bar chart
- Top 10 products by revenue
- Returns by category (DAX measure)
- Stock status donut chart

---

## 🔍 Key Business Insights

1. **May is peak revenue month** — not December as expected.
   Suggests a spring promotion effect worth investigating further.

2. **Electronics drives highest revenue** — highest margin category
   and most frequently purchased big ticket item.

3. **South East is top region** — consistent with UK disposable
   income distribution and population density.

4. **400 hibernating customers** represent a significant win-back
   opportunity — targeted campaign recommended immediately.

5. **277 at-risk customers** are slipping away right now —
   a retention offer this week could recover this segment.

---

## 🛠️ Tools Used

| Tool | Purpose |
|---|---|
| Python 3 | Data generation, cleaning, RFM analysis |
| PostgreSQL 18 | Production relational database |
| pgAdmin 4 | Database management and SQL querying |
| SQLAlchemy | Python to PostgreSQL connector |
| Pandas | Data manipulation and cleaning |
| Matplotlib & Seaborn | RFM visualisations |
| Power BI Desktop | Interactive business dashboard |

---

## ⚙️ How To Run This Project

```bash
# Step 1 — Install dependencies
pip install pandas numpy sqlalchemy psycopg2-binary faker matplotlib seaborn

# Step 2 — Configure database connection
# Edit config.py with your PostgreSQL password

# Step 3 — Generate raw data
python generate_data.py

# Step 4 — Load into PostgreSQL
python loader.py

# Step 5 — Run RFM analysis
python rfm_analysis.py

# Step 6 — Open Power BI
# Open retail_analytics_dashboard.pbix
# Refresh data source with your PostgreSQL credentials
```

---

## 💡 Key Concepts Demonstrated

| Concept | Where Demonstrated |
|---|---|
| Multi-source data integration | loader.py — 3 systems unified |
| Real data quality issues | 8 distinct problems identified and fixed |
| Relational database design | 5 tables with foreign key relationships |
| RFM segmentation | rfm_analysis.py — industry standard technique |
| Live BI reporting | Power BI connected directly to PostgreSQL |
| Actionable insight | Each segment has a specific business recommendation |

---

*Part of a 3-project Retail & Supply Chain Data portfolio*
*Projects: Data Analyst → Data Scientist → Data Engineer*
*Tools: PostgreSQL · pgAdmin · Power BI · Python · PySpark · Hadoop*
"""

