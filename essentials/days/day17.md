# Day 17. Fact 테이블 유형

## 오늘의 한 줄

팩트 테이블은 **사건을 한 줄씩 쌓는 트랜잭션 팩트, 정해진 주기마다 상태를 찍는 주기 스냅샷, 한 건의 진행을 마일스톤마다 갱신하는 누적 스냅샷** 세 가지입니다. 그리고 각 숫자가 어느 차원 방향으로 더해도 되는지(가산·반가산·비가산)를 정해 두지 않으면, 재고처럼 "더하면 안 되는 숫자"가 대시보드에서 아무렇지 않게 더해집니다.

## 왜 중요한가

한 대리가 Tableau에서 "3월 한빛펜정 재고"를 그렸더니 6만 개가 넘게 나왔습니다. 일별 재고 스냅샷 31일치를 그대로 합산했기 때문입니다. 실제 월말 재고는 1,900 BOX입니다. 반대로 정 과장은 "주문부터 수금까지 며칠 걸리나"를 묻는데, 트랜잭션 팩트만 있으면 주문·출고·전표·수금 팩트를 매번 엮어야 해서 아무도 답을 못 냅니다. 질문의 모양에 맞는 팩트 유형을 고르고 가산성을 테이블정의서에 적어야 이런 일이 없습니다.

## 핵심 개념

### 1. 트랜잭션 팩트: 사건 하나 = 한 행

쉽게 말하면 **일이 일어날 때마다 한 줄**을 추가합니다. 주문상세, 출고상세, 전표상세가 그렇습니다. 사건이 없으면 행도 없습니다. 가장 상세하고 유연하며, 한 번 들어간 행은 원칙적으로 바뀌지 않습니다(정정은 역분개·정정 행으로). 공통 DW의 FCT_ORD_LINE처럼 현재 주문상태를 들고 있으면 그 컬럼만 덮어쓰는 예외가 생기므로, 상태 이력이 필요하면 누적 스냅샷이나 상태 변경 팩트로 따로 둡니다.

약점은 "상태"를 묻는 질문입니다. "3월 31일 재고"를 트랜잭션(입고·출고)만으로 구하려면 처음부터 모든 거래를 누적해야 하고, 기초재고가 없으면 아예 구할 수 없습니다(Day 2).

### 2. 주기 스냅샷: 정해진 시점마다 상태 = 한 행

**매일 마감(또는 월말)마다 그 시점의 상태를 사진 찍듯** 저장합니다. 일별재고(FCT_INV_DAILY), 월말 채권잔액, 월말 계정잔액이 대표입니다. 사건이 없어도 행이 생깁니다. 재고가 그대로여도 내일 행은 또 생깁니다.

grain은 "주기 × 대상"입니다. 공통 DW의 FCT_INV_DAILY는 "일자 × 창고 × 품목 × 로트". 주기는 질문이 요구하는 가장 촘촘한 단위로 정하고, 보관 기간이 길어지면 오래된 기간은 월말만 남기는 식으로 줄입니다.

### 3. 누적 스냅샷: 한 건의 일생 = 한 행, 진행할 때마다 갱신

**주문상세 한 줄이 주문 → 출고 → 매출전표 → 수금으로 진행하는 과정**을 한 행에 담고, 마일스톤이 일어날 때마다 그 행의 날짜 컬럼을 채웁니다. 날짜 차원 FK가 여러 개이고(주문일·출고일·매출일·수금일), 단계 간 소요일(lag)을 측정값으로 둡니다.

세 유형 중 유일하게 **행을 UPDATE하는** 팩트입니다. 그래서 "언제 어떻게 바뀌었나"는 남지 않습니다. 진행 이력까지 필요하면 트랜잭션 팩트를 따로 둡니다. 시작과 끝이 분명한 파이프라인형 업무(주문~수금, 발주~입고, 작업지시~생산완료)에만 맞습니다.

| 구분 | 트랜잭션 | 주기 스냅샷 | 누적 스냅샷 |
|---|---|---|---|
| 한 행 | 사건 1건 | 주기 × 대상 | 업무 건 1건의 일생 |
| 행이 생길 때 | 사건 발생 시 | 매 주기 (사건 없어도) | 업무 건 시작 시 |
| 행 수정 | 하지 않음 | 하지 않음 (해당 주기 재적재는 가능) | 마일스톤마다 UPDATE |
| 날짜 FK | 사건일 1개 | 스냅샷 일자 1개 | 마일스톤 수만큼 |
| 잘 답하는 질문 | 얼마나 팔렸나 | 그 시점에 얼마나 있나 | 얼마나 걸리나, 어디서 막혔나 |
| 한빛 예시 | FCT_ORD_LINE, FCT_SHIP_LINE | FCT_INV_DAILY | 주문상세 진행 팩트 (아래 예시) |

### 4. 가산성: 어느 방향으로 더해도 되나

| 유형 | 뜻 | 예시 | 집계 방법 |
|---|---|---|---|
| 가산 (Additive) | 모든 차원 방향으로 더해도 됨 | 주문수량, 주문금액, 출고수량 | SUM |
| 반가산 (Semi-additive) | 일부 차원(대개 날짜)으로는 더하면 안 됨 | 재고수량, 계정잔액, 채권잔액 | 창고·품목으로는 SUM, 날짜로는 기간 말 값 또는 평균 |
| 비가산 (Non-additive) | 어느 방향으로도 더하면 안 됨 | 단가, 비율(출고율), 평균 소요일 | 구성 요소를 저장하고 집계 후 다시 계산 |

재고를 날짜로 더하면 안 되는 이유는 **재고가 "흐름"이 아니라 "수위"이기 때문**입니다. 3월 30일에 1,900개, 31일에 1,900개가 있었다는 것은 같은 1,900개가 이틀 동안 있었다는 뜻이지 3,800개가 있었다는 뜻이 아닙니다. 흐름(입고·출고 수량)은 더할 수 있고, 수위(재고)는 특정 시점 값으로 봅니다.

비가산 측정값은 저장하지 않거나, 저장하더라도 **분자·분모를 함께** 저장합니다. 단가 대신 금액과 수량, 출고율 대신 출고수량과 주문수량을 두면 어떤 수준에서든 다시 계산할 수 있습니다.

## 예시

### 재고 일별 스냅샷을 31일치로 펼치기

공통 DW의 FCT_INV_DAILY에는 3월 31일 하루치만 있습니다. 3월에 입고는 없고 출고만 있었으므로, **3월 31일 재고에 그 날짜 이후의 출고를 되돌려 더하면** 3월 각 일자의 마감 재고를 복원할 수 있습니다(학습용 단순화: 3월 중 다른 재고 변동이 없다고 가정).

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

-- 3월 일별 재고 스냅샷 복원: 일자 × 창고 × 품목 × 로트
CREATE TABLE lab.fct_inv_daily AS
SELECT d.date_sk AS inv_dt_sk, f.wh_sk, f.item_sk, f.lot_sk,
       f.inv_qty + COALESCE((SELECT SUM(s.ship_qty)
                               FROM dw.fct_ship_line s
                              WHERE s.lot_sk = f.lot_sk AND s.wh_sk = f.wh_sk
                                AND s.ship_dt_sk > d.date_sk), 0) AS inv_qty
  FROM dw.fct_inv_daily f
  CROSS JOIN dw.dim_date d
 WHERE f.inv_dt_sk = 20260331
   AND d.yyyymm = '202603';

-- 한빛펜정(P10001) 로트별 재고가 바뀐 날만 보기
SELECT d.full_dt, l.lot_no, x.inv_qty
  FROM lab.fct_inv_daily x
  JOIN dw.dim_date d ON d.date_sk = x.inv_dt_sk
  JOIN dw.dim_item i ON i.item_sk = x.item_sk
  JOIN dw.dim_lot  l ON l.lot_sk  = x.lot_sk
 WHERE i.item_cd = 'P10001'
   AND d.full_dt IN (DATE '2026-03-02', DATE '2026-03-03', DATE '2026-03-11', DATE '2026-03-31')
 ORDER BY d.full_dt, l.lot_no;
```

| 일자 | L250901 | L260105 | 합계 |
|---|---|---|---|
| 3월 1일~2일 | 210 | 2,000 | 2,210 |
| 3월 3일~10일 | 200 | 2,000 | 2,200 |
| 3월 11일~31일 | 0 | 1,900 | 1,900 |

### 재고를 날짜로 더하면

```sql
-- 잘못된 집계: 3월 한빛펜정 재고 = 31일치 스냅샷의 합
SELECT SUM(x.inv_qty) AS wrong_inv_qty
  FROM lab.fct_inv_daily x JOIN dw.dim_item i ON i.item_sk = x.item_sk
 WHERE i.item_cd = 'P10001';

-- 바른 집계: 월말 값, 월 평균 재고 (반가산 측정값의 두 가지 답)
SELECT i.item_cd,
       SUM(x.inv_qty) FILTER (WHERE d.mm_end_yn = 'Y')          AS mm_end_inv_qty,
       ROUND(SUM(x.inv_qty) / COUNT(DISTINCT d.date_sk), 1)     AS avg_inv_qty
  FROM lab.fct_inv_daily x
  JOIN dw.dim_date d ON d.date_sk = x.inv_dt_sk
  JOIN dw.dim_item i ON i.item_sk = x.item_sk
 WHERE d.yyyymm = '202603'
 GROUP BY i.item_cd
 ORDER BY i.item_cd;
```

잘못된 집계는 61,920 BOX입니다. 바른 집계는 월말 1,900 BOX, 월 평균 1,997.4 BOX입니다. 평균은 "같은 날짜 안에서 로트를 먼저 더하고(가산 방향), 그 일별 합을 날짜 수로 나누는" 순서여야 맞습니다. 로트 행 단위로 AVG를 쓰면 로트 수에 따라 값이 바뀝니다.

:::note Oracle 차이
Oracle에는 `FILTER (WHERE ...)` 절이 없습니다. `SUM(CASE WHEN d.MM_END_YN = 'Y' THEN x.INV_QTY END)`로 씁니다. 이 형태는 PostgreSQL에서도 동작하므로 두 DB에 같은 SQL을 써야 하면 CASE 형태가 안전합니다.
:::

### 월말 재고 스냅샷

장기 보관용으로는 일별을 다 남기지 않고 월말만 남긴 월 스냅샷을 둡니다. 주기만 다를 뿐 같은 유형입니다.

```sql
CREATE TABLE lab.fct_inv_mm AS          -- 월말재고팩트: 연월 × 창고 × 품목 (로트는 합침)
SELECT d.yyyymm, x.wh_sk, x.item_sk, SUM(x.inv_qty) AS mm_end_inv_qty
  FROM lab.fct_inv_daily x
  JOIN dw.dim_date d ON d.date_sk = x.inv_dt_sk
 WHERE d.mm_end_yn = 'Y'
 GROUP BY d.yyyymm, x.wh_sk, x.item_sk;

SELECT m.yyyymm, i.item_cd, i.item_nm, m.mm_end_inv_qty
  FROM lab.fct_inv_mm m JOIN dw.dim_item i ON i.item_sk = m.item_sk
 ORDER BY i.item_cd;
```

로트를 합친 순간 "유효기한 임박 재고" 질문에는 답할 수 없습니다. 월 스냅샷의 grain에서 무엇을 버릴지는 요구사항으로 정합니다.

### 비가산: 단가를 평균 내면

```sql
-- 한빛펜정 평균 단가: 단가의 평균 vs 금액 ÷ 수량
SELECT ROUND(AVG(f.uprc), 2)                       AS wrong_avg_uprc,
       ROUND(SUM(f.ord_amt) / SUM(f.ord_qty), 2)   AS right_avg_uprc
  FROM dw.fct_ord_line f JOIN dw.dim_item i ON i.item_sk = f.item_sk
 WHERE i.item_cd = 'P10001' AND f.ord_stat_cd <> '90';
```

단가 평균은 3,150원, 수량 가중 평균은 3,191.30원입니다. 15 BOX짜리 3,000원 주문이 300 BOX짜리 3,200원 주문과 같은 무게로 섞였기 때문입니다. 그래서 단가는 팩트에 두더라도 "합산 금지, 금액 ÷ 수량으로 재계산"이라고 테이블정의서에 적습니다.

### 주문~출고~수금 누적 스냅샷

공통 스키마에는 수금 테이블이 없으므로 `lab`에 가상의 수금(TB_COLL)을 만듭니다. 매출전표(TB_SLIP)는 SRC_DOC_NO에 주문번호가 들어 있어 주문 헤더 단위로 연결됩니다.

```sql
CREATE TABLE lab.tb_coll (               -- 수금 (가상, 학습용)
  coll_no   VARCHAR(14) PRIMARY KEY,
  coll_dt   DATE        NOT NULL,
  ord_no    VARCHAR(14) NOT NULL,
  coll_amt  NUMERIC(15) NOT NULL
);

-- 누적 스냅샷: grain = 주문상세 1행, 마일스톤 날짜 SK 4개 (없으면 -1)
CREATE TABLE lab.fct_ord_line_acc AS
SELECT f.ord_no, f.ord_seq, f.item_sk, f.cust_sk,
       f.ord_dt_sk,
       COALESCE(MAX(s.ship_dt_sk), -1)  AS last_ship_dt_sk,     -- 마지막 출고일
       -1                               AS slip_dt_sk,          -- 매출전표일
       -1                               AS coll_dt_sk,          -- 수금일
       f.ord_qty, COALESCE(SUM(s.ship_qty), 0) AS ship_qty, f.ord_amt,
       CAST(NULL AS INTEGER)            AS ord_to_ship_days,
       CAST(NULL AS INTEGER)            AS ord_to_coll_days
  FROM dw.fct_ord_line f
  LEFT JOIN dw.fct_ship_line s ON s.ord_no = f.ord_no AND s.ord_seq = f.ord_seq
 WHERE f.ord_stat_cd <> '90'
 GROUP BY f.ord_no, f.ord_seq, f.item_sk, f.cust_sk, f.ord_dt_sk, f.ord_qty, f.ord_amt;

-- 마일스톤 갱신 1: 출고 소요일
UPDATE lab.fct_ord_line_acc a
   SET ord_to_ship_days = ds.full_dt - dd.full_dt
  FROM dw.dim_date dd, dw.dim_date ds
 WHERE dd.date_sk = a.ord_dt_sk AND ds.date_sk = a.last_ship_dt_sk AND a.last_ship_dt_sk <> -1;

-- 마일스톤 갱신 2: 매출전표 (헤더 단위 문서 → 그 주문의 모든 라인에 같은 날짜)
UPDATE lab.fct_ord_line_acc a
   SET slip_dt_sk = d.date_sk
  FROM erp.tb_slip sl JOIN dw.dim_date d ON d.full_dt = sl.slip_dt
 WHERE sl.src_doc_no = a.ord_no;

SELECT ord_no, ord_seq, ord_dt_sk, last_ship_dt_sk, slip_dt_sk, coll_dt_sk,
       ord_qty, ship_qty, ord_to_ship_days
  FROM lab.fct_ord_line_acc ORDER BY ord_no, ord_seq;
```

7행(취소 1건 제외)이 생기고, 출고된 5행은 출고 소요일 1일, SO2026030001의 두 라인만 매출전표일 2026-03-03이 채워집니다. 미출고 라인(SO2026030004, SO2026040001)은 출고일 -1로 "아직"을 표시합니다. 이제 4월 10일에 SO2026030001의 수금이 들어왔다고 해 봅니다.

```sql
INSERT INTO lab.tb_coll VALUES ('CL2026040001', DATE '2026-04-10', 'SO2026030001', 90200);

-- 마일스톤 갱신 3: 수금 → 같은 행을 UPDATE (누적 스냅샷의 본질)
UPDATE lab.fct_ord_line_acc a
   SET coll_dt_sk       = dc.date_sk,
       ord_to_coll_days = dc.full_dt - dd.full_dt
  FROM lab.tb_coll c
  JOIN dw.dim_date dc ON dc.full_dt = c.coll_dt,
       dw.dim_date dd
 WHERE c.ord_no = a.ord_no AND dd.date_sk = a.ord_dt_sk;

-- 단계별 진행 현황: 어디서 멈춰 있나
SELECT COUNT(*)                                          AS line_cnt,
       COUNT(*) FILTER (WHERE last_ship_dt_sk <> -1)     AS shipped_cnt,
       COUNT(*) FILTER (WHERE slip_dt_sk <> -1)          AS billed_cnt,
       COUNT(*) FILTER (WHERE coll_dt_sk <> -1)          AS collected_cnt,
       ROUND(AVG(ord_to_coll_days), 1)                   AS avg_ord_to_coll_days
  FROM lab.fct_ord_line_acc;
```

7라인 중 출고 5, 전표 2, 수금 2, 주문~수금 평균 39일입니다. 출고 5라인 중 전표가 2라인뿐이라는 것은 Day 2에서 본 "매출전표가 1건뿐"이라는 원천 빈틈이 그대로 드러난 것입니다. 누적 스냅샷은 이렇게 **프로세스의 병목과 데이터 누락을 한 표로** 보여 줍니다.

## Before / After

**Before: 모든 질문을 트랜잭션 팩트로 답하려는 설계**

| 질문 | 트랜잭션만 있을 때 |
|---|---|
| 3월 말 재고 | 기초재고부터 모든 입출고 누적. 기초재고가 없으면 불가 |
| 주문~수금 소요일 | 주문·출고·전표·수금 팩트를 매번 조인, 헤더·라인 grain 맞추기 반복 |
| 재고 추이 | 날짜별 누적합을 매번 계산 |

**After: 질문 모양별 팩트 유형 + 가산성 명시**

| 팩트 | 유형 | 가산성 기록 |
|---|---|---|
| FCT_ORD_LINE, FCT_SHIP_LINE | 트랜잭션 | 수량·금액 가산, 단가 비가산 |
| FCT_INV_DAILY (+ 월말 스냅샷) | 주기 스냅샷 | 재고수량 반가산: 날짜로는 기간 말 값 또는 평균 |
| 주문상세 진행 팩트 | 누적 스냅샷 | 소요일은 더할 수 있고(합계 자체의 의미는 작음), 평균 소요일은 비가산이라 합 ÷ 건수로 재계산 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 재고를 스냅샷으로 받을지 | 원천(WMS)이 일 마감 재고를 주고 시점 비교 질문이 많으면 주기 스냅샷 적재 | 원천이 거래만 주면 입출고 트랜잭션 팩트 + 기초재고로 스냅샷을 DW에서 생성, 대사 규칙 포함 |
| 스냅샷 주기 | 일별 운영 질문(결품, 유효기한 임박)이 있으면 일별 | 경영 보고만이면 월말. 일별을 최근 N개월만 두고 과거는 월말로 압축하는 것도 방법 |
| 누적 스냅샷 도입 | 시작·끝이 분명하고 마일스톤이 고정된 프로세스(주문~수금)이면 도입 | 단계가 되돌아가거나 반복되면(반품·재출고) 상태 전이 트랜잭션 팩트가 맞음 |
| 비가산 측정값 저장 | 분자·분모를 저장하고 비율은 BI 측정값에서 계산 | 원천이 비율만 주면(예: 외부 지표) 저장하되 "합산 금지"를 명시하고 가중치를 함께 받기 |
| 반가산의 BI 구현 | Power BI는 기간 말 값을 측정값으로 정의(예: 날짜 필터의 마지막 날 재고만 더하는 측정값) | 사용자가 직접 끌어다 쓰는 환경이면 마트에 월말 컬럼을 미리 계산해 둠 |

## 흔한 실수 3가지

1. **재고·잔액을 날짜 방향으로 합산하는 실수.** BI 도구의 기본 집계가 SUM이라 그대로 두면 기간 합이 나옵니다. 테이블정의서에 반가산을 적고, BI에는 기간 말 값 측정값을 미리 만들어 제공합니다.
2. **누적 스냅샷에 진행 이력을 기대하는 실수.** 누적 스냅샷은 행을 덮어쓰므로 "출고일이 언제 정정됐나"는 남지 않습니다. 이력이 필요하면 트랜잭션 팩트를 따로 두고, 누적 스냅샷은 현재 진행 상태 보고용으로만 씁니다.
3. **비율·단가를 그대로 평균 내는 실수.** 행 수에 따라 무게가 달라져 집계 수준마다 다른 값이 나옵니다. 분자·분모를 저장하고 합한 뒤 나눕니다.

## 셀프 체크 질문

**Q1. 재고수량이 반가산인 이유와, 월간 재고 보고에서 어떤 값을 보여 주겠습니까?**

:::answer 모범 답안 보기
재고는 특정 시점의 수위(상태)이지 기간 동안의 흐름이 아니기 때문입니다. 같은 날짜 안에서 창고·품목·로트로는 더할 수 있지만, 날짜를 넘어 더하면 같은 물건을 여러 번 센 의미 없는 값이 됩니다. 월간 보고에는 목적에 따라 월말 재고(마감 시점 상태) 또는 월 평균 재고(재고회전율 계산용)를 보여 줍니다. 평균은 일자별로 먼저 합친 뒤 일수로 나눕니다. 입고·출고 수량은 흐름이라 기간 합계가 의미 있으므로 같은 보고서에 함께 둡니다.
:::

**Q2. 주문~수금 소요일을 보려면 왜 누적 스냅샷이 맞습니까? 트랜잭션 팩트로는 안 되나요?**

:::answer 모범 답안 보기
트랜잭션 팩트로도 계산은 가능하지만, 주문·출고·전표·수금 팩트를 매번 조인하고 grain(주문상세·출고상세·전표 헤더·수금 건)을 맞춰야 해서 쿼리가 복잡하고 fan-out 위험이 큽니다. 누적 스냅샷은 주문상세 한 행에 마일스톤 날짜와 소요일을 모아 두므로 "어느 단계에서 멈춰 있나", "평균 며칠 걸리나"를 한 테이블에서 답합니다. 대신 마일스톤이 생길 때마다 행을 UPDATE해야 하고 변경 이력은 남지 않습니다. 그래서 트랜잭션 팩트를 원본으로 두고 누적 스냅샷은 그 위에 만드는 파생 팩트로 운영합니다.
:::

**Q3. 출고율(출고수량 ÷ 주문수량)을 팩트에 컬럼으로 넣자는 의견에 어떻게 답하겠습니까?**

:::answer 모범 답안 보기
출고율은 비가산이라 그대로 넣으면 품목·월로 집계할 때 평균을 내게 되고, 주문 규모가 다른 라인이 같은 무게로 섞여 틀린 값이 나옵니다. 대신 분자(출고수량)와 분모(주문수량)를 저장하고, 출고율은 BI 측정값에서 "합한 뒤 나누기"로 계산하자고 제안합니다. 라인 단위 출고율을 화면에 보여 줘야 한다면 마트나 뷰에서 계산 컬럼으로 두되, 합계 행에는 다시 계산된 값을 쓰도록 측정값 정의서에 적습니다.
:::

## 오늘의 과제

**과제 1.** 복원한 3월 일별 스냅샷(`lab.fct_inv_daily`)으로 품목별 "3월 1일 마감 재고, 3월 31일 마감 재고, 3월 출고수량"을 한 표로 만드세요. 결과 모양은 `item_cd, strt_inv_qty, end_inv_qty, ship_qty` 4행이며 P10001은 2,210 / 1,900 / 310입니다.

:::answer 해설 보기
반가산 측정값(재고)은 특정 날짜의 값을 고르고, 가산 측정값(출고)은 기간 합계를 냅니다. 두 숫자는 grain도 원천 팩트도 다르므로 따로 집계한 뒤 품목으로 붙입니다.

```sql
WITH inv AS (
  SELECT x.item_sk,
         SUM(CASE WHEN d.full_dt = DATE '2026-03-01' THEN x.inv_qty END) AS strt_inv_qty,
         SUM(CASE WHEN d.full_dt = DATE '2026-03-31' THEN x.inv_qty END) AS end_inv_qty
    FROM lab.fct_inv_daily x JOIN dw.dim_date d ON d.date_sk = x.inv_dt_sk
   GROUP BY x.item_sk
), shp AS (
  SELECT s.item_sk, SUM(s.ship_qty) AS ship_qty
    FROM dw.fct_ship_line s JOIN dw.dim_date d ON d.date_sk = s.ship_dt_sk
   WHERE d.yyyymm = '202603'
   GROUP BY s.item_sk
)
SELECT i.item_cd, inv.strt_inv_qty, inv.end_inv_qty, COALESCE(shp.ship_qty, 0) AS ship_qty
  FROM inv
  JOIN dw.dim_item i ON i.item_sk = inv.item_sk
  LEFT JOIN shp ON shp.item_sk = inv.item_sk
 ORDER BY i.item_cd;
```

P10001 2,210 / 1,900 / 310, P10002 500 / 395 / 105, P10003 500 / 480 / 20, R20001 500 / 500 / 0입니다. 정확히 하면 3월 1일 마감 재고와 3월 말 재고의 차이는 3월 2일~31일 출고분인데, 샘플에는 3월 1일 출고가 없어서 3월 출고 합계와 같습니다. "기초 + 입고 - 출고 = 기말"이 맞는지 보는 수불 대사가 재고 스냅샷 검증의 기본입니다.
:::

**과제 2.** 누적 스냅샷(`lab.fct_ord_line_acc`)에서 "출고는 됐는데 매출전표가 없는 주문상세"를 찾으세요. 결과 모양은 `ord_no, ord_seq, last_ship_dt` 이며 3행(SO2026030002 1, SO2026030003 1·2)입니다.

:::answer 해설 보기
누적 스냅샷은 마일스톤 컬럼이 -1(아직)인지로 단계별 누락을 바로 찾습니다. 이 결과는 데이터 품질 이슈(전표 누락) 또는 업무 지연(전표 미발행)이므로 ERP 팀에 확인할 목록이 됩니다.

```sql
SELECT a.ord_no, a.ord_seq, d.full_dt AS last_ship_dt
  FROM lab.fct_ord_line_acc a
  JOIN dw.dim_date d ON d.date_sk = a.last_ship_dt_sk
 WHERE a.last_ship_dt_sk <> -1
   AND a.slip_dt_sk = -1
 ORDER BY a.ord_no, a.ord_seq;
```
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 차원 모델 설계서 | 팩트별 유형(트랜잭션·주기·누적), 주기, 마일스톤 목록과 갱신 규칙 |
| 테이블정의서 | 측정값마다 가산성(가산·반가산·비가산)과 허용 집계 방법, 반가산의 기준 차원(날짜) |
| 측정값 정의서 (BI) | 월말 재고, 평균 재고, 가중 평균 단가, 출고율의 계산식(합한 뒤 나누기) |
| 매핑정의서 | 누적 스냅샷 마일스톤별 원천과 UPDATE 조건, 헤더 단위 문서(전표)를 라인에 붙이는 규칙 |
| 데이터 품질 규칙 목록 | 수불 대사(기초 + 입고 - 출고 = 기말), 출고 후 전표 미발행 건 점검 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 4 "Inventory"(주기 스냅샷, 누적 스냅샷, 반가산 팩트), Chapter 6 "Order Management"(주문 파이프라인 누적 스냅샷).
- Kimball Group 웹사이트의 Dimensional Modeling Techniques 항목 — "Transaction Fact Tables", "Periodic Snapshot Fact Tables", "Accumulating Snapshot Fact Tables", "Additive, Semi-Additive, Non-Additive Facts".
