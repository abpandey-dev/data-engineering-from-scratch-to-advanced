# Hands-on labs

| Lab | What you do | Needs |
|---|---|---|
| [mini_pipeline.py](mini_pipeline.py) | A complete pipeline: dedupe, dead letters, star schema, quality checks, safe reruns | Python only |
| [spark_lab.py](spark_lab.py) | Real PySpark: lazy plans, windows, broadcast joins, partition pruning, idempotent overwrites, salting | `pip install pyspark`, Java 17+ |

The Spark lab also runs in [Google Colab](https://colab.research.google.com/github/abpandey-dev/data-engineering-from-scratch-to-advanced/blob/main/notebooks/labs/spark_lab.ipynb).

## Build these yourself

Real skill comes from building and debugging, so after the course, build these on free or synthetic data. Never use your employer's data.

1. **Batch warehouse:** public data → S3 or local Parquet → dbt star schema → tests → a dashboard, scheduled with Airflow.
2. **CDC to a lake:** PostgreSQL → Debezium → Kafka → Spark → Iceberg, with deletes handled, using Docker Compose.
3. **Streaming metrics:** a click generator → Kafka → windows and watermarks → a live chart, then kill the job and prove the totals stay correct.
4. **Data quality platform:** freshness, volume and schema monitors, with alerts and lineage.
5. **RAG ingestion:** documents → chunk → incremental embedding → vector index, with deletes and freshness monitoring.
