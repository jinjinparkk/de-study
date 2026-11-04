# 6일차: 계층별로 태스크를 나누고, 수집 DAG 의 Asset 이 갱신되면 자동으로 도는 dbt DAG
from datetime import timedelta                   # 시간 길이 (SQL 의 INTERVAL)
import pendulum
from airflow.sdk import dag, task_group
from airflow.providers.standard.operators.bash import BashOperator
from shop_assets import SHOP_RAW

DBT = "/opt/dbt_venv/bin/dbt"
SHOP = "/opt/airflow/shop"


def notify_failure(context):                     # 실패 알림 함수. 실제로는 슬랙·메일로 보낸다
    ti = context["ti"]                           # ti = 실패한 태스크 인스턴스
    print(f"[알림] {ti.dag_id}.{ti.task_id} 실패 (run_id={ti.run_id}, 시도 {ti.try_number}회)")


def dbt_step(task_id: str, args: str) -> BashOperator:
    # 같은 모양의 BashOperator 를 여러 번 만드는 도우미 (SQL 로 치면 매크로)
    return BashOperator(
        task_id=task_id,
        cwd=SHOP,
        bash_command=f"{DBT} {args} --target prod",
        pool="duckdb",                           # 슬롯 1개짜리 풀: DuckDB 에 쓰는 태스크는 한 번에 하나만
    )


@dag(
    dag_id="dbt_shop_layers",
    schedule=[SHOP_RAW],                         # 시간이 아니라 "SHOP_RAW 가 갱신되면" 실행
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Seoul"),
    catchup=False,
    max_active_runs=1,
    default_args={                               # 모든 태스크에 공통으로 들어가는 기본값
        "retries": 2,                            # 실패하면 2번 더 시도
        "retry_delay": timedelta(seconds=30),    # 시도 사이 30초 쉬기
        "execution_timeout": timedelta(minutes=20),  # 20분 넘으면 강제 실패
        "on_failure_callback": notify_failure,   # 재시도까지 다 실패했을 때 부를 함수
    },
    tags=["day6", "dbt"],
)
def dbt_shop_layers():

    @task_group(group_id="staging")              # 화면에서 접었다 폈다 하는 묶음 (실행 순서와는 무관)
    def staging():
        dbt_step("build", "build --select path:models/staging")

    snapshot = dbt_step("snapshot", "snapshot")

    @task_group(group_id="marts")
    def marts():
        dbt_step("build", "build --select path:models/intermediate path:models/marts")

    staging() >> snapshot >> marts()             # staging → snapshot → intermediate·marts


dbt_shop_layers()
