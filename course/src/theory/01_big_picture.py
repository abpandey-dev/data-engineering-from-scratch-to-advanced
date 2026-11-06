from lib import *

THEORY("Key terms", """
<table><tr><th>Term</th><th>Plain meaning</th></tr>
<tr><td>Pipeline</td><td>a series of steps moving data from source to destination</td></tr>
<tr><td>ETL / ELT</td><td>transform before loading / load raw, then transform</td></tr>
<tr><td>Data lake</td><td>cheap file storage holding raw data of any shape</td></tr>
<tr><td>Data warehouse</td><td>a database built for analytics on clean tables</td></tr>
<tr><td>Schema</td><td>the columns and types data should have</td></tr>
<tr><td>SLA</td><td>a promise, such as "ready by 8 am"</td></tr>
<tr><td>Partition</td><td>a piece of a table, often one day</td></tr>
<tr><td>Lineage</td><td>which data was built from which</td></tr></table>
""")
FAQ("What does a data engineer do?", "<p>Builds and runs reliable systems that collect, store, clean and serve data, so that analysts, scientists and applications can use it.</p>")
FAQ("ETL vs ELT?", "<p>ETL transforms before loading. ELT loads raw data first and transforms inside the warehouse. ELT keeps raw data so you can rebuild after a bug, and it's common now that warehouse compute is cheap and scalable.</p>")
FAQ("OLTP vs OLAP?", "<p>OLTP serves an application with many small reads and writes, usually stored by row. OLAP serves analytics with large scans, usually stored by column.</p>")
FAQ("Data lake vs data warehouse?", "<p>A lake stores raw files of any type cheaply, and structure is applied on read. A warehouse stores structured tables with fast SQL. A lakehouse combines them, adding table features on top of lake files.</p>")
FAQ("Batch vs streaming: how do you choose?", "<p>Start from how fast a decision needs the data. Use streaming only if the business needs seconds, since it costs more and is harder to run.</p>")
FAQ("Why not run reports on the production database?", "<p>Big scans can slow the application for real users, and row-oriented storage is inefficient for analytics.</p>")
FAQ("Scenario: the dashboard shows yesterday's revenue is zero. What do you do first?", "<p>Check whether the pipeline ran, then whether the source sent data, then row counts at each layer. Tell users you're looking into it. Don't jump straight to changing code.</p>")
FAQ("Scenario: a source team adds a new column without telling you. What should happen?", "<p>Ideally a schema check notices it and alerts you, without failing if it's harmless. Removing or renaming a column is more serious, and it should stop the load or be handled by an agreed contract.</p>")
FAQ("Scenario: your manager asks for 'real-time' data. How do you respond?", "<p>Ask how quickly someone acts on it and what the decision is. Many 'real-time' requests turn out to be fine with data every 15 minutes, which is far cheaper to run.</p>")
