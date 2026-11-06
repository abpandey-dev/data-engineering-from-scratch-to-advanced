from lib import *

THEORY("Other approaches", """
<table><tr><th>Approach</th><th>Idea</th><th>Fits</th></tr>
<tr><td>3NF (Inmon)</td><td>normalised central warehouse</td><td>enterprise integration</td></tr>
<tr><td>Star (Kimball)</td><td>facts and dimensions</td><td>analytics and BI</td></tr>
<tr><td>Data Vault</td><td>hubs, links, satellites; full history</td><td>many changing sources, audit needs</td></tr>
<tr><td>One big table</td><td>everything denormalised</td><td>a simple, fast single use case</td></tr></table>
""")
FAQ("What is grain?", "<p>What one row represents. Declaring it first prevents most modelling and reporting errors.</p>")
FAQ("Fact vs dimension?", "<p>Facts record events and measures. Dimensions describe them with context used for filtering and grouping.</p>")
FAQ("Star vs snowflake schema?", "<p>A star keeps dimensions denormalised, so joins are simple. A snowflake normalises dimensions into more tables, saving some space but adding joins.</p>")
FAQ("Explain SCD types 1, 2 and 3.", "<p>Type 1 overwrites. Type 2 adds a new row with validity dates, keeping full history. Type 3 keeps limited history in an extra column.</p>")
FAQ("Why use surrogate keys?", "<p>Natural keys can change or get reused. Surrogate keys are stable, and let one customer have many SCD 2 versions.</p>")
FAQ("Normalise or denormalise?", "<p>Normalise for transactional systems, where consistent updates matter. Denormalise for analytics, where read speed and simplicity matter.</p>")
FAQ("Scenario: design a model for an e-commerce store.", "<p>Start with fact_order_lines at one row per product per order, with dimensions for customer (SCD 2), product, date and store. Add a daily snapshot for inventory, as stock levels are semi-additive.</p>")
FAQ("Scenario: an analyst says numbers doubled after joining a dimension. What's wrong?", "<p>The dimension isn't unique on the join key, often an SCD 2 table joined without date conditions. Check the grain, then add the point-in-time condition.</p>")
FAQ("Scenario: a fact arrives for a customer not yet in the dimension. What do you do?", "<p>Don't drop it. Insert a placeholder dimension row, sometimes called an inferred member, or use an unknown key, and fix it up when the real record arrives.</p>")
