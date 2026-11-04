# 6일차(선택): astronomer-cosmos 로 dbt 모델 하나하나를 Airflow 태스크로 펼치기
# 준비: Dockerfile 의 Airflow 쪽 파이썬에  pip install astronomer-cosmos  추가 → 이 파일을 dags/ 로 복사
import pendulum
from airflow.sdk import dag
from cosmos import DbtTaskGroup, ProjectConfig, ProfileConfig, ExecutionConfig, RenderConfig
from cosmos.constants import LoadMode

DBT = "/opt/dbt_venv/bin/dbt"
SHOP = "/opt/airflow/shop"

profile_config = ProfileConfig(
    profile_name="shop",                                   # profiles.yml 맨 윗줄 이름
    target_name="prod",                                    # 어느 target 으로 돌릴지
    profiles_yml_filepath="/opt/airflow/dbt/profiles.yml", # 이미 있는 profiles.yml 을 그대로 쓴다
)


@dag(
    dag_id="dbt_shop_cosmos",
    schedule=None,
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    catchup=False,
    max_active_runs=1,
    max_active_tasks=1,          # DuckDB 는 동시에 한 프로세스만 쓸 수 있으니 태스크도 한 번에 하나씩
    tags=["day6", "dbt", "cosmos"],
)
def dbt_shop_cosmos():
    DbtTaskGroup(
        group_id="shop",
        project_config=ProjectConfig(SHOP),                # dbt 프로젝트 폴더
        profile_config=profile_config,
        execution_config=ExecutionConfig(dbt_executable_path=DBT),  # 별도 venv 의 dbt 를 쓰게
        render_config=RenderConfig(load_method=LoadMode.DBT_LS),    # 파싱 때 dbt ls 로 모델 목록을 읽는다
    )


dbt_shop_cosmos()
