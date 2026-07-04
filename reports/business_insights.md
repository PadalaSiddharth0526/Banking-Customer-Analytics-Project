# Business Insights Report
## Banking Customer Analytics Project

All figures below are computed directly from `data/processed/bank_customers_revenue.csv`
(10,000 cleaned customer records) via the modules in `src/`. Reproduce any number with:
```bash
python run_pipeline.py
```

---

### Churn Insights

**1. Overall churn is high and worth prioritizing.**
32.6% of customers have churned - roughly 1 in 3. At this scale, even a
2-3 point reduction in churn represents thousands of retained relationships.

**2. Senior customers (60+) are the single highest-risk age group.**
Churn rises from 17% (18-29) to 45% (60+) in a near-linear pattern by age band, with
the sharpest jump after age 50 (30% churn in the 50-59 band vs. 45% in 60+).
*Action: build a dedicated retirement-transition advisory track.*

**3. Inactive members churn 64% more often than active members.**
Inactive members churn at 41.0% vs. 25.0% for active members (lift = 1.26x).
Activity level is the second-strongest churn driver in the dataset after age.

**4. Single-product customers are the most likely to leave.**
Customers with only 1 product churn at 40.1%, more than triple the rate of
customers with 3 products (12.6%). Product depth is strongly protective.

**5. Germany has a structurally higher churn rate than France or Spain.**
Germany: 40.2% churn vs. France 30.1% and Spain 30.1%. This 10-point gap
persists even after accounting for demographic mix, suggesting a local
market or competitive issue rather than random variation.

**6. Zero-balance accounts are the most likely to churn by balance band.**
36.5% of zero-balance customers churn, the highest of any balance band,
compared to 24.0% for customers with $150K+. These are likely dormant
"parked" relationships.

**7. Gender has only a marginal effect on churn.**
Female customers churn slightly more than male customers (33.7% vs. 31.4%),
a modest 4% lift - not a priority lever compared to activity or product count.

**8. Holding a credit card has almost no independent effect on churn.**
32.9% (no card) vs. 32.4% (has card) - card ownership alone doesn't predict
retention; it's the *combination* with activity and product count that matters.

**9. Tenure alone is a weak churn predictor.**
Churn is fairly flat across tenure bands (31.6%-34.0%), meaning "how long
someone has been a customer" matters far less than *how engaged* they are today.

**10. The combination of "senior + inactive + single product" is the highest-risk profile.**
These three factors compound: Senior customers show 1.39x lift, inactive
members 1.26x, and single-product holders 1.23x - customers matching all
three should be the top of any retention outreach list (see
`sql/03_views.sql :: vw_churn_risk_watchlist`).

---

### Revenue Insights

**11. Total estimated annual revenue across the portfolio is ~$17.85M.**
Based on the documented revenue-proxy model in `src/revenue_analysis.py`
(net interest margin on deposits + per-product fees + card interchange).

**12. High-Value customers generate over 3x the revenue-per-customer of Medium-Value customers.**
$2,217.76 avg. revenue vs. $1,085.67 - despite being a similar-sized group
by count (6,180 vs. 3,820), High-Value customers drive the majority of
total portfolio revenue ($13.7M of $17.85M, ~77%).

**13. France is the largest revenue market by total dollars, but not by average customer value.**
France contributes $8.97M in total revenue (largest customer base), while
average revenue per customer is nearly identical across all three
countries (~$1,770-$1,800) - revenue scale comes from customer count, not
market-level differences in customer value.

**14. Customers with more products generate meaningfully more revenue per head.**
Average revenue rises steadily from $1,651.59 (1 product) to $2,173.92
(4 products) - each additional product is worth real incremental revenue,
reinforcing the case for cross-selling.

**15. "Established, High-Value" customers are the single largest revenue segment.**
This segment (age 35-59, High-Value tier) alone generates $8.69M - roughly
half of total portfolio revenue - making it the segment most worth
protecting and investing in.

**16. Senior High-Value customers are the second-largest revenue segment despite elevated churn risk.**
$4.75M in revenue sits with High-Value Seniors, who also carry the highest
churn rate by age band - this is the highest-stakes retention priority
in the entire portfolio.

**17. Young Professionals are a small but underdeveloped revenue segment.**
Only 202 customers (2%) fall into this life-stage band, generating a
modest $266K in the High-Value tier - there is room to grow this segment
through early-career product bundles (e.g. starter cards, micro-savings).

---

### Segmentation & Customer Base Insights

**18. Nearly 1 in 4 customers (24.6%) are flagged High-Risk (inactive + single product).**
This is a large, addressable population - a scaled re-engagement and
cross-sell campaign targeting this group has outsized potential ROI.

**19. Premium customers are a small, high-value niche (3.9% of the base).**
394 customers meet the Premium bar (top-decile balance, active, credit
card holder) - small enough to receive white-glove relationship management
rather than mass-market treatment.

**20. High-Value customers churn less than Medium-Value customers.**
27% churn (High-Value) vs. 41% churn (Medium-Value) - deeper, wealthier
relationships are inherently stickier, reinforcing that cross-selling
and balance growth are also *retention* strategies, not just revenue plays.

**21. The customer base skews toward "Established" life-stage (63% of customers).**
Most of the portfolio sits in the 35-59 age band; marketing and product
strategy should be built primarily around this group's needs (mortgages,
family banking, wealth building) while carving out distinct tracks for
the smaller Young Professional and Senior segments.

**22. Cross-sell opportunity: over half of customers (51%) hold only one product.**
Given single-product customers churn at 3x the rate of 3-product holders
and are worth ~24% less in average annual revenue, this is the single
largest lever available to both grow revenue and reduce churn simultaneously.

---

## Top 3 Priorities for Leadership

1. **Launch a targeted retention program for "Senior + Inactive + Single-Product" customers** -
   the compounding risk profile identified in insights #2, #3, #4, and #10.
2. **Scale cross-selling to single-product customers**, starting with the
   Established life-stage segment where the revenue base is largest (insight #22).
3. **Investigate the Germany churn gap** with local market research, since a
   10-point churn premium versus France/Spain (insight #5) cannot be
   explained by product mix or activity levels alone in this dataset.
