# 5일차: logical date 별로 파일을 "덮어써서" 멱등하게 만드는 DAG
# 프로시저로 치면:  DELETE FROM t WHERE dt = p_date;  INSERT INTO t SELECT ... WHERE order_date = p_date;
# p_date 를 사람이 넣는 대신 Airflow 가 실행마다 {{ ds }} 로 넣어 준다.

import csv                                       # CSV 읽기·쓰기 (표준 라이브러리, 설치 필요 없음)
import os                                        # 폴더 만들기·파일 이름 바꾸기
import pendulum
from airflow.sdk import dag, task, get_current_context, CronDataIntervalTimetable  # CronDataIntervalTimetable = "구간"이 있는 스케줄 (본문 참고)
from airflow.providers.standard.operators.bash import BashOperator   # 셸 명령을 돌리는 전통적인 Operator

SRC = "/opt/airflow/data/raw_orders.csv"         # 입력: 컨테이너 안 경로 (내 PC 의 practice/airflow/data)
OUT_ROOT = "/opt/airflow/output/orders"          # 출력: dt=YYYY-MM-DD 폴더를 날짜마다 하나씩


@dag(
    dag_id="daily_orders_partition",
    # 매일 00:00(UTC, 한국 09:00)에 "어제 하루" 구간을 처리한다. ds = 구간 시작 날짜 = 처리할 데이터의 날짜
    # 시간대를 UTC 로 둔 이유: ds 는 UTC 기준으로 계산된다. 서울 00:00 으로 잡으면 ds 가 하루 전 날짜로 찍힌다 (본문 참고)
    schedule=CronDataIntervalTimetable("0 0 * * *", timezone="UTC"),
    start_date=pendulum.datetime(2026, 10, 1, tz="UTC"),
    catchup=False,                               # 켜면 10-01 부터 오늘까지 전부 자동 실행된다 (백필로 따로 해 볼 것)
    max_active_runs=3,                           # 백필 때 동시에 도는 날짜 수 상한
    params={"min_amount": 0},                    # 수동 실행 때 화면에서 바꿀 수 있는 값 (SQL 의 프로시저 인자 기본값)
    tags=["day5"],
)
def daily_orders_partition():

    @task
    def show_dates(ds=None, data_interval_start=None, data_interval_end=None, logical_date=None):
        # 인자 이름을 컨텍스트 키와 똑같이 적으면 Airflow 가 값을 채워 준다
        print(f"logical_date        = {logical_date}")
        print(f"data_interval_start = {data_interval_start}")
        print(f"data_interval_end   = {data_interval_end}")
        print(f"ds                  = {ds}")

    @task
    def extract_day(ds=None) -> str:
        out_dir = f"{OUT_ROOT}/dt={ds}"          # 파티션 폴더: ... /dt=2026-10-03
        os.makedirs(out_dir, exist_ok=True)      # 있으면 그냥 두고, 없으면 만든다 (CREATE SCHEMA IF NOT EXISTS)
        tmp = f"{out_dir}/orders.csv.tmp"        # 먼저 임시 파일에 쓰고
        final = f"{out_dir}/orders.csv"          # 다 쓰면 진짜 이름으로 바꾼다 (중간에 죽어도 반쪽 파일이 안 남게)

        with open(SRC, newline="", encoding="utf-8") as f:   # FROM raw_orders
            rows = [r for r in csv.DictReader(f)             # 한 줄씩 dict 로 읽어서
                    if r["order_date"] == ds]                # WHERE order_date = ds

        with open(tmp, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=["order_id", "customer_id", "order_date", "status"],
                               extrasaction="ignore")        # SELECT 할 컬럼만 (updated_at 은 버림)
            w.writeheader()
            w.writerows(rows)
        os.replace(tmp, final)                   # 같은 날짜 파일이 있으면 통째로 교체 = DELETE + INSERT

        print(f"{ds}: {len(rows)}건 → {final}")
        return final                             # XCom 에는 "파일 경로"만 넘긴다 (데이터 자체는 X)

    @task
    def check(path: str) -> int:
        ctx = get_current_context()              # 컨텍스트 전체가 필요할 때 꺼내는 방법
        min_amount = ctx["params"]["min_amount"] # params 읽기 (지금은 출력만)
        with open(path, encoding="utf-8") as f:
            n = sum(1 for _ in f) - 1            # 헤더 한 줄 빼고 줄 수 = COUNT(*)
        print(f"검사: {path} 에 {n}건 (params.min_amount={min_amount})")
        return n

    # 전통적인 Operator 방식 태스크. bash_command 안의 {{ ds }} 는 실행 직전에 날짜로 바뀐다 (템플릿)
    list_files = BashOperator(
        task_id="list_files",
        bash_command="ls -l {{ params.out_root }}/dt={{ ds }}",
        params={"out_root": OUT_ROOT},
    )

    path = extract_day()                         # 태스크를 "부르면" 실행되는 게 아니라 순서도에 칸이 하나 생긴다
    show_dates() >> path                         # show_dates 가 끝나야 extract_day 시작
    check(path) >> list_files                    # extract_day → check → list_files


daily_orders_partition()
