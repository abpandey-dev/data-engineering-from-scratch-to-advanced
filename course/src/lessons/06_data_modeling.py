from lib import *
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np



LESSON("Basics", "Grain: the most important word in modelling", """
<p>Before you design any table, finish this sentence: <b>"one row per ___"</b>. That's the <b>grain</b>.</p>
<table><tr><th>Table</th><th>Grain</th></tr>
<tr><td>orders</td><td>one row per order</td></tr>
<tr><td>order_lines</td><td>one row per product in an order</td></tr>
<tr><td>daily_sales</td><td>one row per store, per product, per day</td></tr></table>
<p>Most reporting bugs come from a misunderstood grain. If you think a table has one row per order, when it really has one per line, every count is wrong.</p>
<p><b>Check it, don't assume it:</b> a grain is correct only if those columns are unique. With rows (day 1, sku 1), (day 1, sku 2), (day 2, sku 1), the smallest key is <b>day + sku</b>.</p>
<p><b>Normalisation</b> stores each fact in exactly one place. If a customer's name is on every order, then changing it means updating thousands of rows, and missing one leaves "A" and "A." for one customer. That's an <b>update anomaly</b>. So split out a customers table, which is ideal for OLTP systems.</p>
<p><b>Keys.</b> A <b>natural key</b> is from the business, like an email. A <b>surrogate key</b> is an integer you generate, since natural keys can change or be reused. A <b>hash key</b> is built from several columns, is deterministic, and can be computed without looking anything up.</p>
""", practice=["Is This Column a Key?", "Find the Grain", "Normalise a Flat Table", "Spot the Update Anomaly", "Surrogate Keys", "Hash Key From Several Columns"])


LESSON("Core", "Star schemas: facts and dimensions", """
<p>Fully normalised data needs many joins, which makes analytics slow and hard. The <b>star schema</b>, due to Ralph Kimball, organises data for questions people ask.</p>
<div class="pic">              dim_date
                  │
dim_customer ── fact_orders ── dim_product
                  │
              dim_store</div>
<table><tr><th></th><th>Fact table</th><th>Dimension table</th></tr>
<tr><td>Holds</td><td>events, measures</td><td>descriptions</td></tr>
<tr><td>Example</td><td>order, qty, amount</td><td>product name, category</td></tr>
<tr><td>Size</td><td>huge, ever growing</td><td>small, changes slowly</td></tr>
<tr><td>Answers</td><td>how much?</td><td>by what?</td></tr></table>
<p><b>Four steps to design one:</b> pick the business process, declare the grain, choose the dimensions, and identify the facts.</p>
<p><b>Which measures can you add up?</b></p>
<table><tr><th>Kind</th><th>Example</th><th>Sum across</th></tr>
<tr><td>Additive</td><td>revenue</td><td>everything</td></tr>
<tr><td>Semi-additive</td><td>account balance</td><td>accounts, but not time</td></tr>
<tr><td>Non-additive</td><td>percentages, ratios</td><td>nothing: recompute</td></tr></table>
<p>Daily balances 100, 120, 90 don't total 310 of anything. The closing balance is 90.</p>
<p><b>Date dimensions</b> make "weekends" or "fiscal quarter" a simple filter. <b>Unknown members</b> (key −1) mean a fact with a missing dimension isn't dropped by an inner join.</p>
<p><b>Many-to-many</b> needs a bridge table, and care. An order tagged both "sale" and "gift" gets counted under each. Per-tag totals are valid, but they sum to 250, and the true revenue's 150.</p>
<p><b>Wide table or star?</b> Modern column stores compress repeats well, so a wide denormalised table is often fine for simple cases. Before compression, 10M rows with a 30-byte attribute cost 300 MB wide, against about 80 MB as a star. Columnar compression narrows that gap a lot, so stars today are as much about clarity and consistent definitions as about storage.</p>
""", practice=["Star Schema Query", "Build a Date Dimension", "Additive or Not?", "Daily Snapshot From Events", "Bridge Table: Avoid Double Counting", "Unknown Dimension Member", "Wide Table or Star?", "Check Foreign Keys", "Rollup Must Reconcile"])


LESSON("Core", "Slowly changing dimensions", """
<p>A customer moves from Pune to Delhi in February. Should January's sales now show Delhi? Usually not. This is the <b>slowly changing dimension</b> problem, and it's one of the most asked data engineering questions.</p>
<table><tr><th>Type</th><th>What it does</th><th>Use when</th></tr>
<tr><td><b>SCD 1</b></td><td>overwrite the old value</td><td>history doesn't matter, like fixing a typo</td></tr>
<tr><td><b>SCD 2</b></td><td>keep every version, with dates</td><td>history matters</td></tr>
<tr><td>SCD 3</td><td>a column for the previous value</td><td>only the last change matters</td></tr></table>
<p><b>SCD 2 by hand:</b></p>
<table><tr><th>key</th><th>id</th><th>city</th><th>valid_from</th><th>valid_to</th></tr>
<tr><td>1</td><td>100</td><td>Pune</td><td>2026-01-01</td><td><b>2026-02-01</b></td></tr>
<tr><td>2</td><td>100</td><td>Delhi</td><td>2026-02-01</td><td>9999-12-31</td></tr></table>
<p>The update closes the old row and opens a new one. If the value hasn't changed, do nothing, which is what makes reruns safe.</p>
<p><b>Point-in-time join:</b> find the version active when the event happened.</p>
<pre><code class="py">JOIN dim_customer d ON d.customer_id = f.customer_id
 AND f.day >= d.valid_from AND f.day < d.valid_to</code></pre>
<p>An order on 10 January gets Pune, and one on 10 February gets Delhi. Using half-open ranges (&gt;= start, &lt; end) means each moment matches exactly one row.</p>
<p><b>Check integrity:</b> for each key, ranges should have no overlaps (they'd duplicate facts in joins) and no gaps (they'd drop facts), with exactly one current row.</p>
<p>The same point-in-time idea protects machine learning from leaking the future into training data.</p>
""", practice=["SCD Type 1: Overwrite", "SCD Type 2: Keep History", "Check SCD 2 Integrity", "Point-in-Time Join", "Late-Arriving Fact"])
