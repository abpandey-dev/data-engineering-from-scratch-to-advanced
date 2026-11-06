"""Hands-on PySpark lab: real Spark, running locally. Every step prints its result.

    pip install pyspark
    python labs/spark_lab.py

Needs Java 17 or newer. In Google Colab, run `!pip install pyspark` first (Java is already there).
"""
import os
import shutil
import tempfile

from pyspark.sql import SparkSession, Window
from pyspark.sql import functions as F

os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
spark = (SparkSession.builder.master("local[2]").appName("de-lab")
         .config("spark.driver.bindAddress", "127.0.0.1").config("spark.driver.host", "127.0.0.1")
         .config("spark.ui.enabled", "false").config("spark.sql.shuffle.partitions", "4").getOrCreate())
spark.sparkContext.setLogLevel("ERROR")
out_dir = tempfile.mkdtemp()

# 1. A DataFrame, and lazy evaluation
orders = spark.createDataFrame(
    [(1, "Pune", "2026-01-05", 100.0), (2, "Delhi", "2026-01-05", 50.0), (3, "Pune", "2026-01-06", 25.0),
     (4, "Goa", "2026-01-06", -5.0), (5, "Delhi", "2026-01-06", 75.0), (5, "Delhi", "2026-01-06", 75.0)],
    ["id", "city", "day", "amount"])
plan = orders.filter(F.col("amount") > 0).groupBy("city").agg(F.sum("amount").alias("total"))
print("1. Nothing has run yet. Now an action runs it:")
print(sorted(map(tuple, plan.collect())))

# 2. Remove duplicates
print("2. Rows before and after dropDuplicates:", orders.count(), orders.dropDuplicates(["id"]).count())

# 3. Window: latest order per city
w = Window.partitionBy("city").orderBy(F.col("day").desc(), F.col("id").desc())
latest = orders.dropDuplicates(["id"]).withColumn("rn", F.row_number().over(w)).filter("rn = 1").select("city", "id")
print("3. Latest per city:", sorted(map(tuple, latest.collect())))

# 4. Broadcast join: read the plan
cities = spark.createDataFrame([("Pune", "West"), ("Delhi", "North"), ("Goa", "West")], ["city", "region"])
joined = orders.join(F.broadcast(cities), "city")
print("4. Physical plan:")
print("   uses BroadcastHashJoin:", "BroadcastHashJoin" in joined._jdf.queryExecution().executedPlan().toString())

# 5. Write partitioned Parquet, then see partition pruning
path = os.path.join(out_dir, "orders")
orders.write.mode("overwrite").partitionBy("day").parquet(path)
print("5. Folders written:", sorted(d for d in os.listdir(path) if d.startswith("day=")))
one_day = spark.read.parquet(path).filter(F.col("day") == "2026-01-05")
print("   rows on one day:", one_day.count())
print("   partition filter in plan:", "PartitionFilters: [isnotnull(day" in one_day._jdf.queryExecution().executedPlan().toString())

# 6. Idempotent load: overwrite one partition only
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
for _ in range(2):   # running twice must not duplicate data
    orders.filter("day = '2026-01-05'").write.mode("overwrite").partitionBy("day").parquet(path)
print("6. Rows after loading one day twice:", spark.read.parquet(path).count())

# 7. Skew: salt a hot key
skewed = spark.range(10000).withColumn("key", F.when(F.col("id") % 100 < 95, "hot").otherwise(F.concat(F.lit("k"), (F.col("id") % 20).cast("string"))))
sizes = [r["count"] for r in skewed.groupBy("key").count().orderBy(F.desc("count")).limit(1).collect()]
salted = skewed.withColumn("salted", F.concat(F.col("key"), F.lit("#"), (F.col("id") % 10).cast("string")))
biggest = salted.groupBy("salted").count().agg(F.max("count")).first()[0]
print("7. Largest group before and after salting:", sizes[0], biggest)

# 8. Repartition vs coalesce
df = spark.range(1000).repartition(8)
print("8. Partitions:", df.rdd.getNumPartitions(), "→ coalesce:", df.coalesce(2).rdd.getNumPartitions(), "→ repartition:", df.repartition(4).rdd.getNumPartitions())

spark.stop()
shutil.rmtree(out_dir, ignore_errors=True)
print("Lab finished.")
