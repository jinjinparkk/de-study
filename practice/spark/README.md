# 7일차 Spark 실습

`shop_spark.py` 는 shop 데이터(raw_orders·raw_payments·raw_customers)를 PySpark로 읽어
dbt의 `fct_orders`·`daily_sales` 와 같은 집계를 DataFrame API와 Spark SQL로 각각 만들고,
`explain()`·파티션·셔플을 확인한 뒤 `order_date` 로 나눈 parquet 를 씁니다.

## 1. 폴더 준비 (PowerShell)

```powershell
cd $HOME\dbt-practice\shop
mkdir spark
# 이 저장소의 practice/spark/shop_spark.py 를 shop\spark\ 에 복사
curl.exe -sL https://jinjinparkk.github.io/de-study/practice/spark/shop_spark.py -o spark\shop_spark.py
```

결과적으로 아래 모양이 됩니다. 컨테이너 안에서는 `shop` 폴더가 `/home/jovyan/work` 로 보입니다.

```
shop\
├── data\raw_orders.csv, raw_payments.csv, raw_customers.csv
├── spark\shop_spark.py
└── out\fct_orders\order_date=2026-10-01\part-....parquet   ← 실행 후 생김
```

## 2. 컨테이너 띄우기

```powershell
docker run -d --name de-spark `
  -p 8888:8888 -p 4040:4040 `
  -v "${HOME}\dbt-practice\shop:/home/jovyan/work" `
  quay.io/jupyter/pyspark-notebook
docker logs de-spark   # http://127.0.0.1:8888/lab?token=... 주소 확인
```

- 이미지가 큽니다(수 GB). 처음 한 번은 내려받는 데 시간이 걸립니다.
- 8888·4040 이 이미 쓰이고 있으면 앞쪽 숫자만 바꿉니다: `-p 8890:8888 -p 4041:4040`.

## 3. 실행

```powershell
docker exec -it de-spark spark-submit /home/jovyan/work/spark/shop_spark.py
# Spark UI(http://localhost:4040)를 보고 싶으면 끝나기 전에 멈춰 두기
docker exec -it -e KEEP_UI=1 de-spark spark-submit /home/jovyan/work/spark/shop_spark.py
```

Jupyter(8888)에서 새 노트북을 열고 파일 내용을 셀별로 붙여 넣어도 됩니다.

## 4. DuckDB / dbt 에서 읽기

```sql
select order_date, count(*) as orders, sum(amount) as revenue
from read_parquet('out/fct_orders/*/*.parquet', hive_partitioning = true)
where status = 'completed'
group by order_date
order by order_date;
```

dbt 에서는 `sources.yml` 에 `external_location: "read_parquet('out/fct_orders/*/*.parquet', hive_partitioning = true)"` 인 source 를 추가합니다(7일차 페이지 참고).

## 5. 정리

```powershell
docker stop de-spark      # 멈추기 (다시 쓰려면 docker start de-spark)
docker rm -f de-spark     # 지우기
```

## 환경 변수

| 이름 | 기본값 | 뜻 |
|---|---|---|
| `DATA_DIR` | `/home/jovyan/work/data` | CSV 폴더 |
| `OUT_DIR` | `/home/jovyan/work/out` | parquet 출력 폴더 |
| `SPARK_MASTER` | `local[*]` | 클러스터 주소 |
| `KEEP_UI` | (없음) | `1` 이면 종료 전에 Enter 대기 |
