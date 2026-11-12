# Day 18. Dimension 설계

## 오늘의 한 줄

차원은 팩트를 "누가·언제·무엇을·어디서"로 자르는 칼입니다. 여러 팩트가 **같은 칼(Conformed Dimension)** 을 써야 그룹 전체 숫자를 나란히 비교할 수 있고, 그 약속을 표로 그린 것이 버스 매트릭스입니다. 날짜·Role-playing·Junk·Degenerate는 이 칼을 상황에 맞게 다듬는 기법입니다.

## 왜 중요한가

영업 마트는 거래처유형을 "병원·약국·도매상"으로, 물류 마트는 WMS 코드대로 "의료기관·소매·유통"으로 담았다고 해 보겠습니다. 경영지원실이 "거래처유형별 주문 대비 출고"를 요청하는 순간 두 마트를 붙일 방법이 없어서 엑셀로 손 매핑을 하게 됩니다. 반대로 출고 팩트에 주문일자와 출고일자가 둘 다 있는데 날짜 차원을 하나만 연결하면 Power BI에서 "주문월 기준 출고량"과 "출고월 기준 출고량"을 구분할 수 없습니다. 차원 설계는 개별 테이블이 아니라 **팩트들 사이의 약속**을 설계하는 일입니다.

## 핵심 개념

### 1. Conformed Dimension: 같은 칼을 같이 쓴다

쉽게 말하면 주문 팩트와 출고 팩트가 **같은 거래처 차원, 같은 품목 차원, 같은 날짜 차원**을 쓰는 것입니다. 같은 키, 같은 속성 이름, 같은 코드값, 같은 뜻이면 두 팩트를 각각 집계한 결과를 그 속성으로 나란히 붙일 수 있습니다. 이렇게 서로 다른 팩트를 공통 차원으로 붙여 보는 것을 drill-across라고 합니다.

공통 차원이 반드시 "완전히 같은 테이블"일 필요는 없습니다. 월 단위 목표 팩트에는 일 단위 날짜 차원 대신 **월 차원**이 붙는데, 월 차원의 속성(연도, 분기, 연월)이 날짜 차원의 속성과 이름·값이 같으면 둘은 conformed입니다. 이런 상위 수준 부분집합을 shrunken(축소) 차원이라고 부릅니다.

공통 차원은 기술보다 **거버넌스**의 문제입니다. 거래처유형 코드를 누가 정하고, 계열사 WMS 코드를 누가 매핑하는지가 정해져야 합니다(Day 13 MDM).

### 2. 버스 매트릭스: 프로세스 × 공통 차원

행은 업무 프로세스(팩트), 열은 공통 차원, 칸은 "이 팩트가 이 차원을 쓰는가"입니다. 한 장으로 세 가지를 보여 줍니다. 어떤 차원을 먼저 공통화해야 하는지(체크가 많은 열), 프로젝트 차수 범위(어느 행까지 하나), 그리고 새 팩트를 붙일 때 재사용할 차원입니다. Kimball 방식에서 "통합 설계도" 역할을 하는 산출물입니다.

### 3. 날짜 차원: 함수가 아니라 테이블로

"날짜는 DATE 컬럼에서 함수로 뽑으면 되지 않나" 싶지만, 업무 달력은 함수로 계산되지 않습니다. 공휴일, 그룹 영업일, 회계연도·회계월, 마감일, 영업 주차는 회사가 정하는 값입니다. 이것을 날짜 차원 한 곳에 두면 모든 팩트가 같은 달력을 씁니다.

공통 DW의 DIM_DATE는 DATE_SK를 YYYYMMDD 정수로 둡니다. 다른 차원은 의미 없는 일련번호 SK를 쓰는데 날짜만 예외인 이유는, 날짜는 값이 바뀌지 않고 범위가 확정적이며, 정수 날짜 키가 팩트 파티션 키로 쓰기 좋기 때문입니다. 대신 "SK에 의미를 담지 않는다"는 원칙의 예외임을 표준에 적어 둡니다.

### 4. Role-playing: 한 차원, 여러 역할

출고 팩트에는 주문일자와 출고일자가 둘 다 있습니다. 날짜 차원 테이블은 하나지만 팩트에서 **두 가지 역할**로 쓰입니다. 역할마다 뷰(또는 BI 모델에서 별칭 테이블)를 만들어 컬럼 이름에 역할을 붙입니다. 그래야 사용자가 "주문연월"과 "출고연월"을 헷갈리지 않습니다.

### 5. Junk 차원과 Degenerate 차원

**Junk 차원**은 주문상태코드, 주문상세유형(일반·증정), 긴급여부처럼 값이 몇 개 안 되는 플래그·코드를 하나로 묶은 차원입니다. 각각 차원을 만들면 팩트 FK가 늘고, 팩트에 코드 그대로 두면 이름·설명이 없습니다. 실제 나오는 조합만(또는 전체 조합을) 한 테이블에 담습니다.

**Degenerate 차원**은 주문번호처럼 **차원 테이블 없이 팩트에 남은 업무 키**입니다. 주문번호에 붙일 속성(주문일자, 거래처)은 이미 다른 차원으로 빠졌으므로 테이블이 비게 되지만, 주문 건수 세기, 원천 추적, 헤더 단위 묶기에는 꼭 필요합니다.

## 예시

### 버스 매트릭스: 한빛 그룹 DW

| 업무 프로세스 (팩트) | 날짜 | 거래처 | 품목 | 사원 | 창고 | 로트 | 구매처 | 계정 | 회사 | 차수 |
|---|---|---|---|---|---|---|---|---|---|---|
| 주문 (FCT_ORD_LINE) | O | O | O | O | | | | | O | 1차 |
| 출고 (FCT_SHIP_LINE) | O (출고·주문) | O | O | | O | O | | | O | 1차 |
| 일별재고 (FCT_INV_DAILY) | O | | O | | O | O | | | O | 1차 |
| 영업목표 (월) | O (월) | | | O | | | | | O | 1차 |
| 입고 | O | | O | | O | O | O | | O | 2차 |
| 발주 | O | | O | | | | O | | O | 2차 |
| 생산실적 | O | | O | | | O | | | O | 2차 |
| 총계정원장 | O | | | | | | | O | O | 3차 |

날짜·품목·회사 열에 체크가 가장 많으므로 1차에서 반드시 그룹 공통으로 확정해야 하는 차원입니다. 거래처는 1차의 두 팩트가 함께 쓰므로 한빛제약 ERP 코드와 한빛로지스 WMS 코드의 매핑이 1차 필수 과제가 됩니다. 공통 DW에는 회사 차원이 아직 없습니다. 1차는 회사가 고정(주문 1000, 창고 2000)이라 창고 차원의 회사 속성으로 버티지만, 계열사가 붙는 2차부터는 DIM_CO가 필요하다는 것도 이 표에서 보입니다.

### Role-playing: 주문일자와 출고일자

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

-- 같은 날짜 차원을 역할별 뷰로: 컬럼 이름에 역할을 붙임
CREATE VIEW lab.v_dim_ord_dt AS
SELECT date_sk AS ord_dt_sk, full_dt AS ord_dt, yyyymm AS ord_yyyymm, wk_day_nm AS ord_wk_day_nm
  FROM dw.dim_date;
CREATE VIEW lab.v_dim_ship_dt AS
SELECT date_sk AS ship_dt_sk, full_dt AS ship_dt, yyyymm AS ship_yyyymm, wk_day_nm AS ship_wk_day_nm
  FROM dw.dim_date;

-- 출고 라인별 주문일·출고일과 요일, 리드타임
SELECT f.ship_no, f.ship_seq, o.ord_dt, o.ord_wk_day_nm, s.ship_dt, s.ship_wk_day_nm,
       s.ship_dt - o.ord_dt AS lead_days, f.ship_qty
  FROM dw.fct_ship_line f
  JOIN lab.v_dim_ord_dt  o ON o.ord_dt_sk  = f.ord_dt_sk
  JOIN lab.v_dim_ship_dt s ON s.ship_dt_sk = f.ship_dt_sk
 ORDER BY f.ship_no, f.ship_seq;
```

6행 모두 주문 다음 날 출고(리드타임 1일)입니다. 3월 2일(월) 주문은 3월 3일(화), 3월 10일(화) 주문은 3월 11일(수)에 나갔습니다. Power BI에서는 같은 날짜 테이블과 두 관계를 만들고 하나를 비활성화하는 방법도 있지만, 사용자가 직접 끌어다 쓰는 모델이라면 역할별 테이블(뷰)을 따로 두는 쪽이 헷갈림이 적습니다(Day 26).

### Conformed 축소 차원: 월별 실적 vs 목표

영업목표는 월 × 영업사원 grain입니다. 일 단위 날짜 차원에 붙일 수 없으므로 날짜 차원에서 월 차원을 파생합니다. 목표 금액은 학습용 가상 값입니다.

```sql
-- 월 차원: 날짜 차원의 부분집합 (속성 이름·값이 같아야 conformed)
CREATE TABLE lab.dim_mm AS
SELECT DISTINCT yyyymm, yr, qtr, mm FROM dw.dim_date WHERE date_sk <> -1;

CREATE TABLE lab.fct_sales_tgt (            -- 영업목표팩트: 연월 × 사원
  yyyymm   CHAR(6)     NOT NULL,
  emp_sk   INTEGER     NOT NULL,
  tgt_amt  NUMERIC(15) NOT NULL,
  PRIMARY KEY (yyyymm, emp_sk)
);
INSERT INTO lab.fct_sales_tgt
SELECT '202603', e.emp_sk, v.tgt_amt
  FROM (VALUES ('E1001', 100000), ('E1002', 150000), ('E1003', 2000000), ('E1004', 50000)) AS v (emp_no, tgt_amt)
  JOIN dw.dim_emp e ON e.emp_no = v.emp_no;

-- drill-across: 두 팩트를 공통 차원(월, 사원)으로 각각 집계한 뒤 붙임
WITH act AS (
  SELECT d.yyyymm, f.emp_sk, SUM(f.ord_amt) AS ord_amt
    FROM dw.fct_ord_line f JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
   WHERE f.ord_stat_cd <> '90'
   GROUP BY d.yyyymm, f.emp_sk
)
SELECT m.yyyymm, e.emp_nm, t.tgt_amt, COALESCE(a.ord_amt, 0) AS ord_amt,
       ROUND(100.0 * COALESCE(a.ord_amt, 0) / t.tgt_amt, 1) AS achv_rt
  FROM lab.fct_sales_tgt t
  JOIN lab.dim_mm m   ON m.yyyymm = t.yyyymm
  JOIN dw.dim_emp e   ON e.emp_sk = t.emp_sk
  LEFT JOIN act a     ON a.yyyymm = t.yyyymm AND a.emp_sk = t.emp_sk
 ORDER BY e.emp_no;
```

3월 김도윤 60,000원(60.0%), 이서연 146,000원(97.3%), 박지훈 2,160,000원(108.0%), 최하은 0원입니다. 두 팩트의 grain(주문상세 vs 월·사원)이 달라도 **공통 차원 수준으로 각각 집계한 뒤** 붙이면 fan-out이 없습니다. 김도윤의 60,000원은 청솔내과의원 3월 2일 주문(SO2026030002)입니다. 청솔내과의원 담당은 3월 16일 이서연으로 바뀌었지만, 주문 팩트의 사원이 "주문을 받은 사원"이라 이 건은 김도윤에게 남습니다. 거래처의 현재 담당 기준으로 묶으면 이서연에게 갑니다. 이 귀속 기준은 Day 19에서 다시 따집니다.

### Junk 차원: 작은 코드들을 한 차원으로

```sql
-- 주문 Junk 차원: 주문상태 × 주문상세유형 (Day 4의 01 일반, 02 증정) 전체 조합
CREATE TABLE lab.dim_ord_junk (
  ord_junk_sk     INTEGER     PRIMARY KEY,
  ord_stat_cd     VARCHAR(2)  NOT NULL,
  ord_stat_nm     VARCHAR(10) NOT NULL,
  ord_dtl_tp_cd   VARCHAR(2)  NOT NULL,
  ord_dtl_tp_nm   VARCHAR(10) NOT NULL,
  sales_incl_yn   CHAR(1)     NOT NULL,      -- 매출실적 포함여부 (파생 규칙을 차원에 고정)
  UNIQUE (ord_stat_cd, ord_dtl_tp_cd)
);
INSERT INTO lab.dim_ord_junk
SELECT ROW_NUMBER() OVER (ORDER BY s.cd, t.cd), s.cd, s.nm, t.cd, t.nm,
       CASE WHEN s.cd <> '90' AND t.cd = '01' THEN 'Y' ELSE 'N' END
  FROM (VALUES ('10','접수'), ('20','확정'), ('30','출고완료'), ('90','취소')) AS s (cd, nm)
 CROSS JOIN (VALUES ('01','일반'), ('02','증정')) AS t (cd, nm);

-- 팩트에 붙이면: 공통 스키마 주문상세에는 유형 컬럼이 없으므로 모두 01 일반으로 매핑
SELECT j.ord_stat_nm, j.ord_dtl_tp_nm, j.sales_incl_yn,
       COUNT(*) AS line_cnt, COUNT(DISTINCT f.ord_no) AS ord_cnt, SUM(f.ord_amt) AS ord_amt
  FROM dw.fct_ord_line f
  JOIN lab.dim_ord_junk j ON j.ord_stat_cd = f.ord_stat_cd AND j.ord_dtl_tp_cd = '01'
 GROUP BY j.ord_junk_sk, j.ord_stat_nm, j.ord_dtl_tp_nm, j.sales_incl_yn
 ORDER BY j.ord_junk_sk;
```

출고완료 5라인·3건 2,302,000원, 확정 1라인 64,000원, 접수 1라인 45,000원, 취소 1라인 25,000원입니다. `COUNT(DISTINCT f.ord_no)`가 Degenerate 차원의 쓰임입니다. 주문 "건수"는 주문번호 없이는 셀 수 없습니다. Junk 차원에 "매출실적 포함여부"를 두면 취소·증정 제외 규칙이 BI 측정값마다 흩어지지 않고 한 곳에 고정됩니다.

:::note Oracle 차이
Oracle 23ai 이전에는 `FROM (VALUES ...)`를 쓸 수 없어 `SELECT '10' cd, '접수' nm FROM DUAL UNION ALL ...`로 조합을 만듭니다. `ROW_NUMBER() OVER`와 `CROSS JOIN`은 같습니다.
:::

## Before / After

**Before: 팩트마다 자기 차원, 날짜는 컬럼 하나, 코드는 팩트에 그대로**

| 문제 | 증상 |
|---|---|
| 영업 마트 DIM_CUST_SALES, 물류 마트 DIM_CUST_LOGI | 거래처유형 코드·이름이 달라 drill-across 불가 |
| 출고 팩트에 날짜 FK 하나(출고일) | "주문월 기준 출고"를 못 구함 |
| 팩트에 ORD_STAT_CD, 증정 플래그를 코드로 | 화면마다 CASE 문으로 이름을 붙이고 취소 제외 규칙이 제각각 |
| 주문번호를 "속성이 없다"며 삭제 | 주문 건수, 원천 추적 불가 |

**After**

| 설계 | 내용 |
|---|---|
| 공통 차원 | DIM_CUST·DIM_ITEM·DIM_DATE를 모든 팩트가 공유, WMS 코드는 적재 시 매핑 |
| 축소 차원 | 월 차원은 날짜 차원에서 파생해 속성 이름·값 일치 |
| Role-playing | 출고 팩트에 ORD_DT_SK, SHIP_DT_SK 둘 다, 역할별 뷰 제공 |
| Junk | 주문상태 × 주문상세유형 + 매출실적 포함여부 |
| Degenerate | ORD_NO, ORD_SEQ, SHIP_NO를 팩트에 유지 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 공통 차원 범위 | 버스 매트릭스에서 두 팩트 이상이 쓰는 차원은 1차부터 공통으로 | 한 팩트만 쓰는 차원은 그 팩트 범위에서 시작하되 이름·코드는 표준을 따름 |
| 계열사 코드가 다를 때 | 그룹 표준 코드를 정하고 계열사 코드는 매핑 테이블로 (차원에는 표준 + 원천 코드 둘 다) | 표준 합의가 늦으면 원천 코드로 적재하고 "미매핑" 값을 -1이 아닌 별도 값으로 표시해 범위를 드러냄 |
| Junk vs 개별 차원 | 값이 적고 서로 관련 없는 플래그 여러 개는 Junk | 속성이 많고 독립적으로 분석되는 코드(예: 거래처유형)는 개별 차원 또는 기존 차원의 속성 |
| Junk 조합 | 조합 수가 작으면 전체 조합을 미리 생성 | 조합이 크면 실제 나온 조합만 적재 시 추가 |
| Role-playing 구현 | 사용자가 모델을 직접 쓰면 역할별 뷰·테이블 | 개발자만 쓰는 모델이면 BI의 비활성 관계 + 측정값에서 관계 지정 |
| 날짜 SK | YYYYMMDD 정수 (파티션·가독성) | 시각까지 필요하면 날짜 차원 + 별도 시간 차원(시·분), 날짜·시각을 한 차원에 섞지 않음 |

## 흔한 실수 3가지

1. **"같은 이름이면 conformed"라고 믿는 실수.** 두 마트 모두 DIM_CUST가 있어도 키 체계나 거래처유형 코드값이 다르면 공통 차원이 아닙니다. 키·속성 이름·코드값·뜻 네 가지를 대조표로 확인합니다.
2. **두 팩트를 공통 차원으로 직접 조인하는 실수.** 주문 팩트와 출고 팩트를 품목 SK로 바로 조인하면 품목별 라인 수가 곱해집니다(Day 16). 각각 공통 차원 수준으로 집계한 뒤 붙입니다.
3. **Degenerate 차원을 지우는 실수.** "차원 테이블이 없으니 필요 없다"며 주문번호를 빼면 건수 집계와 원천 대사가 불가능해집니다. 업무 키는 팩트에 남깁니다.

## 셀프 체크 질문

**Q1. 버스 매트릭스는 무엇이고, 프로젝트 초기에 왜 그립니까?**

:::answer 모범 답안 보기
행에 업무 프로세스(팩트), 열에 공통 차원을 두고 각 팩트가 어떤 차원을 쓰는지 표시한 표입니다. 프로젝트 초기에 그리는 이유는 세 가지입니다. 체크가 많은 열(날짜·품목·회사)이 먼저 공통화해야 할 차원임을 보여 주고, 행을 차수로 나눠 범위를 합의하는 도구가 되며, 1차에서 만든 차원을 2·3차 팩트가 재사용한다는 통합 계획을 한 장으로 설명할 수 있습니다. Kimball 방식에서는 이 표가 Inmon의 전사 모델 역할, 즉 "따로 만들어도 나중에 붙는다"는 보증서입니다.
:::

**Q2. 출고 팩트에 주문일자와 출고일자를 모두 두면 날짜 차원은 몇 개 필요합니까?**

:::answer 모범 답안 보기
물리 테이블은 하나(DIM_DATE)이고, 팩트에는 날짜 FK가 두 개(ORD_DT_SK, SHIP_DT_SK) 있습니다. 같은 차원이 두 역할을 하는 Role-playing입니다. 사용자에게는 역할별 뷰나 BI 모델의 별칭 테이블을 제공하고 컬럼 이름에 "주문연월", "출고연월"처럼 역할을 붙입니다. 하나만 연결하면 다른 기준의 질문(주문월 기준 출고량)에 답할 수 없고, 둘 다 같은 이름으로 노출하면 사용자가 헷갈립니다. 공휴일 같은 달력 속성은 테이블이 하나라 두 역할에 똑같이 적용됩니다.
:::

**Q3. 주문번호는 차원 테이블이 없는데 왜 팩트에 남깁니까?**

:::answer 모범 답안 보기
주문번호는 Degenerate 차원입니다. 주문 헤더의 속성(주문일자, 거래처, 영업사원)은 이미 각 차원으로 빠졌기 때문에 주문번호 차원 테이블을 만들면 키 하나만 남는 빈 테이블이 됩니다. 그래도 주문번호는 주문 건수(COUNT DISTINCT), 헤더 단위 묶음 분석(주문당 평균 라인 수), 원천 시스템과의 대사·추적, 다른 팩트(출고)와 라인 단위로 연결하는 데 꼭 필요합니다. 그래서 테이블 없이 팩트 컬럼으로 둡니다.
:::

## 오늘의 과제

**과제 1.** 거래처유형별로 3월 주문금액(취소 제외)과 3월 출고금액을 drill-across로 한 표에 보여 주세요. 결과 모양은 `cust_tp_nm, ord_amt, ship_amt` 이며 병원은 주문 124,000 / 출고 60,000입니다.

:::answer 해설 보기
두 팩트 모두 공통 거래처 차원(DIM_CUST)을 쓰므로 거래처유형명이 같은 값입니다. 주문 팩트의 거래처 SK는 주문일자 버전, 출고 팩트는 출고일자 버전이지만 각 팩트가 사건 일자에 유효했던 버전의 거래처유형을 쓰므로 문제없습니다(유형이 바뀌면 Day 19처럼 새 버전이 생깁니다). 각각 집계한 뒤 붙입니다.

```sql
WITH o AS (
  SELECT c.cust_tp_nm, SUM(f.ord_amt) AS ord_amt
    FROM dw.fct_ord_line f
    JOIN dw.dim_cust c ON c.cust_sk = f.cust_sk
    JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
   WHERE d.yyyymm = '202603' AND f.ord_stat_cd <> '90'
   GROUP BY c.cust_tp_nm
), s AS (
  SELECT c.cust_tp_nm, SUM(f.ship_amt) AS ship_amt
    FROM dw.fct_ship_line f
    JOIN dw.dim_cust c ON c.cust_sk = f.cust_sk
    JOIN dw.dim_date d ON d.date_sk = f.ship_dt_sk
   WHERE d.yyyymm = '202603'
   GROUP BY c.cust_tp_nm
)
SELECT COALESCE(o.cust_tp_nm, s.cust_tp_nm) AS cust_tp_nm,
       COALESCE(o.ord_amt, 0) AS ord_amt, COALESCE(s.ship_amt, 0) AS ship_amt
  FROM o FULL OUTER JOIN s ON s.cust_tp_nm = o.cust_tp_nm
 ORDER BY cust_tp_nm;
```

도매상 2,160,000 / 2,160,000, 병원 124,000 / 60,000, 약국 82,000 / 82,000입니다. 병원의 차이 64,000원은 청솔내과의원 3월 20일 주문(확정, 미출고)입니다.
:::

**과제 2.** 날짜 차원을 점검하세요. 2026년 월별로 일수, 주말 일수, 월말 행 수를 보여 주는 쿼리를 작성합니다. 결과 모양은 `yyyymm, day_cnt, wkend_cnt, mm_end_cnt` 12행이며 모든 월의 `mm_end_cnt`는 1이어야 합니다.

:::answer 해설 보기
날짜 차원은 모든 팩트가 기대는 기준이므로, 빈 날짜나 중복이 없는지, 월말 플래그가 월마다 정확히 하나인지 적재 후 점검합니다. -1 행은 제외합니다.

```sql
SELECT yyyymm, COUNT(*) AS day_cnt,
       COUNT(*) FILTER (WHERE wkend_yn = 'Y')  AS wkend_cnt,
       COUNT(*) FILTER (WHERE mm_end_yn = 'Y') AS mm_end_cnt
  FROM dw.dim_date
 WHERE yr = 2026
 GROUP BY yyyymm
 ORDER BY yyyymm;
```

공휴일(HLDY_YN)은 샘플에서 모두 N입니다. 실제 공휴일과 그룹 영업일은 회사 달력에서 받아 갱신해야 하며, 이 값의 오너(경영지원실)를 메타데이터에 적어 둡니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 버스 매트릭스 | 프로세스 × 공통 차원, 차수, 차원별 오너 |
| 차원 정의서 | 차원별 grain(한 행의 의미), 속성, 코드값 출처, SCD 유형, -1 행 정의 |
| 공통 차원 대조표 | 계열사 원천 코드 ↔ 그룹 표준 코드 매핑, 미매핑 처리 규칙 |
| 표준 정의서 | 날짜 SK = YYYYMMDD 예외 규칙, Role-playing 컬럼 명명(ORD_DT_SK, SHIP_DT_SK) |
| BI 모델 설계서 | 역할별 날짜 테이블, Junk 차원의 매출 포함 규칙을 측정값과 연결 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 3 "Retail Sales"(날짜 차원, Degenerate 차원), Chapter 4 "Inventory"(버스 매트릭스, Conformed 차원), Chapter 6 "Order Management"(Role-playing 차원, Junk 차원).
- Kimball Group 웹사이트의 Dimensional Modeling Techniques 항목 — "Conformed Dimensions", "Enterprise Data Warehouse Bus Matrix", "Role-Playing Dimensions", "Junk Dimensions", "Degenerate Dimensions".
