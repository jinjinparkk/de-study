# Day 26. BI 성능을 고려한 마트 설계

## 오늘의 한 줄

BI 마트는 "보고서 화면 하나에 테이블 하나"가 아니라 **BI 엔진이 잘 먹는 모양(스타 스키마)과 한 곳에서 정의된 지표**를 내주는 일입니다. Power BI는 차원 → 팩트 단방향 관계의 스타 스키마에서 가장 빠르고 헷갈림이 적고, 지표 정의는 DAX 여기저기가 아니라 마트 뷰와 시맨틱 모델 한 곳에 둡니다.

## 왜 중요한가

영업팀이 "엑셀처럼 한 장으로 달라"고 해서 주문·거래처·품목·사원 컬럼을 전부 펼친 와이드 테이블을 Power BI에 올렸습니다. 처음엔 편했지만 목표 대비 달성률을 붙이는 순간 목표(월 × 사원)를 어디에 붙일지 막히고, 출고일 기준 매출을 달라는 요청에 같은 테이블을 하나 더 만들고, 거래처명 하나 정정하는데 수백만 행을 다시 씁니다. 리포트마다 "매출"의 취소 포함 여부가 달라 경영회의에서 숫자가 두 개 나옵니다. **모델 모양과 지표 정의 위치**를 정하지 않은 대가입니다.

## 핵심 개념

### 1. 스타 스키마 vs 와이드(OBT) 테이블

OBT(One Big Table)는 팩트와 차원 속성을 모두 펼친 한 장의 테이블입니다. 조인이 없어 단순하고, 컬럼 저장 엔진에서는 반복 값이 잘 압축돼 의외로 빠를 때도 있습니다. 하지만 grain이 다른 팩트(목표, 재고)를 붙일 수 없고, 차원 속성 변경이 팩트 전체 재작성이 되며, 역할이 다른 날짜(주문일·출고일)마다 컬럼 묶음이 늘어납니다. 스타 스키마는 차원을 따로 두고 여러 팩트가 같은 차원을 공유하므로(Day 18 conformed), 새 팩트가 와도 모델이 커질 뿐 무너지지 않습니다.

### 2. Power BI가 스타 스키마를 선호하는 이유

Power BI의 필터는 관계를 따라 **1 쪽(차원)에서 다(*) 쪽(팩트)으로** 흐릅니다. 슬라이서에서 "서울1팀"을 고르면 사원 차원이 걸러지고, 관계를 따라 주문 팩트와 목표 팩트가 함께 걸러집니다. 그래서 두 팩트의 grain이 달라도 공통 차원만 있으면 한 화면에서 실적 vs 목표가 됩니다. 차원은 작고 팩트는 길고 좁은 모양이 VertiPaq(Import 모드의 컬럼 저장 엔진)의 압축과 DAX 계산 모두에 유리합니다. Microsoft의 Power BI 문서도 스타 스키마 설계를 권장합니다.

### 3. Import, DirectQuery, 그리고 Tableau의 추출 vs 라이브

| 방식 | 원리 | 장점 | 대가 |
|---|---|---|---|
| Power BI Import | 데이터를 모델 안으로 가져와 압축 저장 | 빠른 응답, DAX 전 기능 | 새로 고침 주기만큼 늦음, 모델 크기 관리 |
| Power BI DirectQuery | 화면 조작마다 DB에 SQL 전송 | 최신 데이터, 큰 데이터 | 응답이 DB 성능에 종속 (Day 25의 프루닝·집계가 그대로 중요) |
| Tableau 추출 | 데이터를 추출 파일(.hyper)로 가져옴 | 빠름, 원천 부하 분리 | 추출 새로 고침 일정 관리 |
| Tableau 라이브 | 조작마다 DB에 질의 | 최신 | DB 성능·동시 사용자 부하 |

일 1회 배치 DW라면 Import·추출이 기본입니다. 데이터가 하루 한 번 바뀌는데 매 클릭마다 DB를 때릴 이유가 없습니다. DirectQuery·라이브는 실시간성이 필요하거나 데이터가 너무 커서 가져올 수 없을 때 고르고, 그때는 DB 쪽 집계·파티션 설계가 BI 성능의 전부가 됩니다.

### 4. 시맨틱 레이어와 지표 표준화

시맨틱 레이어(semantic layer)는 테이블·컬럼 위에 **업무 용어와 지표 정의**를 얹은 층입니다. Power BI의 시맨틱 모델(semantic model, 예전 이름 dataset), dbt Semantic Layer 같은 도구가 이 역할을 합니다. 핵심은 "매출금액 = 취소(90) 제외 주문금액" 같은 정의를 **한 곳에서** 관리하고, 모든 리포트가 그 정의를 재사용하는 것입니다. 정의 위치는 둘로 나눕니다. 행 단위 규칙(취소 제외, 부호)은 마트 뷰 컬럼에, 집계·시간 계산(전월 대비, 달성률)은 시맨틱 모델 측정값에 둡니다. 정의서(지표 사전)에는 이름, 산식, 기준 일자(주문일/출고일), 포함·제외 조건, 오너를 적습니다.

## 예시

### BI가 읽는 뷰와 목표 테이블

Power BI는 dw 테이블을 직접 읽지 않고 BI 전용 뷰를 읽게 합니다. 뷰는 이름·지표 규칙을 고정하는 계약이자, 뒤의 테이블 구조가 바뀌어도 리포트를 지키는 완충입니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;

-- 날짜: 알 수 없음(-1) 행 제외 (Power BI 날짜 테이블은 빈틈 없는 연속 날짜여야 함)
CREATE VIEW lab.v_bi_dim_date AS
SELECT date_sk, full_dt, yr, qtr, mm, yyyymm, dd, wk_day_no, wk_day_nm, wkend_yn
  FROM dw.dim_date WHERE date_sk <> -1;

CREATE VIEW lab.v_bi_dim_cust AS
SELECT cust_sk, cust_no, cust_nm, cust_tp_nm, rgn_nm, emp_nm AS mgr_emp_nm, eff_strt_dt, eff_end_dt, curr_yn
  FROM dw.dim_cust;
CREATE VIEW lab.v_bi_dim_item AS
SELECT item_sk, item_cd, item_nm, item_tp_nm, unit_cd FROM dw.dim_item;
CREATE VIEW lab.v_bi_dim_emp AS
SELECT emp_sk, emp_no, emp_nm, dept_nm, hq_dept_nm FROM dw.dim_emp;

-- 주문상세 팩트 BI 뷰: 지표 규칙(취소 제외)과 두 번째 날짜 역할(최초 출고일)을 여기서 고정
CREATE VIEW lab.v_bi_fct_ord_line AS
SELECT f.ord_dt_sk,
       COALESCE((SELECT MIN(s.ship_dt_sk) FROM dw.fct_ship_line s
                  WHERE s.ord_no = f.ord_no AND s.ord_seq = f.ord_seq), -1) AS ship_dt_sk,   -- 미출고 = -1
       f.cust_sk, f.item_sk, f.emp_sk, f.ord_no, f.ord_seq, f.ord_stat_cd,
       CASE WHEN f.ord_stat_cd = '90' THEN 'Y' ELSE 'N' END AS cncl_yn,
       f.ord_qty, f.ord_amt,
       CASE WHEN f.ord_stat_cd = '90' THEN 0 ELSE f.ord_amt END AS sales_amt               -- 매출금액 정의
  FROM dw.fct_ord_line f;

-- 영업목표 (Day 18의 3월 목표, 가상): grain = 월 × 사원, 날짜 관계용으로 월 첫날 SK
CREATE TABLE lab.bi_sales_tgt (
  tgt_dt_sk INTEGER     NOT NULL,          -- 목표월 첫날 DATE_SK
  yyyymm    CHAR(6)     NOT NULL,
  emp_sk    INTEGER     NOT NULL,
  tgt_amt   NUMERIC(15) NOT NULL,
  PRIMARY KEY (yyyymm, emp_sk)
);
INSERT INTO lab.bi_sales_tgt
SELECT 20260301, '202603', e.emp_sk, v.tgt_amt
  FROM (VALUES ('E1001', 100000), ('E1002', 150000), ('E1003', 2000000), ('E1004', 50000)) AS v (emp_no, tgt_amt)
  JOIN dw.dim_emp e ON e.emp_no = v.emp_no;
```

```text
 V_BI_DIM_DATE 1 --* V_BI_FCT_ORD_LINE (ORD_DT_SK)    활성
 V_BI_DIM_DATE 1 ..* V_BI_FCT_ORD_LINE (SHIP_DT_SK)   비활성 (점선)
 V_BI_DIM_DATE 1 --* BI_SALES_TGT      (TGT_DT_SK)    활성
 V_BI_DIM_CUST 1 --* V_BI_FCT_ORD_LINE (CUST_SK)
 V_BI_DIM_ITEM 1 --* V_BI_FCT_ORD_LINE (ITEM_SK)
 V_BI_DIM_EMP  1 --* V_BI_FCT_ORD_LINE (EMP_SK)
 V_BI_DIM_EMP  1 --* BI_SALES_TGT      (EMP_SK)       두 팩트가 공유
 모든 관계: 1:* 단방향 (차원 -> 팩트)
```

### DAX 결과를 맞춰 볼 기준 숫자 (SQL)

Power BI에서 만든 측정값이 맞는지 확인할 기준을 SQL로 먼저 뽑습니다. 리포트 검수의 정답지입니다.

```sql
WITH act AS (
  SELECT d.yyyymm, e.emp_nm, SUM(f.sales_amt) AS sales_amt,
         COUNT(DISTINCT f.ord_no) FILTER (WHERE f.cncl_yn = 'N') AS ord_cnt
    FROM lab.v_bi_fct_ord_line f
    JOIN lab.v_bi_dim_date d ON d.date_sk = f.ord_dt_sk
    JOIN lab.v_bi_dim_emp  e ON e.emp_sk  = f.emp_sk
   GROUP BY d.yyyymm, e.emp_nm
)
SELECT a.yyyymm, a.emp_nm, a.sales_amt, a.ord_cnt, t.tgt_amt,
       ROUND(100.0 * a.sales_amt / t.tgt_amt, 1) AS achv_rt
  FROM act a
  LEFT JOIN lab.bi_sales_tgt t ON t.yyyymm = a.yyyymm
                              AND t.emp_sk = (SELECT emp_sk FROM dw.dim_emp WHERE emp_nm = a.emp_nm)
 ORDER BY a.yyyymm, a.emp_nm;
```

| yyyymm | emp_nm | sales_amt | ord_cnt | tgt_amt | achv_rt |
|---|---|---|---|---|---|
| 202603 | 김도윤 | 60,000 | 1 | 100,000 | 60.0 |
| 202603 | 박지훈 | 2,160,000 | 1 | 2,000,000 | 108.0 |
| 202603 | 이서연 | 146,000 | 2 | 150,000 | 97.3 |
| 202604 | 이서연 | 0 | 0 | | |
| 202604 | 최하은 | 45,000 | 1 | | |

3월 합계 2,366,000원, 4월 합계 45,000원이므로 4월의 전월 대비 증감률은 약 -98.1%입니다. 3월 출고일 기준 매출(최초 출고일이 3월인 라인)은 2,302,000원이고, 미출고인 SO2026030004의 64,000원은 출고일 "(공백)"으로 나옵니다. 최하은의 3월 목표 50,000원은 3월 실적이 없어 위 표에 나오지 않지만 Power BI에서는 목표 행이 보입니다(두 팩트를 공통 차원으로 각각 집계하므로).

### Power BI Desktop 실습

준비: 위 SQL로 뷰와 목표 테이블을 만든 PostgreSQL DB, Power BI Desktop. 메뉴 이름은 버전·언어 설정에 따라 조금씩 다를 수 있습니다.

1. Power BI Desktop에서 **Get Data(데이터 가져오기)** 를 열고 **PostgreSQL database** 를 고릅니다. 서버(예: `localhost`)와 데이터베이스 이름을 넣고, 데이터 연결 모드는 **Import** 를 고릅니다. 환경에 따라 PostgreSQL 드라이버 설치를 요구할 수 있습니다. 연결이 어렵다면 psql의 `\copy (SELECT * FROM lab.v_bi_fct_ord_line) TO 'fct_ord_line.csv' CSV HEADER` 로 각 뷰를 CSV로 내보내고 Get Data의 Text/CSV로 가져와도 이후 단계는 같습니다.
2. 탐색 창에서 lab 스키마의 `v_bi_dim_date`, `v_bi_dim_cust`, `v_bi_dim_item`, `v_bi_dim_emp`, `v_bi_fct_ord_line`, `bi_sales_tgt` 여섯 개를 선택하고 Load 합니다.
3. 필드 목록에서 테이블 이름을 `dim_date`, `dim_cust`, `dim_item`, `dim_emp`, `fct_ord_line`, `sales_tgt` 로 바꿉니다. 아래 DAX는 이 이름을 씁니다.
4. **Model view(모델 보기)** 로 갑니다. Power BI가 컬럼 이름으로 관계를 자동으로 만들었을 수 있으니 하나씩 확인하고, 아래 표와 다른 관계는 지웁니다.
5. **Manage relationships(관계 관리)** 에서 아래 관계를 만듭니다. 모두 카디널리티 일대다(1:*), 교차 필터 방향 **Single(단일)** 입니다. 날짜 테이블과 팩트 사이에는 관계가 두 개인데, 하나만 활성일 수 있으므로 출고일 관계는 "활성" 체크를 끕니다(모델 보기에 점선으로 보임).

| 1 쪽 (차원) | * 쪽 (팩트) | 활성 |
|---|---|---|
| dim_date[date_sk] | fct_ord_line[ord_dt_sk] | 예 |
| dim_date[date_sk] | fct_ord_line[ship_dt_sk] | 아니요 |
| dim_cust[cust_sk] | fct_ord_line[cust_sk] | 예 |
| dim_item[item_sk] | fct_ord_line[item_sk] | 예 |
| dim_emp[emp_sk] | fct_ord_line[emp_sk] | 예 |
| dim_emp[emp_sk] | sales_tgt[emp_sk] | 예 |
| dim_date[date_sk] | sales_tgt[tgt_dt_sk] | 예 |

6. `dim_date` 테이블을 선택하고 **Mark as date table(날짜 테이블로 표시)** 을 실행해 날짜 열로 `full_dt` 를 고릅니다. 관계가 정수 키(date_sk)로 맺어져 있어도 이 표시가 있어야 DATEADD 같은 시간 인텔리전스 함수가 이 테이블을 날짜 기준으로 씁니다. 날짜 열은 값이 유일하고 빈틈 없이 연속이어야 해서, 뷰에서 -1(1900-01-01) 행을 뺐습니다.
7. 사용자에게 보일 필요 없는 SK 열(`*_sk`)은 숨깁니다. 요일명(`wk_day_nm`)은 정렬 기준 열을 `wk_day_no` 로 지정하면 월~일 순으로 정렬됩니다.
8. `fct_ord_line` 테이블에서 **New measure(새 측정값)** 로 아래 측정값을 하나씩 만듭니다.

```dax
매출금액 = SUM ( fct_ord_line[sales_amt] )

주문건수 =
CALCULATE ( DISTINCTCOUNT ( fct_ord_line[ord_no] ), fct_ord_line[cncl_yn] = "N" )

전월 매출금액 =
CALCULATE ( [매출금액], DATEADD ( dim_date[full_dt], -1, MONTH ) )

전월 대비 증감률 =
DIVIDE ( [매출금액] - [전월 매출금액], [전월 매출금액] )

목표금액 = SUM ( sales_tgt[tgt_amt] )

목표 달성률 = DIVIDE ( [매출금액], [목표금액] )

출고일 기준 매출금액 =
CALCULATE ( [매출금액], USERELATIONSHIP ( fct_ord_line[ship_dt_sk], dim_date[date_sk] ) )
```

9. 보고서 화면에 행렬(Matrix)을 놓고 행 = `dim_date[yyyymm]`, `dim_emp[emp_nm]`, 값 = 위 측정값들을 넣습니다. 달성률·증감률은 서식을 백분율로 바꿉니다.
10. 위의 SQL 기준 숫자와 비교합니다. 3월 박지훈 2,160,000 / 목표 2,000,000 / 108.0%, 4월 전체 증감률 약 -98.1%, 3월 출고일 기준 매출 2,302,000원이 나오면 모델이 맞습니다. 출고일 기준에서 연월이 공백인 행(64,000원)은 미출고입니다.

목표는 월 grain이라 일 단위로 내려 보면 1일에만 값이 붙습니다. 목표 관련 측정값은 월 이상 수준에서만 쓰도록 리포트를 만들거나, 일 수준에서는 공백을 반환하도록 측정값에 조건을 둡니다. Day 18에서 본 것처럼 출고일·주문일을 역할별 날짜 테이블로 따로 두는 방법도 있습니다. 사용자가 직접 필드를 끌어 쓰는 셀프서비스 모델이면 역할별 테이블이, 측정값을 미리 만들어 주는 관리형 모델이면 비활성 관계 + USERELATIONSHIP이 단순합니다.

### 비교용 OBT 뷰

```sql
-- 같은 내용을 한 장으로 펼친 OBT: 목표(월 × 사원)는 붙일 곳이 없음
CREATE VIEW lab.v_bi_obt_ord AS
SELECT f.ord_no, f.ord_seq, d.full_dt AS ord_dt, d.yyyymm AS ord_yyyymm,
       c.cust_no, c.cust_nm, c.cust_tp_nm, c.rgn_nm, i.item_cd, i.item_nm,
       e.emp_nm, e.dept_nm, f.cncl_yn, f.ord_qty, f.sales_amt
  FROM lab.v_bi_fct_ord_line f
  JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
  JOIN dw.dim_cust c ON c.cust_sk = f.cust_sk
  JOIN dw.dim_item i ON i.item_sk = f.item_sk
  JOIN dw.dim_emp  e ON e.emp_sk  = f.emp_sk;

SELECT ord_yyyymm, SUM(sales_amt) AS sales_amt FROM lab.v_bi_obt_ord GROUP BY ord_yyyymm ORDER BY 1;
```

합계는 스타와 같습니다. 그러나 목표를 붙이려면 OBT를 사원 × 월로 다시 집계해 조인하거나 목표를 라인마다 복제해야 하고(fan-out, Day 16), 출고일 기준을 보려면 출고일 컬럼 묶음을 또 펼쳐야 합니다. OBT는 grain 하나, 질문 하나짜리 추출용으로는 좋지만 그룹 공통 모델로는 맞지 않습니다.

## Before / After

| 항목 | Before | After |
|---|---|---|
| 모델 | 화면마다 와이드 테이블 | 공통 차원 + 팩트 스타, BI 전용 뷰로 연결 |
| 관계 | 자동 감지 그대로, 양방향 | 차원 → 팩트 1:* 단방향, 날짜 두 역할은 활성 1 + 비활성 1 |
| 날짜 | 팩트의 날짜 컬럼으로 직접 | 날짜 테이블 표시, 시간 인텔리전스는 날짜 테이블 기준 |
| 매출 정의 | 리포트마다 DAX FILTER가 제각각 | 행 규칙은 뷰(sales_amt), 집계·시간 계산은 공통 측정값 |
| 목표 | 엑셀을 리포트에 따로 붙임 | 월 × 사원 목표 팩트를 같은 차원에 연결 |
| 검수 | 화면 눈으로 확인 | SQL 기준 숫자와 측정값 대조 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 스타 vs OBT | 여러 팩트·여러 리포트가 공유하는 그룹 모델이면 스타 | 단일 grain, 단일 목적 분석·데이터 추출이면 OBT도 가능 |
| Import vs DirectQuery | 일 배치, 모델이 메모리에 들어가면 Import | 실시간 요구나 초대형 데이터면 DirectQuery + DB 집계·파티션 |
| 지표 정의 위치 | 행 단위 규칙(취소 제외)은 마트 뷰 | 시간·비율 계산은 시맨틱 모델 측정값. 둘 다 지표 사전에 기록 |
| 역할 날짜 | 관리형 모델이면 비활성 관계 + USERELATIONSHIP | 셀프서비스면 역할별 날짜 테이블 |
| 양방향 필터 | 원칙적으로 쓰지 않음 | 브리지(다대다, Day 20)처럼 꼭 필요한 곳만 제한적으로, 이유를 설계서에 기록 |
| Tableau 추출 vs 라이브 | 물류 분석처럼 일 단위면 추출 | 현장 모니터링처럼 분 단위가 필요하면 라이브 + 집계 테이블 |

## 흔한 실수 3가지

1. **자동 감지 관계를 그대로 두는 실수.** 이름이 같은 컬럼끼리 엉뚱한 관계가 생기거나 양방향이 걸려 숫자가 바뀝니다. 관계는 설계서대로 직접 만듭니다.
2. **날짜 테이블에 -1(1900-01-01) 행을 그대로 넣는 실수.** 연속 날짜 조건이 깨져 날짜 테이블 표시가 안 되거나 연도 슬라이서에 1900년이 나옵니다. BI 뷰에서 빼고, -1 팩트는 공백 항목으로 보이게 합니다.
3. **같은 지표를 리포트마다 DAX로 다시 만드는 실수.** "매출"이 리포트마다 달라집니다. 공통 측정값을 시맨틱 모델에 두고, 리포트는 그 모델을 재사용합니다.

## 셀프 체크 질문

**Q1. 현업이 와이드 테이블 하나로 달라고 합니다. 어떻게 설득하거나 절충하겠습니까?**

:::answer 모범 답안 보기
현업이 원하는 것은 테이블 모양이 아니라 "필드를 쉽게 찾고 바로 쓰는 것"이라는 점에서 출발합니다. 스타 모델에서도 표시 폴더, 업무 이름, 숨김 처리로 필드 목록을 한 장처럼 보이게 할 수 있습니다. 그리고 OBT로 하면 생기는 일을 구체적으로 보여 줍니다. 목표 대비 달성률을 붙일 수 없고, 출고일 기준 매출을 위해 테이블이 하나 더 생기고, 거래처명 정정마다 전체 재적재가 필요합니다. 특정 분석이나 엑셀 내보내기용으로는 스타 위에 OBT 뷰를 따로 제공하는 절충이 좋습니다. 공통 모델은 스타, 단일 목적 추출은 OBT입니다.
:::

**Q2. Power BI 모델에서 관계를 단방향으로 두는 이유는 무엇입니까?**

:::answer 모범 답안 보기
필터 흐름을 예측 가능하게 하기 위해서입니다. 단방향이면 차원을 고르면 팩트가 걸러지는 한 방향만 있어서, 측정값 결과를 설명할 수 있습니다. 양방향을 걸면 팩트를 거쳐 다른 차원까지 필터가 번지고, 팩트가 두 개면 필터 경로가 여러 개가 되어 모호해지거나 의도치 않은 결과가 나옵니다. 계산 비용도 늘어납니다. 그래서 기본은 단방향이고, 다대다 브리지처럼 꼭 필요한 곳만 측정값 안에서 CROSSFILTER 등으로 제한적으로 씁니다.
:::

**Q3. "매출"의 정의가 리포트마다 다릅니다. 지표 표준화를 어떻게 진행하겠습니까?**

:::answer 모범 답안 보기
먼저 현재 쓰이는 매출 정의를 모아 차이를 표로 만듭니다(취소 포함 여부, 주문일/출고일 기준, 부가세, 반품). 그룹 경영지원실 같은 지표 오너와 정의를 합의해 지표 사전에 이름·산식·기준 일자·포함 제외 조건·오너를 적고, 다른 정의가 필요하면 "출고매출"처럼 이름을 달리합니다. 구현은 행 규칙을 마트 뷰 컬럼에, 시간·비율 계산을 공통 시맨틱 모델 측정값에 두고 리포트는 그 모델만 쓰게 합니다. 마지막으로 SQL 기준 숫자와 측정값을 대조하는 검수를 배포 절차에 넣습니다.
:::

## 오늘의 과제

**과제 1.** 정 과장이 품목별 "3월 출고일 기준 매출"을 Power BI 없이 SQL로 먼저 보고 싶어 합니다. BI 뷰만 사용해 품목별 출고일 기준 3월 매출을 구하세요. 결과 모양은 `item_nm, ship_basis_amt` 3행이며 합계가 2,302,000원입니다.

:::answer 해설 보기
DAX의 USERELATIONSHIP과 같은 일을 SQL에서는 날짜 차원을 출고일 키로 조인해서 합니다. 같은 차원을 다른 키로 붙이는 것이 Role-playing의 본질입니다.

```sql
SELECT i.item_nm, SUM(f.sales_amt) AS ship_basis_amt
  FROM lab.v_bi_fct_ord_line f
  JOIN lab.v_bi_dim_date d ON d.date_sk = f.ship_dt_sk
  JOIN lab.v_bi_dim_item i ON i.item_sk = f.item_sk
 WHERE d.yyyymm = '202603'
 GROUP BY i.item_nm
 ORDER BY i.item_nm;
```

한빛펜정 992,000원(SO2026030001 32,000 + SO2026030003 960,000), 한빛록스정 1,260,000원, 한빛시럽 50,000원입니다. 주문일 기준과의 차이 64,000원은 미출고인 SO2026030004 한빛펜정 20 BOX입니다.
:::

**과제 2.** 마트 검수용으로 사원별 3월 "목표 대비" 표를 SQL로 만드세요. 목표가 있는데 실적이 없는 사원도 나와야 합니다. 결과 모양은 `emp_nm, tgt_amt, sales_amt, achv_rt` 4행이고 최하은은 50,000 / 0 / 0.0입니다.

:::answer 해설 보기
목표를 기준으로 실적을 LEFT JOIN 합니다. 실적과 목표를 각각 사원 × 월로 집계한 뒤 붙여야 fan-out이 없습니다. Power BI는 공통 차원(dim_emp) 기준으로 두 팩트를 각각 집계하므로 같은 결과를 냅니다.

```sql
WITH act AS (
  SELECT f.emp_sk, SUM(f.sales_amt) AS sales_amt
    FROM lab.v_bi_fct_ord_line f
    JOIN lab.v_bi_dim_date d ON d.date_sk = f.ord_dt_sk
   WHERE d.yyyymm = '202603'
   GROUP BY f.emp_sk
)
SELECT e.emp_nm, t.tgt_amt, COALESCE(a.sales_amt, 0) AS sales_amt,
       ROUND(100.0 * COALESCE(a.sales_amt, 0) / t.tgt_amt, 1) AS achv_rt
  FROM lab.bi_sales_tgt t
  JOIN lab.v_bi_dim_emp e ON e.emp_sk = t.emp_sk
  LEFT JOIN act a ON a.emp_sk = t.emp_sk
 WHERE t.yyyymm = '202603'
 ORDER BY e.emp_nm;
```

김도윤 60.0, 박지훈 108.0, 이서연 97.3, 최하은 0.0입니다. 이 표를 Power BI 행렬과 나란히 놓고 검수합니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 마트 설계서 | BI 뷰 목록, 각 뷰의 grain·키, 뷰에 고정한 행 규칙(sales_amt 등), 제외 행(-1 날짜) |
| 시맨틱 모델 설계서 | 테이블·관계(1:*, 방향, 활성 여부), 날짜 테이블 지정, 숨김 열, 측정값 목록과 DAX |
| 지표 사전 | 지표명, 산식, 기준 일자, 포함·제외 조건, 오너, 구현 위치(뷰/측정값) |
| 리포트 검수서 | SQL 기준 숫자 vs 화면 숫자 대조표 |
| BI 연결 정의 | Import/DirectQuery·추출/라이브 선택과 근거, 새로 고침 일정(Day 24 SLA와 연동) |

## 참고할 원전

- Microsoft Learn, Power BI 문서 — "Understand star schema and the importance for Power BI", 모델 관계(relationships), 날짜 테이블 지정(Mark as date table), USERELATIONSHIP·DATEADD DAX 함수 참조.
- Tableau 공식 도움말 — 추출(Extract)과 라이브 연결.
- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 6 "Order Management"(Role-playing 날짜).
- dbt 공식 문서 — Semantic Layer.
