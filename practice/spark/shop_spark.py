# 7일차 실습: shop 데이터를 PySpark로 집계하고 parquet로 쓰기
#
# 컨테이너(quay.io/jupyter/pyspark-notebook) 안에서 실행:
#   docker exec -it de-spark spark-submit /home/jovyan/work/spark/shop_spark.py
# 또는 노트북 셀에 이 파일 내용을 나눠 붙여 넣어도 된다.
#
# 경로는 환경 변수로 바꿀 수 있다 (기본값은 README의 docker run 마운트 기준).
#   DATA_DIR : raw_*.csv 가 있는 폴더
#   OUT_DIR  : parquet 결과를 쓸 폴더
#   KEEP_UI=1 : 끝나기 전에 Enter 를 기다린다 (그동안 http://localhost:4040 Spark UI 보기)

import os                                   # 환경 변수 읽기용 (SQL의 변수 선언 정도로 생각)
from pyspark.sql import SparkSession        # Spark에 접속하는 입구 (DB 커넥션 같은 것)
from pyspark.sql import functions as F      # lower, trim, sum, count 같은 SQL 함수 모음

DATA_DIR = os.environ.get("DATA_DIR", "/home/jovyan/work/data")
OUT_DIR = os.environ.get("OUT_DIR", "/home/jovyan/work/out")

# ---------------------------------------------------------------
# 0. SparkSession 만들기 = "DB에 접속"
# ---------------------------------------------------------------
spark = (
    SparkSession.builder
    .appName("shop_spark")                          # Spark UI에 보일 작업 이름
    .master(os.environ.get("SPARK_MASTER", "local[*]"))  # local[*] = 내 PC 코어 전부를 익스큐터처럼 사용
    .config("spark.sql.shuffle.partitions", "8")    # 셔플 후 파티션 수 (기본 200은 작은 데이터에 과함)
    .getOrCreate()
)
spark.sparkContext.setLogLevel("WARN")              # INFO 로그가 너무 많아서 줄임
print("Spark version:", spark.version)

# ---------------------------------------------------------------
# 1. CSV 읽기 = FROM read_csv(...)
# ---------------------------------------------------------------
# schema를 직접 적으면 = CREATE TABLE 의 컬럼 정의. 추론(inferSchema)보다 빠르고 안전하다.
orders_raw = spark.read.csv(
    f"{DATA_DIR}/raw_orders.csv",
    header=True,
    schema="order_id INT, customer_id INT, order_date DATE, status STRING, updated_at TIMESTAMP",
)
payments_raw = spark.read.csv(
    f"{DATA_DIR}/raw_payments.csv",
    header=True,
    schema="payment_id INT, order_id INT, method STRING, amount BIGINT",
)
customers_raw = spark.read.csv(
    f"{DATA_DIR}/raw_customers.csv",
    header=True,
    schema="customer_id INT, name STRING, email STRING, city STRING, membership STRING, updated_at TIMESTAMP",
)
# 여기까지는 아무것도 읽지 않았다(지연 실행). 아래 count()가 "액션"이라 이때 실제로 읽는다.
print("rows:", orders_raw.count(), payments_raw.count(), customers_raw.count())

# ---------------------------------------------------------------
# 2. DataFrame API로 dbt 모델 흉내 내기
# ---------------------------------------------------------------
# stg_orders: select order_id, customer_id, order_date, lower(trim(status)) as status
stg_orders = orders_raw.select(
    "order_id",
    "customer_id",
    "order_date",
    F.lower(F.trim("status")).alias("status"),
)

# stg_payments: select order_id, sum(amount) as amount from ... group by order_id
stg_payments = payments_raw.groupBy("order_id").agg(F.sum("amount").alias("amount"))

# fct_orders: stg_orders left join stg_payments using (order_id)
fct_orders = stg_orders.join(stg_payments, on="order_id", how="left")

# daily_sales: where status='completed' group by order_date → count(*), sum(amount)
daily_sales_df = (
    fct_orders
    .where(F.col("status") == "completed")          # WHERE status = 'completed'
    .groupBy("order_date")                          # GROUP BY order_date
    .agg(
        F.count("*").alias("orders"),               # count(*) as orders
        F.sum("amount").alias("revenue"),           # sum(amount) as revenue
    )
    .orderBy("order_date")                          # ORDER BY order_date
)

# ---------------------------------------------------------------
# 3. 같은 것을 Spark SQL로 (임시 뷰 = CREATE TEMP VIEW)
# ---------------------------------------------------------------
orders_raw.createOrReplaceTempView("raw_orders")
payments_raw.createOrReplaceTempView("raw_payments")

daily_sales_sql = spark.sql("""
    with stg_orders as (
        select order_id, customer_id, order_date, lower(trim(status)) as status
        from raw_orders
    ),
    stg_payments as (
        select order_id, sum(amount) as amount
        from raw_payments
        group by order_id
    )
    select o.order_date, count(*) as orders, sum(p.amount) as revenue
    from stg_orders o
    left join stg_payments p using (order_id)
    where o.status = 'completed'
    group by o.order_date
    order by o.order_date
""")

print("\n== daily_sales (DataFrame API) ==")
daily_sales_df.show()                               # show() 도 액션 → 여기서 계산이 일어난다
print("== daily_sales (Spark SQL) ==")
daily_sales_sql.show()

# 두 결과가 같은지: (A EXCEPT ALL B) 와 (B EXCEPT ALL A) 가 둘 다 0행이면 같다
diff = daily_sales_df.exceptAll(daily_sales_sql).count() + daily_sales_sql.exceptAll(daily_sales_df).count()
print("DataFrame vs SQL 차이 행 수:", diff)

# ---------------------------------------------------------------
# 4. explain() = EXPLAIN. 두 방식의 실행 계획이 같다는 것도 확인
# ---------------------------------------------------------------
print("\n== explain: DataFrame API ==")
daily_sales_df.explain()
print("== explain: Spark SQL ==")
daily_sales_sql.explain()

# 작은 테이블이라 Broadcast Hash Join 이 골라졌다. 브로드캐스트를 끄면 Sort-Merge Join 으로 바뀐다.
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", "-1")
print("== explain: 브로드캐스트를 끈 경우 ==")
stg_orders.join(stg_payments, "order_id", "left").explain()
spark.conf.set("spark.sql.autoBroadcastJoinThreshold", str(10 * 1024 * 1024))  # 원래값(10MB)으로

# ---------------------------------------------------------------
# 5. 파티션 수 보기: repartition(셔플 O) vs coalesce(셔플 X)
# ---------------------------------------------------------------
print("\nfct_orders 파티션 수:", fct_orders.rdd.getNumPartitions())
re4 = fct_orders.repartition(4, "order_date")       # order_date 해시로 4덩어리 재분배 (셔플 발생)
print("repartition(4, order_date):", re4.rdd.getNumPartitions())
co1 = re4.coalesce(1)                               # 4덩어리를 1개로 합치기만 (셔플 없음)
print("coalesce(1):", co1.rdd.getNumPartitions())

# 파티션마다 몇 행씩 들어갔나 (spark_partition_id() = 행이 들어 있는 파티션 번호)
re4.groupBy(F.spark_partition_id().alias("partition")).count().orderBy("partition").show()

# ---------------------------------------------------------------
# 6. parquet 로 쓰기: order_date 별 폴더로 나눠서 (partitionBy)
# ---------------------------------------------------------------
out_path = f"{OUT_DIR}/fct_orders"
(
    fct_orders
    .repartition("order_date")                      # 날짜별로 모아서 → 날짜 폴더마다 파일 1개 (작은 파일 줄이기)
    .write
    .mode("overwrite")                              # = CREATE OR REPLACE
    .partitionBy("order_date")                      # out/fct_orders/order_date=2026-10-01/part-....parquet
    .parquet(out_path)
)
print("written:", out_path)

# 다시 읽어서 확인 + 파티션 가지치기(PartitionFilters) 보기
back = spark.read.parquet(out_path)
print("read back rows:", back.count())
back.where(F.col("order_date") == "2026-10-05").explain()

if os.environ.get("KEEP_UI") == "1":
    input("Spark UI: http://localhost:4040  (Enter 를 누르면 종료)")

spark.stop()
