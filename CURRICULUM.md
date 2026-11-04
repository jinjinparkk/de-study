# 커리큘럼 설계 (작성 규칙 포함)

학습자: 프로시저(BigQuery SQL)로 마트를 만들어 온 analytics engineer. SQL은 능숙, Python은 초보.
목표: dbt를 제대로 익히고(메인), Airflow·Spark 개념과 기본 실습. 이론 비중이 높아야 함.
환경: Windows 11, PowerShell, Python 3.12, Docker Desktop 있음. 포트 8000·8001·8081 사용 중 → Airflow는 8083, dbt docs는 8085.

## 7일 구성

| 일차 | 도구 | 주제 | 실습 결과물 |
|---|---|---|---|
| 1 | dbt | 큰 그림: ELT, 프로시저 → dbt, 프로젝트 구조, compile | `shop` 프로젝트, stg_orders·stg_payments·daily_sales (read_csv 직접) |
| 2 | dbt | source·ref·DAG, 계층(staging/intermediate/marts), 이름 규칙, materialization(view/table/ephemeral), 선택자 기초(`+model`) | sources.yml(external_location), stg_customers/orders/payments, int_order_payments, fct_orders, dim_customers, dbt_project.yml 폴더별 설정 |
| 3 | dbt | 테스트(generic 4종·singular·severity·store_failures), source freshness, docs·리니지, model contract, `dbt build` | schema.yml, tests/ 2개, freshness 경고 체험, docs serve --port 8085, fct_orders contract |
| 4 | dbt | Jinja(set/for/if), 매크로, 패키지(dbt_utils), incremental(MERGE 프로시저 대응), snapshot(SCD2), `--full-refresh` | 결제수단 pivot 매크로, fct_orders incremental, customers snapshot. data/next/ 파일로 바꿔 끼워 재실행 |
| 5 | Airflow | 왜 오케스트레이터, DAG·Task·Operator, 스케줄러·워커·메타DB, logical date·data interval, catchup·백필, 멱등성, XCom, TaskFlow API | Docker로 Airflow 3 standalone(8083), 첫 DAG(3 태스크), 날짜별 파일을 멱등하게 쓰는 DAG, 백필 |
| 6 | Airflow+dbt | 운영 패턴: 재시도·타임아웃·알림, BashOperator로 dbt, 계층별 태스크 분리, Cosmos(개념+선택 실습), Asset(데이터 기반 스케줄), dbt 선택자·state:modified·CI 개념, 환경(dev/prod target) | Airflow 컨테이너 안에서 dbt build 하는 DAG, 수집 DAG → Asset → dbt DAG |
| 7 | Spark | 왜 분산, 드라이버·익스큐터, DataFrame·지연 실행(변환/액션), 파티션·셔플·조인 전략, Spark SQL, explain, 언제 Spark vs 웨어하우스(dbt), 7일 정리와 다음 로드맵 | Docker pyspark-notebook, 같은 shop 데이터로 집계, explain·Spark UI(4040), parquet 파티션 쓰기 → DuckDB/dbt 에서 읽기 |

## 실습 데이터 (practice/data)

- `raw_customers.csv` (15행): customer_id, name, email, city, membership(basic/silver/gold), updated_at
- `raw_orders.csv` (30행, 2026-10-01~10-19): order_id, customer_id, order_date, status, updated_at
  - 지저분한 값: order 7 = `COMPLETED`(대문자), order 12 = ` shipped`(앞 공백) → staging에서 lower(trim())
  - status 값: placed, shipped, completed, returned
- `raw_payments.csv` (32행): payment_id, order_id, method(card/bank_transfer/kakaopay/point), amount(원)
  - order 5, 18 은 분할 결제(card + point 10000)
- `next/` = 4일차용 "다음 날" 파일
  - `next/raw_orders.csv` (40행): 26~30번 → completed(updated_at 2026-10-21 10:00), 3번 → returned(10-21 11:30), 31~40 신규(10-21~10-24)
  - `next/raw_payments.csv` (42행): 신규 주문 결제 추가
  - `next/raw_customers.csv` (16행): 2번 고객 membership → gold, 5번 고객 city 변경(둘 다 updated_at 10-21), 16번 신규

학습자의 dbt 프로젝트: `$HOME\dbt-practice\shop`, CSV는 `shop\data\`, DuckDB 파일 `shop.duckdb`, 프로필 이름 `shop`, 스키마 `main`.
2일차부터 sources.yml:

```yaml
sources:
  - name: shop_raw
    meta:
      external_location: "read_csv('data/{name}.csv', header = true)"
    tables:
      - name: raw_customers
      - name: raw_orders
      - name: raw_payments
```

## 페이지 작성 규칙

- 파일: `days/dayN.html`. `days/day1.html`의 구조·클래스를 그대로 따른다(head, `body data-page="dayN"`, `.layout > aside.toc + main`, 끝에 `<script src="../assets/app.js">`). 메뉴·목차·완료 버튼·이전/다음은 app.js가 자동으로 붙인다.
- 순서: eyebrow → h1 → lead → meta-line(이론/실습 시간·퀴즈 수) → "오늘 마치면 할 수 있는 것" 박스 → 이론 h2 여러 개 → 실습 h2(.lab > .step) → 자주 막히는 곳 → 정리(💡 한 줄 요약 + 스스로 설명해 보기 3문항) → 퀴즈 h2(.quiz > .q 6~8개).
- 말투: 한국어 존댓말, 쉬운 말. 새 개념마다 🧸 비유 박스(`.box.analogy`)를 적어도 하나. 핵심 문장은 `.box.summary` "💡 한 줄 요약". "면접용"이라는 표현 금지.
- 학습자는 프로시저 출신 → 개념마다 "프로시저 감각으로 옮기면"(`.box.proc`) 비교를 넣는다.
- Python 코드는 줄마다 주석으로 SQL에 빗대 설명(학습자가 Python 초보).
- 구조는 ASCII 박스 그림(`pre.diagram`)으로 보여준다.
- 실습 단계는 `.step data-id="..."` + `.step-title`. 학습자가 직접 쓰게 하고, 정답은 `details.hint` 안에 "힌트 1 → 힌트 2 → 정답 보기" 순서로 숨긴다. 설치·설정 같은 단순 단계는 바로 보여줘도 된다.
- 퀴즈: `.q data-answer="정답번호(1부터)"` + `.q-text` + `ol.q-opts > li` + `.q-explain`. 정답 번호를 골고루 섞는다. 해설은 왜 맞고 왜 틀린지까지.
- HTML 안 코드의 `<`, `>`, `&` 는 `&lt;` `&gt;` `&amp;` 로 쓴다(Jinja의 `{{ }}`, `{% %}`는 그대로 써도 된다).
- 버전: dbt Core 1.10+ 기준(generic test 인자는 `arguments:` 아래, 테스트 키는 `data_tests:`), snapshot은 YAML 설정 방식(1.9+), Airflow 3.x(`from airflow.sdk import dag, task`, `schedule=`, Asset, `airflow backfill create`). 버전 차이가 있는 부분은 박스로 짚어 준다.
- 외부 CDN·폰트·라이브러리 쓰지 않는다.
