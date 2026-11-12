# Day 24. 오케스트레이션과 운영

## 오늘의 한 줄

오케스트레이션은 작업을 순서대로 돌리는 일이 아니라 **"아침 7시에 숫자가 맞게 보인다"는 약속(SLA)을 지키는 운영 설계**입니다. 의존성은 데이터 기준으로, 재시도는 멱등한 작업에만, 실패는 영향 범위와 함께 알리고, 복구는 "실패한 곳부터 하류까지"로 정해 둡니다.

## 왜 중요한가

출고 팩트 적재가 새벽 4시에 실패했는데 영업 마트와 Power BI 갱신은 시간 기반 스케줄이라 그대로 돌았습니다. 정 과장은 7시에 어제 출고가 빠진 대시보드를 경영회의에 띄웠고, 담당자는 9시에 출근해서야 실패 메일을 봤습니다. 다시 돌리려니 어느 작업부터 다시 해야 하는지, 이미 돈 마트를 다시 돌려도 되는지 아무도 모릅니다. **의존성, 알림, 복구 범위**가 설계되지 않은 운영의 전형입니다.

## 핵심 개념

### 1. 의존성은 시간이 아니라 데이터로

"STG는 1시, 팩트는 3시"처럼 시간으로 순서를 맞추면 앞 작업이 늦거나 실패해도 뒤 작업이 돕니다. 의존성은 **"이 작업이 읽는 데이터를 만드는 작업이 같은 업무기준일로 성공했는가"** 로 겁니다. 계열사 원천처럼 오케스트레이터 밖에 있는 선행 조건(ERP 일 마감)은 센서(sensor)로 마감 신호를 기다립니다. 정확한 용어로 작업 간 의존 그래프를 DAG(방향 비순환 그래프)라고 합니다.

### 2. SLA와 배치 시간대

SLA(Service Level Agreement)는 "업무기준일 D의 데이터가 D+1일 몇 시까지 BI에 반영된다"는 현업과의 약속입니다. 시간대 설계는 이 약속에서 **거꾸로** 계산합니다. BI 갱신 완료 시각에서 각 단계 소요 시간과 재시도 여유를 빼면, 원천 추출을 언제 시작해야 하는지와 원천 마감이 언제까지 끝나야 하는지가 나옵니다. 여유가 없으면 증분 적재(Day 22), 병렬화, 마감 시각 협의 중 하나를 고릅니다.

### 3. 재시도와 멱등성

일시적 오류(네트워크, 잠금 대기)는 재시도로 대부분 해결됩니다. 단, 재시도는 **멱등한 작업에만** 안전합니다(Day 22). 데이터 오류(거부 건 급증, 대사 불일치)는 재시도해도 같은 결과이므로 재시도하지 않고 즉시 멈춰 알립니다. 그래서 작업 실패를 "재시도할 실패"와 "멈출 실패"로 나눠 설계합니다.

### 4. 백필: 과거 구간을 다시 채우기

백필(backfill)은 로직 수정·누락 발견 때 과거 업무기준일들을 다시 돌리는 일입니다. 작업이 업무기준일을 파라미터로 받고, 그 날짜의 데이터만 다시 만들 수 있어야 가능합니다. 실행 중 `SYSDATE`를 읽는 작업은 백필할 수 없습니다. 순서도 중요합니다. 날짜를 병렬로 돌려도 되는 작업(트랜잭션 팩트)과, 전날 결과에 의존해 날짜 순서대로 돌려야 하는 작업(재고 스냅샷, SCD2 차원)을 구분합니다.

### 5. 알림과 복구 시나리오

알림은 "실패했다"가 아니라 **"무엇이 실패했고, 어느 산출물이 영향받고, 누가 무엇을 하면 되는가"** 를 담아야 합니다. 복구는 실패 작업 하나가 아니라 실패 작업과 그 하류 전체를 다시 돌리는 것이 기본이고, BI 화면에는 "데이터 기준시각"을 보여 줘서 사용자가 오래된 숫자를 알아챌 수 있게 합니다.

## 예시

### 배치 시간대 (SLA에서 거꾸로 계산, 시각은 가상)

```text
 D+0 23:00  ERP close                  ERP 일 마감 (ERP 운영팀)
 D+1 00:30  wait_erp_close (sensor)    마감 신호 대기, 최대 01:30
 D+1 01:00  STG_*                      추출 (주문·출고·재고·마스터) 병렬
 D+1 02:30  DIM_*                      차원 적재 (DIM_CUST SCD2 등)
 D+1 03:00  FCT_*                      팩트 적재 병렬
 D+1 04:30  CHK_RECON                  품질 검증·대사, 실패 시 하류 중단
 D+1 05:00  DM_SALES                   영업 마트
 D+1 06:00  BI_PBI_SALES               Power BI 갱신, 여유 1시간
 D+1 07:00  SLA                        대시보드 반영 완료 (정 과장)
```

### 배치 통제 테이블

오케스트레이터(Airflow)의 실행 기록과 별도로, DW 안에 작업 정의·의존성·실행 이력을 둡니다. 도구를 바꿔도 운영 이력이 남고, SQL로 SLA·영향 범위를 바로 계산할 수 있습니다.

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

CREATE TABLE lab.batch_job (               -- 배치작업
  job_id    VARCHAR(30) PRIMARY KEY,       -- 작업ID
  job_nm    VARCHAR(50) NOT NULL,          -- 작업명
  layer_cd  VARCHAR(5)  NOT NULL,          -- STG / DIM / FCT / CHK / DM / BI
  sla_tm    TIME,                          -- 완료 기한 (D+1 기준 시각, 있는 작업만)
  retry_yn  CHAR(1)     NOT NULL DEFAULT 'Y',  -- 재시도 허용 (멱등한 작업만 Y)
  owner_nm  VARCHAR(30) NOT NULL           -- 담당
);
CREATE TABLE lab.batch_job_dep (           -- 작업의존성: 선행 작업이 같은 업무기준일로 성공해야 실행
  job_id      VARCHAR(30) NOT NULL REFERENCES lab.batch_job(job_id),
  prnt_job_id VARCHAR(30) NOT NULL REFERENCES lab.batch_job(job_id),
  PRIMARY KEY (job_id, prnt_job_id)
);
CREATE TABLE lab.batch_run (               -- 배치실행이력
  batch_id    VARCHAR(20) NOT NULL,        -- 배치ID
  job_id      VARCHAR(30) NOT NULL REFERENCES lab.batch_job(job_id),
  biz_dt      DATE        NOT NULL,        -- 업무기준일
  try_no      SMALLINT    NOT NULL,        -- 시도 차수
  run_stat_cd VARCHAR(10) NOT NULL,        -- RUNNING / SUCCESS / FAILED
  strt_dtm    TIMESTAMP   NOT NULL,
  end_dtm     TIMESTAMP,
  row_cnt     BIGINT,
  err_msg     VARCHAR(200),
  PRIMARY KEY (job_id, biz_dt, try_no)
);

INSERT INTO lab.batch_job VALUES
 ('STG_ORD',       '주문 추출',        'STG', NULL,    'Y', '나'),
 ('STG_SHIP',      '출고 추출',        'STG', NULL,    'Y', '한 대리(원천)'),
 ('STG_CUST',      '거래처 추출',      'STG', NULL,    'Y', '나'),
 ('DIM_CUST',      '거래처차원 SCD2',  'DIM', NULL,    'N', '나'),
 ('FCT_ORD_LINE',  '주문상세팩트',     'FCT', NULL,    'Y', '나'),
 ('FCT_SHIP_LINE', '출고상세팩트',     'FCT', NULL,    'Y', '나'),
 ('CHK_RECON',     '원천 대사',        'CHK', TIME '04:30', 'N', '나'),
 ('DM_SALES',      '영업 마트',        'DM',  TIME '05:30', 'Y', '나'),
 ('BI_PBI_SALES',  'Power BI 갱신',    'BI',  TIME '07:00', 'Y', '정 과장(확인)');
INSERT INTO lab.batch_job_dep VALUES
 ('DIM_CUST', 'STG_CUST'),
 ('FCT_ORD_LINE', 'STG_ORD'),  ('FCT_ORD_LINE', 'DIM_CUST'),
 ('FCT_SHIP_LINE', 'STG_SHIP'), ('FCT_SHIP_LINE', 'DIM_CUST'),
 ('CHK_RECON', 'FCT_ORD_LINE'), ('CHK_RECON', 'FCT_SHIP_LINE'),
 ('DM_SALES', 'CHK_RECON'),
 ('BI_PBI_SALES', 'DM_SALES');

-- 업무기준일 2026-04-05 실행 이력 (가상): 출고 팩트가 재시도 끝에 실패
INSERT INTO lab.batch_run VALUES
 ('B20260406', 'STG_ORD',       DATE '2026-04-05', 1, 'SUCCESS', TIMESTAMP '2026-04-06 01:00', TIMESTAMP '2026-04-06 01:20', 3, NULL),
 ('B20260406', 'STG_SHIP',      DATE '2026-04-05', 1, 'SUCCESS', TIMESTAMP '2026-04-06 01:00', TIMESTAMP '2026-04-06 01:40', 6, NULL),
 ('B20260406', 'STG_CUST',      DATE '2026-04-05', 1, 'SUCCESS', TIMESTAMP '2026-04-06 01:00', TIMESTAMP '2026-04-06 01:05', 6, NULL),
 ('B20260406', 'DIM_CUST',      DATE '2026-04-05', 1, 'SUCCESS', TIMESTAMP '2026-04-06 02:30', TIMESTAMP '2026-04-06 02:35', 1, NULL),
 ('B20260406', 'FCT_ORD_LINE',  DATE '2026-04-05', 1, 'SUCCESS', TIMESTAMP '2026-04-06 03:00', TIMESTAMP '2026-04-06 03:10', 4, NULL),
 ('B20260406', 'FCT_SHIP_LINE', DATE '2026-04-05', 1, 'FAILED',  TIMESTAMP '2026-04-06 03:00', TIMESTAMP '2026-04-06 03:30', NULL, 'lock timeout'),
 ('B20260406', 'FCT_SHIP_LINE', DATE '2026-04-05', 2, 'FAILED',  TIMESTAMP '2026-04-06 03:40', TIMESTAMP '2026-04-06 04:10', NULL, 'lock timeout'),
 ('B20260406', 'FCT_SHIP_LINE', DATE '2026-04-05', 3, 'FAILED',  TIMESTAMP '2026-04-06 04:20', TIMESTAMP '2026-04-06 04:50', NULL, 'lock timeout');
```

### 질문 1: 지금 무엇을 돌릴 수 있나

```sql
-- 업무기준일 D에 대해: 아직 성공하지 않았고, 선행 작업이 모두 성공한 작업
SELECT j.job_id
  FROM lab.batch_job j
 WHERE NOT EXISTS (SELECT 1 FROM lab.batch_run r
                    WHERE r.job_id = j.job_id AND r.biz_dt = DATE '2026-04-05' AND r.run_stat_cd = 'SUCCESS')
   AND NOT EXISTS (SELECT 1 FROM lab.batch_job_dep d
                    WHERE d.job_id = j.job_id
                      AND NOT EXISTS (SELECT 1 FROM lab.batch_run r
                                       WHERE r.job_id = d.prnt_job_id AND r.biz_dt = DATE '2026-04-05'
                                         AND r.run_stat_cd = 'SUCCESS'))
 ORDER BY j.job_id;
```

결과는 FCT_SHIP_LINE 하나입니다. CHK_RECON은 출고 팩트를 기다리므로 돌지 않고, 그 하류인 마트와 Power BI 갱신도 돌지 않습니다. 시간 기반이었다면 마트는 5시에 출고가 빠진 채 돌았을 것입니다.

### 질문 2: 실패의 영향 범위와 SLA

```sql
-- 실패 작업의 하류 전체 (재귀) + 각 작업의 SLA
WITH RECURSIVE dn AS (
  SELECT 'FCT_SHIP_LINE'::VARCHAR(30) AS job_id, 0 AS lvl
  UNION ALL
  SELECT d.job_id, dn.lvl + 1
    FROM lab.batch_job_dep d JOIN dn ON d.prnt_job_id = dn.job_id
)
SELECT dn.job_id, MIN(dn.lvl) AS lvl, j.sla_tm, j.owner_nm,
       CASE WHEN j.sla_tm IS NOT NULL AND DATE '2026-04-06' + j.sla_tm < TIMESTAMP '2026-04-06 05:00'
            THEN 'SLA 위반' WHEN j.sla_tm IS NOT NULL THEN 'SLA 위험' END AS sla_stat
  FROM dn JOIN lab.batch_job j ON j.job_id = dn.job_id
 GROUP BY dn.job_id, j.sla_tm, j.owner_nm
 ORDER BY lvl;
```

| job_id | lvl | sla_tm | sla_stat (05:00 현재) |
|---|---|---|---|
| FCT_SHIP_LINE | 0 | | |
| CHK_RECON | 1 | 04:30 | SLA 위반 |
| DM_SALES | 2 | 05:30 | SLA 위험 |
| BI_PBI_SALES | 3 | 07:00 | SLA 위험 |

이 결과가 그대로 알림 본문이 됩니다. "출고상세팩트 3회 실패(lock timeout). 영향: 원천 대사·영업 마트·Power BI 영업 대시보드. 07:00 SLA 위험. 조치: 잠금 세션 확인(ERP 운영팀), 해소 후 FCT_SHIP_LINE부터 재실행."

### 복구 시나리오

| 상황 | 판단 | 조치 |
|---|---|---|
| 일시 오류, SLA 전 해소 | 재시도 허용 작업 | 원인 해소 후 실패 작업부터 하류 전체 재실행 (멱등하므로 안전) |
| SLA까지 해소 불가 | 부분 데이터를 보일지 현업과 사전 합의한 규칙대로 | 합의안 A: 전일 데이터 유지 + 대시보드에 "데이터 기준: 4/4" 표시. 합의안 B: 주문만 갱신, 출고 지표는 "지연" 표시 |
| 데이터 오류 (대사 불일치) | 재시도 금지 | 하류 중단, 원인 분석, 원천 수정 후 해당 업무기준일 재실행 |
| 로직 버그 발견 (과거 N일 영향) | 백필 | 수정 배포 → 영향 기간을 날짜 파라미터로 재실행, 순서 의존 작업은 날짜 오름차순 |

### Airflow DAG 스케치

실행되지 않는 설계 스케치입니다. import 경로와 일부 인자는 Airflow 버전에 따라 다를 수 있으니 사용하는 버전의 문서로 확인합니다.

```python
import pendulum
from datetime import timedelta
from airflow import DAG
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator
from airflow.providers.common.sql.sensors.sql import SqlSensor

def notify_failure(context):
    # 배치 통제 테이블에서 영향 범위·SLA를 조회해 메신저/메일로 보냄 (구현 생략)
    ...

# 업무기준일: 논리 날짜가 "업무일"인지 "실행일"인지는 버전·timetable 설정에 따라 다르므로
# 한 곳에서만 정의하고 모든 SQL에 이 값을 넘긴다
BIZ_DT = "{{ ds }}"   # Airflow 3 기본(CronTriggerTimetable)이면 ds 가 실행일이라 "{{ macros.ds_add(ds, -1) }}"

default_args = {
    "owner": "group-dw",
    "retries": 2,                          # 멱등한 작업만. 비멱등 작업은 개별로 retries=0
    "retry_delay": timedelta(minutes=10),
    "on_failure_callback": notify_failure,
}

with DAG(
    dag_id="hb_dw_sales_daily",
    start_date=pendulum.datetime(2026, 4, 1, tz="Asia/Seoul"),
    schedule="30 0 * * *",                 # 매일 00:30 (KST)
    catchup=False,                         # 백필은 명시적으로만
    max_active_runs=1,                     # 같은 DAG의 날짜끼리 겹치지 않게
    default_args=default_args,
) as dag:
    wait_erp_close = SqlSensor(
        task_id="wait_erp_close",
        conn_id="hbp_erp",
        sql=f"SELECT COUNT(*) FROM erp_close_log WHERE close_dt = DATE '{BIZ_DT}'",
        mode="reschedule", poke_interval=300, timeout=60 * 60,
    )
    stg_ord  = SQLExecuteQueryOperator(task_id="stg_ord",  conn_id="group_dw", sql=f"CALL stg.sp_ord('{BIZ_DT}')")
    stg_ship = SQLExecuteQueryOperator(task_id="stg_ship", conn_id="group_dw", sql=f"CALL stg.sp_ship('{BIZ_DT}')")
    stg_cust = SQLExecuteQueryOperator(task_id="stg_cust", conn_id="group_dw", sql=f"CALL stg.sp_cust('{BIZ_DT}')")
    # SCD2 는 버전 생성이 순서에 의존 → 자동 재시도 대신 원인 확인 후 수동 재실행(백필도 날짜 오름차순으로 한 번씩)
    dim_cust = SQLExecuteQueryOperator(task_id="dim_cust", conn_id="group_dw", retries=0,
                                       sql=f"CALL dw.sp_dim_cust('{BIZ_DT}')")
    fct_ord  = SQLExecuteQueryOperator(task_id="fct_ord_line",  conn_id="group_dw", sql=f"CALL dw.sp_fct_ord('{BIZ_DT}')")
    fct_ship = SQLExecuteQueryOperator(task_id="fct_ship_line", conn_id="group_dw", sql=f"CALL dw.sp_fct_ship('{BIZ_DT}')")
    chk      = SQLExecuteQueryOperator(task_id="chk_recon", conn_id="group_dw", retries=0,
                                       sql=f"CALL dw.sp_chk_recon('{BIZ_DT}')")   # 불일치면 예외 → 하류 중단
    dm_sales = SQLExecuteQueryOperator(task_id="dm_sales", conn_id="group_dw", sql=f"CALL dm.sp_sales('{BIZ_DT}')")

    wait_erp_close >> [stg_ord, stg_ship, stg_cust]
    stg_cust >> dim_cust
    [stg_ord, dim_cust] >> fct_ord
    [stg_ship, dim_cust] >> fct_ship
    [fct_ord, fct_ship] >> chk >> dm_sales
```

Power BI 갱신을 시간 예약만으로 걸면 위 의존성이 끊깁니다. 가능하면 마트 완료 후 API로 호출하고, 어렵다면 예약을 SLA 여유 안에 두고 대시보드에 "데이터 기준시각"을 보여 줍니다.

## Before / After

| 항목 | Before | After |
|---|---|---|
| 순서 | 시각으로 맞춤 (1시, 3시, 5시) | 같은 업무기준일의 선행 성공을 조건으로 |
| 재시도 | 전 작업 일괄 3회 | 멱등한 작업만, 데이터 오류는 재시도 없이 중단 |
| 알림 | "Task failed" 메일 | 실패 작업 + 하류 영향 + SLA 상태 + 조치·담당 |
| 날짜 | 작업 안에서 SYSDATE | 업무기준일 파라미터, 백필 가능 |
| 이력 | 도구 로그에만 | DW 배치 통제 테이블 (도구 교체에도 유지, SQL로 분석) |
| 사용자 | 오래된 숫자인지 모름 | 대시보드에 데이터 기준시각 표시 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| DAG 크기 | 같은 SLA·같은 업무기준일로 묶이는 작업은 한 DAG | SLA·주기·담당이 다르면 DAG를 나누고 데이터 완료 신호(센서·통제 테이블)로 연결 |
| 재시도 | 연결·잠금 같은 일시 오류 | 대사 불일치·거부 급증은 재시도 0, 즉시 중단·알림 |
| SLA 위반 임박 | 현업이 "늦어도 정확한 숫자"를 원하면 하류 중단 + 기준시각 표시 | "일부라도 최신"을 원하면 영향 없는 지표만 갱신 (사전 합의 필수) |
| 백필 | 트랜잭션 팩트는 날짜 병렬 | 스냅샷·SCD2는 날짜 오름차순 순차 |
| 원천 의존 | 원천 마감 신호가 있으면 센서로 대기 | 신호가 없으면 마감 테이블·건수 안정화 확인을 ERP 운영팀과 정의 |

SLA 시각은 기술팀이 정하지 않습니다. 정 과장에게 "몇 시까지 어제 숫자가 보여야 합니까, 그 시각에 안 되면 전날 숫자와 일부 최신 숫자 중 무엇이 낫습니까?"를 물어 합의하고, 그 답이 복구 시나리오 표의 "합의안"이 됩니다.

## 흔한 실수 3가지

1. **시간으로 의존성을 맞추는 실수.** 앞 작업이 늦는 날 뒤 작업이 반쪽 데이터로 돌고, 그 결과가 정상처럼 보입니다. 데이터 기준 의존성으로 바꿉니다.
2. **모든 작업에 같은 재시도를 거는 실수.** 비멱등 작업이 재시도되면 중복이 생기고, 데이터 오류는 재시도로 시간만 씁니다. 실패 유형별로 정책을 나눕니다.
3. **실패 작업 하나만 다시 돌리는 실수.** 이미 돈 하류(마트, BI)는 옛 데이터로 남습니다. 복구는 실패 작업부터 하류 전체가 기본입니다.

## 셀프 체크 질문

**Q1. 영업 대시보드 SLA가 오전 7시입니다. 배치 시간대를 어떻게 설계하겠습니까?**

:::answer 모범 답안 보기
7시에서 거꾸로 계산합니다. Power BI 갱신 소요, 마트, 품질 검증, 팩트, 차원, 추출의 소요 시간을 실측하고 각 단계에 재시도 한 번 분량의 여유를 둡니다. 그러면 추출 시작 시각과 "ERP 마감이 늦어도 몇 시까지 끝나야 하는지"가 나옵니다. 마감 시각이 맞지 않으면 증분 적재로 소요를 줄이거나, 병렬화하거나, ERP 운영팀과 마감 시각을 협의합니다. 원천 마감은 센서로 기다리되 최대 대기 시간을 두고, 넘으면 알림을 보냅니다.
:::

**Q2. 새벽에 출고 팩트가 실패했습니다. 복구 절차를 설명해 보세요.**

:::answer 모범 답안 보기
먼저 실패 유형을 봅니다. 잠금·연결 같은 일시 오류면 원인을 해소하고, 데이터 오류면 재시도하지 않고 원인을 분석합니다. 다음으로 배치 통제 테이블에서 하류 영향(대사, 영업 마트, Power BI)과 SLA 상태를 뽑아 담당자와 현업에 알립니다. 해소되면 실패 작업부터 하류 전체를 같은 업무기준일로 재실행합니다. 작업이 멱등하므로 이미 일부 들어간 데이터가 있어도 안전합니다. SLA 안에 못 끝나면 사전 합의대로 전일 데이터를 유지하고 대시보드에 기준시각을 표시합니다. 끝나면 원인과 재발 방지책을 장애 보고에 남깁니다.
:::

**Q3. 지난 2주치 주문 팩트에 로직 버그가 있었습니다. 백필을 어떻게 하겠습니까?**

:::answer 모범 답안 보기
수정한 로직을 배포한 뒤 영향 기간의 업무기준일을 파라미터로 하나씩 재실행합니다. 주문 팩트는 날짜끼리 독립인 트랜잭션 팩트라 병렬로 돌려도 되지만, 하류의 스냅샷이나 누적 지표가 있으면 날짜 오름차순으로 돌립니다. 하류 마트도 같은 기간을 다시 만들고, 백필 전후 금액 차이를 대사 리포트로 남겨 현업에 "어느 기간 숫자가 얼마 바뀌는지"를 미리 공지합니다. 운영 배치와 겹치지 않게 시간대를 분리합니다.
:::

## 오늘의 과제

**과제 1.** 출고 팩트의 4번째 시도가 05:20에 성공했다고 기록하고, 그 시점에 실행 가능한 작업을 다시 조회하세요. 결과 모양은 `job_id` 1행(CHK_RECON)입니다.

:::answer 해설 보기
실행 이력은 덮어쓰지 않고 시도 차수를 늘려 추가합니다. 실패 기록이 남아야 장애 보고와 재시도 정책 검토가 가능합니다.

```sql
INSERT INTO lab.batch_run VALUES
 ('B20260406', 'FCT_SHIP_LINE', DATE '2026-04-05', 4, 'SUCCESS',
  TIMESTAMP '2026-04-06 05:00', TIMESTAMP '2026-04-06 05:20', 6, NULL);

SELECT j.job_id
  FROM lab.batch_job j
 WHERE NOT EXISTS (SELECT 1 FROM lab.batch_run r
                    WHERE r.job_id = j.job_id AND r.biz_dt = DATE '2026-04-05' AND r.run_stat_cd = 'SUCCESS')
   AND NOT EXISTS (SELECT 1 FROM lab.batch_job_dep d
                    WHERE d.job_id = j.job_id
                      AND NOT EXISTS (SELECT 1 FROM lab.batch_run r
                                       WHERE r.job_id = d.prnt_job_id AND r.biz_dt = DATE '2026-04-05'
                                         AND r.run_stat_cd = 'SUCCESS'))
 ORDER BY j.job_id;
```

CHK_RECON의 SLA(04:30)는 이미 지났으므로, 이 작업이 끝나면 05:30 마트 SLA에 맞출 수 있는지 다시 판단합니다.
:::

**과제 2.** 백필 대상 목록을 만드세요. 2026-04-01 ~ 2026-04-05 중 FCT_ORD_LINE이 성공 기록이 없는 업무기준일을 날짜 오름차순으로 보여 줍니다. 결과 모양은 `biz_dt` 4행(04-01 ~ 04-04)입니다.

:::answer 해설 보기
달력(generate_series)을 기준으로 성공 이력을 LEFT JOIN 하거나 NOT EXISTS로 거르면 "실행조차 안 된 날"까지 잡힙니다. 실행 이력만 보면 아예 안 돈 날은 보이지 않습니다.

```sql
SELECT g.biz_dt::DATE AS biz_dt
  FROM generate_series(DATE '2026-04-01', DATE '2026-04-05', INTERVAL '1 day') AS g (biz_dt)
 WHERE NOT EXISTS (SELECT 1 FROM lab.batch_run r
                    WHERE r.job_id = 'FCT_ORD_LINE' AND r.biz_dt = g.biz_dt::DATE
                      AND r.run_stat_cd = 'SUCCESS')
 ORDER BY 1;
```

샘플 이력에는 4월 5일만 있어 1~4일이 나옵니다. 이 목록이 백필 명령의 날짜 범위가 됩니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 배치 설계서 | 작업 목록, 의존성 그래프(DAG), 배치 시간대, 업무기준일 정의, 재시도 정책(작업별) |
| 운영 SLA 합의서 | 산출물별 반영 기한, 미달 시 표시 방식(전일 유지/부분 갱신), 합의자 |
| 장애 대응 매뉴얼 | 실패 유형별 판단 기준, 복구 절차(실패 작업부터 하류 전체), 연락 체계 |
| 백필 절차서 | 파라미터, 병렬/순차 구분, 사전 공지 양식, 전후 대사 |
| 테이블정의서 | BATCH_JOB, BATCH_JOB_DEP, BATCH_RUN 구조 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 19 "ETL Subsystems and Techniques"(작업 스케줄러, 의존성, 복구와 재시작, 오류 처리 하위 시스템).
- Apache Airflow 공식 문서 — DAG, Task 재시도, Sensor, Backfill, 템플릿 변수(사용 버전 기준으로 확인).
