# 6일차: 가장 단순한 형태 — dbt build 한 번을 태스크 하나로
import pendulum
from airflow.sdk import dag
from airflow.providers.standard.operators.bash import BashOperator

DBT = "/opt/dbt_venv/bin/dbt"                    # dbt 전용 가상환경 안의 실행 파일
SHOP = "/opt/airflow/shop"                       # 내 PC 의 shop 프로젝트가 연결된 곳


@dag(
    dag_id="dbt_shop_build",
    schedule=None,
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Seoul"),
    catchup=False,
    max_active_runs=1,                           # DuckDB 파일은 동시에 한 프로세스만 쓸 수 있다
    tags=["day6", "dbt"],
)
def dbt_shop_build():
    BashOperator(
        task_id="dbt_build",
        cwd=SHOP,                                # cd /opt/airflow/shop 한 뒤 실행 (read_csv('data/...') 상대 경로 때문)
        bash_command=f"{DBT} build --target prod",
    )


dbt_shop_build()
