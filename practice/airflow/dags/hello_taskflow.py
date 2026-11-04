# 5일차 첫 DAG: 태스크 3개 (extract → transform → load)
# SQL 로 치면 "프로시저 하나를 3단계 블록으로 나누고, 단계마다 실행 기록이 남는 것"

import pendulum                                  # 날짜·시간대 라이브러리 (SQL 의 TIMESTAMP WITH TIME ZONE 담당)
from airflow.sdk import dag, task                # Airflow 3 의 DAG 작성 도구. @dag, @task 두 개만 쓴다


@dag(                                            # 아래 함수 하나 = DAG 하나 (CREATE PROCEDURE 선언부)
    dag_id="hello_taskflow",                     # 화면에 보이는 이름. 파일 이름과 달라도 되지만 맞추는 게 편하다
    schedule=None,                               # 자동 실행 없음. 버튼(Trigger)으로만 돌린다
    start_date=pendulum.datetime(2026, 10, 1, tz="Asia/Seoul"),  # 이 DAG 가 "유효해지는" 날짜
    catchup=False,                               # 지난 날짜를 몰아서 채우지 않기
    tags=["day5"],                               # 화면에서 거르기용 꼬리표
)
def hello_taskflow():                            # 이 함수 몸통은 "순서도를 그리는 코드". 데이터 처리는 안에서 안 한다

    @task                                        # 이 함수 = 태스크 하나 (프로시저 안의 블록 하나)
    def extract() -> list[dict]:
        rows = [                                 # 원래는 API·DB 에서 읽어 오는 부분. 오늘은 고정값
            {"order_id": 1, "amount": 39000},
            {"order_id": 2, "amount": 59000},
            {"order_id": 3, "amount": 19000},
        ]
        print(f"extract: {len(rows)}건 읽음")    # print 는 태스크 로그에 그대로 찍힌다
        return rows                              # return 값은 XCom 에 저장된다 (아주 작은 값만!)

    @task
    def transform(rows: list[dict]) -> int:      # 앞 태스크의 return 값을 인자로 받는다
        total = sum(r["amount"] for r in rows)   # SELECT SUM(amount) FROM rows
        print(f"transform: 합계 {total}원")
        return total

    @task
    def load(total: int) -> None:
        print(f"load: 오늘 매출 {total:,}원 을 적재했다고 칩시다")

    load(transform(extract()))                   # 함수에 함수를 넘기면 순서가 생긴다: extract >> transform >> load


hello_taskflow()                                 # 맨 아래에서 한 번 불러 줘야 Airflow 가 DAG 로 등록한다
