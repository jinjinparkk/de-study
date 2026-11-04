# 6일차: "수집" DAG. landing 폴더에 새 CSV 가 있으면 shop/data 로 옮기고 Asset 을 갱신한다
import glob                                      # 파일 이름 패턴으로 찾기 (LIKE '%.csv')
import os
import shutil                                    # 파일 복사
import pendulum
from airflow.sdk import dag, task
from airflow.sdk.exceptions import AirflowSkipException   # "이번엔 건너뛰기" 신호
from shop_assets import SHOP_RAW                 # 같은 dags 폴더의 shop_assets.py 에서 가져오기

LANDING = "/opt/airflow/landing"                 # 내 PC 의 practice/airflow/landing
SHOP_DATA = "/opt/airflow/shop/data"             # 내 PC 의 dbt-practice/shop/data


@dag(
    dag_id="collect_shop_raw",
    schedule=None,                               # 연습이라 수동 실행. 실제로는 매시간 등
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Seoul"),
    catchup=False,
    tags=["day6"],
)
def collect_shop_raw():

    @task(outlets=[SHOP_RAW])                    # 이 태스크가 "성공"하면 SHOP_RAW 가 갱신됐다고 기록된다
    def move_landing_files() -> list[str]:
        files = sorted(glob.glob(f"{LANDING}/raw_*.csv"))
        if not files:                            # 새 파일이 없으면 건너뛰기(skipped) → Asset 갱신도 없음
            raise AirflowSkipException("landing 에 새 파일이 없습니다")
        moved = []
        for src in files:                        # FOR 문: 파일마다
            dst = os.path.join(SHOP_DATA, os.path.basename(src))
            shutil.copyfile(src, dst)            # shop/data 의 같은 이름 파일을 덮어쓴다
            os.remove(src)                       # 옮긴 파일은 landing 에서 지운다 (다음 실행 때 또 옮기지 않게)
            moved.append(os.path.basename(src))
        print(f"옮긴 파일: {moved}")
        return moved

    move_landing_files()


collect_shop_raw()
