# 6일차: 여러 DAG 가 같이 쓰는 Asset 정의 (dags 폴더 안의 보통 파이썬 파일 = 공용 모듈)
from airflow.sdk import Asset

# "shop 의 원본 CSV 가 새로 갱신됐다" 를 뜻하는 이름표. Airflow 는 이 URI 의 파일을 직접 들여다보지 않는다.
SHOP_RAW = Asset(name="shop_raw", uri="file:///opt/airflow/shop/data")
