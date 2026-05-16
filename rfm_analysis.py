# rfm_analysis.py
# Builds a full RFM customer segmentation model
# using PostgreSQL as the data source
# This is the most widely used customer analytics
# technique in retail

import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
from config import CONNECTION_STRING
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date

engine = create_engine(CONNECTION_STRING)

# ── STEP 1: PULL TRANSACTION DATA FROM POSTGRESQL ─────────────────
def load_transaction_data():
    """
    Pulls customer transaction history from PostgreSQL
    We only want positive transactions (no returns)
    and only customers we can identify (no guest checkouts)
    """
    print("  Loading transaction data from PostgreSQL...")

    query = """
        SELECT
            t.customer_id,
            t.transaction_date,
            t.total_value,
            c.full_name,
            c.region,
            c.age_group,
            c.loyalty_member
        FROM transactions t
        JOIN customers c
          ON t.customer_id = c.customer_id
        WHERE t.quantity    > 0
          AND t.customer_id IS NOT NULL
        ORDER BY t.customer_id, t.transaction_date
    """

    df = pd.read_sql(query, engine)
    df['transaction_date'] = pd.to_datetime(df['transaction_date'])
    print(f"  Loaded {len(df):,} transactions")
    print(f"  Covering {df['customer_id'].nunique():,} customers")
    return df

# ── STEP 2: CALCULATE RFM SCORES ──────────────────────────────────
def calculate_rfm(df):
    """
    Calculates Recency, Frequency, and Monetary values
    for each customer

    Recency   = days since last purchase
    Frequency = total number of purchases
    Monetary  = total amount spent
    """
    print("\n  Calculating RFM values...")

    # Reference date = day after last transaction
    # Think of it like asking "as of today, how long ago
    # did each customer last buy?"
    reference_date = df['transaction_date'].max() \
                     + pd.Timedelta(days=1)

    rfm = df.groupby('customer_id').agg(
        recency   = ('transaction_date',
                     lambda x: (reference_date - x.max()).days),
        frequency = ('transaction_id' if 'transaction_id' in df.columns
                     else 'transaction_date', 'count'),
        monetary  = ('total_value', 'sum')
    ).reset_index()

    rfm['monetary'] = rfm['monetary'].round(2)

    print(f"  RFM calculated for {len(rfm):,} customers")
    print(f"\n  RFM Summary:")
    print(f"  Avg Recency   : {rfm['recency'].mean():.0f} days")
    print(f"  Avg Frequency : {rfm['frequency'].mean():.1f} purchases")
    print(f"  Avg Monetary  : £{rfm['monetary'].mean():.2f}")
    return rfm

# ── STEP 3: SCORE EACH CUSTOMER 1-5 ──────────────────────────────
def score_rfm(rfm):
    """
    Scores each customer 1-5 on each dimension
    Uses quintiles — splits customers into 5 equal groups

    For Recency:   lower days = better = score 5
    For Frequency: higher count = better = score 5
    For Monetary:  higher spend = better = score 5
    """
    print("\n  Scoring customers 1-5 on each dimension...")

    # pd.qcut splits into equal-sized buckets
    # For recency we reverse the labels (5=most recent)
    rfm['r_score'] = pd.qcut(
        rfm['recency'],
        q      = 5,
        labels = [5, 4, 3, 2, 1]  # reversed — lower recency = better
    ).astype(int)

    rfm['f_score'] = pd.qcut(
        rfm['frequency'].rank(method='first'),
        q      = 5,
        labels = [1, 2, 3, 4, 5]
    ).astype(int)

    rfm['m_score'] = pd.qcut(
        rfm['monetary'].rank(method='first'),
        q      = 5,
        labels = [1, 2, 3, 4, 5]
    ).astype(int)

    # Combined RFM score — simple average
    rfm['rfm_score'] = (
        rfm['r_score'] +
        rfm['f_score'] +
        rfm['m_score']
    ) / 3

    rfm['rfm_score'] = rfm['rfm_score'].round(2)
    return rfm

# ── STEP 4: ASSIGN SEGMENTS ───────────────────────────────────────
def assign_segments(rfm):
    """
    Assigns each customer to a named segment
    based on their RFM scores

    This is where the analysis becomes actionable —
    each segment has a different marketing strategy
    """
    print("\n  Assigning customer segments...")

    def segment(row):
        r = row['r_score']
        f = row['f_score']
        m = row['m_score']

        if r >= 4 and f >= 4 and m >= 4:
            return 'Champion'
        elif r >= 3 and f >= 3 and m >= 3:
            return 'Loyal Customer'
        elif r >= 4 and f <= 2:
            return 'New Customer'
        elif r >= 3 and f >= 2 and m <= 2:
            return 'Potential Loyalist'
        elif r == 3 and f == 3:
            return 'Needs Attention'
        elif r <= 2 and f >= 3 and m >= 3:
            return 'At Risk'
        elif r <= 2 and f >= 4 and m >= 4:
            return 'Cannot Lose Them'
        elif r <= 2 and f <= 2 and m <= 2:
            return 'Lost'
        else:
            return 'Hibernating'

    rfm['segment'] = rfm.apply(segment, axis=1)

    # Segment summary
    segment_summary = rfm.groupby('segment').agg(
        customers = ('customer_id', 'count'),
        avg_recency   = ('recency',   'mean'),
        avg_frequency = ('frequency', 'mean'),
        avg_monetary  = ('monetary',  'mean'),
        total_revenue = ('monetary',  'sum')
    ).round(2).reset_index()

    segment_summary = segment_summary.sort_values(
        'total_revenue', ascending=False
    )

    print("\n  Customer Segments:")
    print(segment_summary.to_string(index=False))
    return rfm, segment_summary

# ── STEP 5: ADD CUSTOMER DETAILS ──────────────────────────────────
def enrich_rfm(rfm, df):
    """
    Adds customer details back to RFM table
    So we know not just the score but who the customer is
    """
    customer_details = df.groupby('customer_id').agg(
        full_name      = ('full_name',      'first'),
        region         = ('region',         'first'),
        age_group      = ('age_group',      'first'),
        loyalty_member = ('loyalty_member', 'first')
    ).reset_index()

    rfm_enriched = rfm.merge(customer_details,
                              on='customer_id',
                              how='left')
    return rfm_enriched

# ── STEP 6: SAVE RESULTS BACK TO POSTGRESQL ───────────────────────
def save_to_postgres(rfm_enriched):
    """
    Saves RFM results back into PostgreSQL
    So Power BI can connect to it directly
    This is the bridge between Python analysis
    and Power BI reporting
    """
    print("\n  Saving RFM results to PostgreSQL...")

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS customer_rfm"))
        conn.commit()

    rfm_enriched.to_sql(
        'customer_rfm',
        engine,
        if_exists = 'replace',
        index     = False
    )
    print(f"  Saved {len(rfm_enriched):,} customer RFM records")
    print("  Table name: customer_rfm")
    print("  Power BI can now connect to this table directly!")

# ── STEP 7: VISUALISATIONS ────────────────────────────────────────
def create_visualisations(rfm_enriched, segment_summary):
    """
    Creates 4 charts showing the RFM analysis results
    These go in your portfolio and GitHub README
    """
    print("\n  Creating visualisations...")
    sns.set_style("whitegrid")
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        'Customer RFM Segmentation Analysis',
        fontsize=16, fontweight='bold', y=1.02
    )

    # Chart 1 — Customer count per segment
    ax1 = axes[0, 0]
    colors = {
        'Champion'          : '#2ecc71',
        'Loyal Customer'    : '#27ae60',
        'New Customer'      : '#3498db',
        'Potential Loyalist': '#2980b9',
        'Needs Attention'   : '#f39c12',
        'At Risk'           : '#e67e22',
        'Cannot Lose Them'  : '#e74c3c',
        'Lost'              : '#c0392b',
        'Hibernating'       : '#95a5a6'
    }
    seg_colors = [
        colors.get(s, '#95a5a6')
        for s in segment_summary['segment']
    ]
    ax1.barh(
        segment_summary['segment'],
        segment_summary['customers'],
        color=seg_colors
    )
    ax1.set_title('Customers per Segment', fontweight='bold')
    ax1.set_xlabel('Number of Customers')

    # Chart 2 — Revenue per segment
    ax2 = axes[0, 1]
    ax2.bar(
        segment_summary['segment'],
        segment_summary['total_revenue'],
        color=seg_colors
    )
    ax2.set_title('Total Revenue per Segment', fontweight='bold')
    ax2.set_xlabel('Segment')
    ax2.set_ylabel('Revenue (£)')
    ax2.tick_params(axis='x', rotation=45)
    ax2.yaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f'£{x:,.0f}')
    )

    # Chart 3 — RFM Score distribution
    ax3 = axes[1, 0]
    ax3.hist(
        rfm_enriched['rfm_score'],
        bins=20,
        color='#3498db',
        edgecolor='white'
    )
    ax3.set_title(
        'Distribution of RFM Scores', fontweight='bold'
    )
    ax3.set_xlabel('RFM Score (1=Low, 5=High)')
    ax3.set_ylabel('Number of Customers')

    # Chart 4 — Average spend per segment
    ax4 = axes[1, 1]
    sns.barplot(
        data    = segment_summary,
        x       = 'avg_monetary',
        y       = 'segment',
        palette = 'RdYlGn',
        ax      = ax4
    )
    ax4.set_title(
        'Average Spend per Customer by Segment',
        fontweight='bold'
    )
    ax4.set_xlabel('Average Total Spend (£)')
    ax4.xaxis.set_major_formatter(
        plt.FuncFormatter(lambda x, _: f'£{x:,.0f}')
    )

    plt.tight_layout()
    plt.savefig(
        'rfm_analysis.png',
        dpi=150,
        bbox_inches='tight'
    )
    plt.show()
    print("  Charts saved: rfm_analysis.png")

# ── MASTER FUNCTION ───────────────────────────────────────────────
def run_rfm_analysis():
    print("\n" + "="*55)
    print("  RETAIL CUSTOMER RFM SEGMENTATION")
    print("="*55)

    df               = load_transaction_data()
    rfm              = calculate_rfm(df)
    rfm              = score_rfm(rfm)
    rfm, segment_sum = assign_segments(rfm)
    rfm_enriched     = enrich_rfm(rfm, df)

    save_to_postgres(rfm_enriched)
    create_visualisations(rfm_enriched, segment_sum)

    print("\n" + "="*55)
    print("  RFM ANALYSIS COMPLETE")
    print("  Results saved to PostgreSQL table: customer_rfm")
    print("  Ready to connect Power BI!")
    print("="*55)

if __name__ == '__main__':
    run_rfm_analysis()