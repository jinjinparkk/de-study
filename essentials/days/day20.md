# Day 20. 고급 패턴

## 오늘의 한 줄

기본 스타 스키마로 안 풀리는 질문은 대부분 다섯 가지 모양입니다. **숫자 없는 사건**(팩트리스 팩트), **한 행에 값이 여럿**(브리지), **헤더와 라인의 grain 차이**(배분), **늘 같은 집계**(집계 팩트), **순서가 뒤바뀐 도착**(Late-arriving). 각 패턴은 grain을 지키면서 질문에 답하는 방법입니다.

## 왜 중요한가

정 과장이 "3월에 방문은 했는데 주문이 없는 거래처"를 묻습니다. 주문 팩트에는 방문이 없고, 방문에는 숫자가 없어서 팩트로 만들 생각을 못 하면 답할 수 없습니다. 바른팜유통을 박지훈·최하은 두 명이 함께 맡는데 담당 칸이 하나라면, 실적이 한 사람에게만 가거나 두 사람에게 모두 가서 합계가 부풀어 오릅니다. 신규 거래처 주문이 마스터 등록보다 먼저 들어오면 적재가 실패하거나 실적이 "알 수 없음"으로 사라집니다. 고급 패턴은 이런 일상적 예외를 위한 표준 해법입니다.

## 핵심 개념

### 1. 팩트리스 팩트: 사건이 일어났다는 사실 자체

쉽게 말하면 **측정값 없이 차원 FK만 있는 팩트**입니다. 두 가지 쓰임이 있습니다. 하나는 사건 기록입니다. 영업사원 방문(일자 × 사원 × 거래처)처럼 숫자는 없지만 "일어났다"가 중요한 사건입니다. 다른 하나는 커버리지(대상 범위)입니다. "3월 한빛펜정 약국 프로모션 대상 = 햇살약국, 늘봄약국"처럼 일어날 수 있었던 조합을 기록합니다. 커버리지가 있어야 "대상이었는데 팔리지 않은 것"을 셀 수 있습니다. 판매 팩트에는 팔린 것만 있기 때문입니다.

### 2. 브리지 테이블: 한 행에 값이 여럿일 때

grain 한 행에 차원 값이 둘 이상이면(공동 담당, 복수 진단, 복수 프로모션) 차원 FK 하나로 담을 수 없습니다. 팩트와 차원 사이에 **브리지 테이블**(거래처 × 사원 × 배분율)을 둡니다. 배분율을 곱하면 합계가 보존되는 "가중 보고", 곱하지 않으면 사람마다 전액이 보이는 "영향 보고"가 됩니다. 두 보고는 둘 다 쓸모가 있지만 합계 행의 의미가 다르므로 반드시 구분해서 이름을 붙입니다.

부서처럼 깊이가 가변인 계층도 브리지로 펼칩니다. Day 6에서 만든 "조상-자손 쌍"이 계층 브리지입니다.

### 3. 헤더-라인 grain 불일치: 배분하거나 분리하거나

주문 헤더의 할인·배송비는 라인 grain보다 굵습니다. 선택지는 두 가지입니다. 업무가 합의한 규칙(금액 비례, 수량 비례, 중량 비례)으로 **라인에 배분**하면 품목별 순매출을 볼 수 있습니다. 합의가 안 되면 **헤더 grain 팩트**로 따로 두고 섞지 않습니다. 배분할 때는 원 단위 반올림 차이를 어느 라인에 몰지까지 정해야 헤더 합계와 정확히 맞습니다.

### 4. 집계 팩트: 자주 묻는 수준을 미리 계산

월 × 품목처럼 늘 같은 수준으로 묻는 질문은 상세 팩트에서 집계한 **집계 팩트**를 둡니다. 원칙은 세 가지입니다. 상세 팩트를 대체하지 않는다, 공통 차원(축소 차원)을 쓴다, 상세와 합계가 맞는지 매 적재마다 대사한다. Power BI의 집계 테이블 기능처럼 BI가 알아서 집계 팩트로 보내 주는 구조(aggregate navigation)도 같은 생각입니다.

### 5. Late-arriving: 팩트가 늦거나, 차원이 늦거나

**늦게 도착한 팩트**(3월 14일 출고가 4월 2일에 들어옴)는 차원 SK를 **사건 일자 기준 버전**으로 찾아야 합니다. 현재 버전으로 붙이면 Type 2가 무너집니다. **차원보다 먼저 도착한 팩트**(early-arriving fact: 거래처 마스터 등록 전의 주문)는 -1로 보내면 나중에 고칠 길이 막연해집니다. 업무 키만 아는 **추정 멤버(inferred member)** 를 차원에 먼저 만들어 SK를 주고, 마스터가 도착하면 그 행을 Type 1로 채웁니다.

## 예시

### 팩트리스 팩트: 방문과 프로모션 커버리지

방문 기록과 프로모션 대상은 학습용 가상 데이터입니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE lab.fct_visit (                 -- 방문팩트 (팩트리스): 일자 × 사원 × 거래처
  visit_dt_sk INTEGER NOT NULL, emp_sk INTEGER NOT NULL, cust_sk INTEGER NOT NULL,
  PRIMARY KEY (visit_dt_sk, emp_sk, cust_sk)
);
INSERT INTO lab.fct_visit
SELECT TO_CHAR(v.dt, 'YYYYMMDD')::INT, e.emp_sk, c.cust_sk
  FROM (VALUES (DATE '2026-03-02','E1001','C000101'), (DATE '2026-03-09','E1001','C000101'),
               (DATE '2026-03-02','E1002','C000201'), (DATE '2026-03-18','E1002','C000101'),
               (DATE '2026-03-10','E1003','C000301'), (DATE '2026-03-12','E1003','C000102')) AS v (dt, emp_no, cust_no)
  JOIN dw.dim_emp e  ON e.emp_no = v.emp_no
  JOIN dw.dim_cust c ON c.cust_no = v.cust_no AND v.dt BETWEEN c.eff_strt_dt AND c.eff_end_dt;

-- 3월에 방문했지만 주문이 없는 거래처
SELECT DISTINCT c.cust_no, c.cust_nm
  FROM lab.fct_visit v
  JOIN dw.dim_cust c ON c.cust_sk = v.cust_sk
 WHERE v.visit_dt_sk BETWEEN 20260301 AND 20260331
   AND NOT EXISTS (SELECT 1 FROM dw.fct_ord_line f JOIN dw.dim_cust c2 ON c2.cust_sk = f.cust_sk
                    WHERE c2.cust_no = c.cust_no AND f.ord_dt_sk BETWEEN 20260301 AND 20260331);

CREATE TABLE lab.fct_promo_cvrg (            -- 프로모션대상팩트 (커버리지): 프로모션 × 거래처 × 품목
  promo_cd VARCHAR(10) NOT NULL, cust_no VARCHAR(10) NOT NULL, item_cd VARCHAR(10) NOT NULL,
  strt_dt  DATE NOT NULL, end_dt DATE NOT NULL,
  PRIMARY KEY (promo_cd, cust_no, item_cd)
);
INSERT INTO lab.fct_promo_cvrg VALUES
 ('PRM2603','C000201','P10001',DATE '2026-03-01',DATE '2026-03-31'),
 ('PRM2603','C000202','P10001',DATE '2026-03-01',DATE '2026-03-31');

-- 프로모션 대상이었지만 기간 중 주문이 없는 조합
SELECT p.promo_cd, p.cust_no, p.item_cd
  FROM lab.fct_promo_cvrg p
 WHERE NOT EXISTS (
       SELECT 1 FROM dw.fct_ord_line f
         JOIN dw.dim_cust c ON c.cust_sk = f.cust_sk
         JOIN dw.dim_item i ON i.item_sk = f.item_sk
         JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
        WHERE c.cust_no = p.cust_no AND i.item_cd = p.item_cd
          AND d.full_dt BETWEEN p.strt_dt AND p.end_dt AND f.ord_stat_cd <> '90');
```

방문 후 무주문은 미래종합병원(C000102), 프로모션 미반응은 늘봄약국(C000202)입니다. 늘봄약국은 4월 3일에 주문했지만 프로모션 기간 밖입니다. 커버리지 테이블이 없으면 "대상인데 안 산 곳"이라는 질문 자체가 성립하지 않습니다.

### 브리지: 바른팜유통 공동 담당

바른팜유통(C000301)을 박지훈 60%, 최하은 40%로 공동 담당한다고 가정합니다(가상).

```sql
CREATE TABLE lab.brg_cust_emp (              -- 거래처담당브리지: 거래처 × 사원 × 배분율
  cust_no  VARCHAR(10) NOT NULL, emp_sk INTEGER NOT NULL, alloc_rt NUMERIC(5,4) NOT NULL,
  PRIMARY KEY (cust_no, emp_sk)
);
INSERT INTO lab.brg_cust_emp
SELECT v.cust_no, e.emp_sk, v.rt
  FROM (VALUES ('C000301','E1003',0.6), ('C000301','E1004',0.4)) AS v (cust_no, emp_no, rt)
  JOIN dw.dim_emp e ON e.emp_no = v.emp_no;

-- 배분율 합 = 1 점검 (브리지의 필수 품질 규칙)
SELECT cust_no, SUM(alloc_rt) AS rt_sum FROM lab.brg_cust_emp GROUP BY cust_no HAVING SUM(alloc_rt) <> 1;

-- 가중 보고(합계 보존) vs 영향 보고(사람마다 전액)
SELECT e.emp_nm,
       SUM(f.ord_amt * b.alloc_rt) AS weighted_amt,
       SUM(f.ord_amt)              AS impact_amt
  FROM dw.fct_ord_line f
  JOIN dw.dim_cust c      ON c.cust_sk = f.cust_sk
  JOIN lab.brg_cust_emp b ON b.cust_no = c.cust_no
  JOIN dw.dim_emp e       ON e.emp_sk  = b.emp_sk
 GROUP BY e.emp_nm
 ORDER BY e.emp_nm;
```

배분율 점검은 0건입니다. 가중 보고는 박지훈 1,296,000원, 최하은 864,000원으로 합이 원래 주문금액 2,160,000원과 같습니다. 영향 보고는 두 사람 모두 2,160,000원이라 합치면 두 배가 됩니다. 브리지는 팩트를 여러 행으로 펼치므로 그 자체가 의도된 fan-out이고, 그래서 배분율로 되돌려 놓는 것입니다.

### 헤더 할인·배송비를 라인에 배분

SO2026030003에 헤더 할인 50,000원, SO2026030001에 배송비 3,000원이 있다고 가정합니다(가상). 금액 비례로 배분하고, 원 미만 차이는 금액이 가장 큰 라인에 몹니다.

```sql
CREATE TABLE lab.tb_ord_hdr_chg (            -- 주문헤더 부대금액 (가상): 헤더 grain
  ord_no VARCHAR(14) PRIMARY KEY, dc_amt NUMERIC(15) NOT NULL, dlv_amt NUMERIC(15) NOT NULL
);
INSERT INTO lab.tb_ord_hdr_chg VALUES ('SO2026030003', 50000, 0), ('SO2026030001', 0, 3000);

CREATE TABLE lab.fct_ord_line_alloc AS
WITH base AS (
  SELECT f.ord_no, f.ord_seq, f.ord_amt, h.dc_amt, h.dlv_amt,
         SUM(f.ord_amt) OVER (PARTITION BY f.ord_no) AS hdr_amt,
         ROW_NUMBER() OVER (PARTITION BY f.ord_no ORDER BY f.ord_amt DESC, f.ord_seq) AS amt_rank
    FROM dw.fct_ord_line f JOIN lab.tb_ord_hdr_chg h ON h.ord_no = f.ord_no
), floor_alloc AS (
  SELECT b.*, FLOOR(dc_amt * ord_amt / hdr_amt) AS dc_floor, FLOOR(dlv_amt * ord_amt / hdr_amt) AS dlv_floor
    FROM base b
)
SELECT ord_no, ord_seq, ord_amt,
       dc_floor  + CASE WHEN amt_rank = 1 THEN dc_amt  - SUM(dc_floor)  OVER (PARTITION BY ord_no) ELSE 0 END AS alloc_dc_amt,
       dlv_floor + CASE WHEN amt_rank = 1 THEN dlv_amt - SUM(dlv_floor) OVER (PARTITION BY ord_no) ELSE 0 END AS alloc_dlv_amt
  FROM floor_alloc;

SELECT a.*, a.ord_amt - a.alloc_dc_amt AS net_amt FROM lab.fct_ord_line_alloc a ORDER BY ord_no, ord_seq;

-- 대사: 라인 배분 합 = 헤더 금액 (0행이어야 정상)
SELECT a.ord_no FROM lab.fct_ord_line_alloc a JOIN lab.tb_ord_hdr_chg h ON h.ord_no = a.ord_no
 GROUP BY a.ord_no, h.dc_amt, h.dlv_amt
HAVING SUM(a.alloc_dc_amt) <> h.dc_amt OR SUM(a.alloc_dlv_amt) <> h.dlv_amt;
```

| ord_no | ord_seq | ord_amt | 배분 할인 | 배분 배송비 |
|---|---|---|---|---|
| SO2026030001 | 1 | 32,000 | 0 | 1,170 |
| SO2026030001 | 2 | 50,000 | 0 | 1,830 |
| SO2026030003 | 1 | 960,000 | 22,222 | 0 |
| SO2026030003 | 2 | 1,200,000 | 27,778 | 0 |

내림만 하면 할인 합이 49,999원, 배송비 합이 2,999원으로 1원씩 모자랍니다. 그 1원을 가장 큰 라인에 붙여 헤더와 정확히 맞췄습니다. 이 "1원 규칙"을 매핑정의서에 적지 않으면 회계 대사에서 매달 질문이 옵니다.

### 집계 팩트와 대사

```sql
CREATE TABLE lab.fct_ord_mm_item AS          -- 월 × 품목 집계 팩트 (취소 제외)
SELECT d.yyyymm, f.item_sk, SUM(f.ord_qty) AS ord_qty, SUM(f.ord_amt) AS ord_amt, COUNT(*) AS line_cnt
  FROM dw.fct_ord_line f JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
 WHERE f.ord_stat_cd <> '90'
 GROUP BY d.yyyymm, f.item_sk;

-- 상세 vs 집계 대사: 금액 차이 0이어야 정상
SELECT (SELECT SUM(ord_amt) FROM dw.fct_ord_line WHERE ord_stat_cd <> '90') -
       (SELECT SUM(ord_amt) FROM lab.fct_ord_mm_item) AS diff_amt;
```

집계 팩트에는 LINE_CNT처럼 "몇 건이 모였나"를 함께 두면 평균(금액 ÷ 건수)을 다시 계산할 수 있습니다. 거래처 수처럼 중복을 빼고 세야 하는 값(COUNT DISTINCT)은 집계 팩트끼리 더할 수 없으므로 넣지 않거나 그 수준 전용으로 표시합니다.

### Late-arriving: 추정 멤버와 늦은 팩트

```sql
CREATE TABLE lab.dim_cust (LIKE dw.dim_cust INCLUDING ALL);
INSERT INTO lab.dim_cust SELECT * FROM dw.dim_cust;
SELECT setval(pg_get_serial_sequence('lab.dim_cust', 'cust_sk'), (SELECT MAX(cust_sk) FROM lab.dim_cust));
ALTER TABLE lab.dim_cust ADD COLUMN inferred_yn CHAR(1) NOT NULL DEFAULT 'N';

-- (1) 마스터보다 먼저 온 주문: C000203 주문이 왔는데 차원에 없음 → 추정 멤버 생성
INSERT INTO lab.dim_cust (cust_no, cust_nm, cust_tp_cd, cust_tp_nm, rgn_cd, rgn_nm, emp_no, emp_nm,
                          eff_strt_dt, inferred_yn, batch_id)
SELECT 'C000203', '미확인(C000203)', '-1', '알 수 없음', '-1', '알 수 없음', '-1', '알 수 없음',
       DATE '1900-01-01', 'Y', 'B20260502'
 WHERE NOT EXISTS (SELECT 1 FROM lab.dim_cust WHERE cust_no = 'C000203');

-- (2) 다음 날 마스터 도착: 추정 멤버는 새 버전이 아니라 같은 행을 채움 (Type 1)
UPDATE lab.dim_cust
   SET cust_nm = '새봄약국', cust_tp_cd = '02', cust_tp_nm = '약국', rgn_cd = 'SEL', rgn_nm = '서울',
       emp_no = 'E1002', emp_nm = '이서연', inferred_yn = 'N', batch_id = 'B20260503'
 WHERE cust_no = 'C000203' AND inferred_yn = 'Y';

-- (3) 늦게 온 팩트: 3월 14일 청솔내과의원 출고가 4월 2일에 적재됨 → 사건 일자 버전으로 SK 조회
SELECT 'event_dt 기준' AS lookup_rule, cust_sk, emp_nm
  FROM lab.dim_cust WHERE cust_no = 'C000101' AND DATE '2026-03-14' BETWEEN eff_strt_dt AND eff_end_dt
UNION ALL
SELECT 'curr_yn 기준 (잘못)', cust_sk, emp_nm
  FROM lab.dim_cust WHERE cust_no = 'C000101' AND curr_yn = 'Y';
```

추정 멤버는 SK를 받은 그날부터 팩트가 붙을 수 있고, 마스터가 오면 이름이 채워져 과거 주문까지 "새봄약국"으로 보입니다. 늦은 팩트는 사건 일자 기준이면 김도윤 버전(SK 1), 현재 기준이면 이서연 버전(SK 2)으로 붙습니다. 적재 시점이 아니라 **사건 일자**로 찾아야 Type 2가 의미를 가집니다.

## Before / After

| 상황 | Before | After |
|---|---|---|
| 방문·프로모션 대상 | "숫자가 없어서" 적재 안 함 | 팩트리스 팩트로 적재, NOT EXISTS로 "안 일어난 일" 분석 |
| 공동 담당 | 담당 칸 하나에 대표자만 | 브리지 + 배분율, 가중·영향 보고를 이름으로 구분 |
| 헤더 할인 | 라인마다 헤더 할인 반복 저장 (fan-out) | 금액 비례 배분 + 1원 규칙, 또는 헤더 grain 팩트 |
| 월 보고 성능 | 매번 상세 팩트 전체 집계 | 집계 팩트 + 매 적재 대사 |
| 마스터보다 빠른 주문 | 적재 실패 또는 -1 | 추정 멤버 생성 후 Type 1로 채움 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 커버리지 팩트 | "안 일어난 일" 질문이 반복되면 커버리지 팩트 | 대상 범위가 차원 속성으로 표현되면(예: 약국 전체) 차원 필터 + 주문 팩트로 충분 |
| 브리지 vs 대표값 | 배분이 업무적으로 중요하고(인센티브) 배분율이 관리되면 브리지 | 분석만 필요하고 배분율이 없으면 "주 담당" 한 명을 차원 속성으로 |
| 헤더 금액 | 배분 규칙이 재무와 합의되면 라인 배분 | 합의 전이면 헤더 grain 팩트로 분리하고 품목별 순매출은 보류 |
| 집계 팩트 | BI 응답 시간 요구가 있고 질문 수준이 고정이면 | 질문 수준이 자주 바뀌면 컬럼너 DW의 상세 조회 성능을 먼저 확인(Day 25·27) |
| 차원이 늦을 때 | 업무 키가 확실하면 추정 멤버 | 업무 키조차 비어 있으면 -1 + 오류 테이블로 보내 재처리(Day 23) |

## 흔한 실수 3가지

1. **브리지 배분율 합을 점검하지 않는 실수.** 공동 담당이 추가되면서 합이 1.2가 되면 가중 보고 합계가 조용히 20% 부풉니다. 배분율 합 = 1 점검을 품질 규칙으로 둡니다.
2. **배분 반올림 차이를 방치하는 실수.** 라인 합과 헤더 금액이 1원씩 어긋나 매달 회계 대사 질문이 옵니다. 내림 + 차액을 최대 라인에 주는 규칙을 정하고 대사 쿼리를 둡니다.
3. **늦게 온 팩트를 현재 차원 버전으로 붙이는 실수.** 적재 코드가 `curr_yn = 'Y'`로 SK를 찾으면 늦게 온 3월 거래가 4월 담당에게 갑니다. SK 조회는 항상 사건 일자 BETWEEN으로 합니다.

## 셀프 체크 질문

**Q1. 팩트리스 팩트는 숫자가 없는데 왜 팩트입니까? 예를 들어 설명해 보세요.**

:::answer 모범 답안 보기
팩트는 "측정값을 담는 테이블"이 아니라 "업무 사건이나 관계의 grain을 담는 테이블"이기 때문입니다. 영업사원 방문은 숫자는 없지만 일자 × 사원 × 거래처라는 사건이고, COUNT로 방문 횟수를 셀 수 있습니다. 프로모션 커버리지는 "대상이었다"는 관계를 담아서, 주문 팩트와 NOT EXISTS로 비교해 "대상이었는데 안 산 곳"을 찾게 해 줍니다. 주문 팩트에는 일어난 일만 있으므로 일어나지 않은 일을 분석하려면 커버리지 팩트가 필요합니다.
:::

**Q2. 주문 헤더의 할인 금액을 품목별 매출에 반영하려면 어떻게 하겠습니까?**

:::answer 모범 답안 보기
먼저 재무·영업과 배분 기준(금액 비례, 수량 비례 등)을 합의합니다. 합의되면 라인 grain으로 배분해 주문상세 팩트에 배분 할인 금액을 두고, 원 단위 반올림 차이는 내림 후 차액을 금액이 가장 큰 라인에 주는 식으로 정해서 라인 합이 헤더 금액과 정확히 맞게 합니다. 매 적재마다 "라인 배분 합 = 헤더 금액" 대사를 돌립니다. 합의가 안 되면 할인을 헤더 grain 팩트로 따로 두고, 품목별 매출은 할인 전 금액이라고 명시합니다. 헤더 할인을 라인마다 그대로 반복 저장하는 것만은 하지 않습니다.
:::

**Q3. 신규 거래처의 주문이 거래처 마스터보다 하루 먼저 DW에 들어옵니다. 어떻게 처리하겠습니까?**

:::answer 모범 답안 보기
주문에 거래처번호(업무 키)가 있으므로 거래처 차원에 추정 멤버를 먼저 만듭니다. 업무 키만 채우고 나머지 속성은 "미확인"으로 두며 추정여부 플래그를 'Y'로 표시합니다. 주문 팩트는 이 SK를 받아 정상 적재됩니다. 다음 날 마스터가 오면 추정 멤버 행을 새 버전이 아니라 같은 행에 Type 1로 채우고 플래그를 'N'으로 바꿉니다. 그러면 이미 적재된 주문도 자동으로 정상 거래처명으로 보입니다. -1로 보내면 나중에 팩트의 SK를 다시 고쳐야 하므로 추정 멤버가 낫습니다. 추정 멤버가 일정 기간 이상 채워지지 않으면 품질 경보를 띄웁니다.
:::

## 오늘의 과제

**과제 1.** 사원별 3월 방문 횟수와 3월 주문 건수를 한 표로 보여 주세요(팩트리스 팩트 + 트랜잭션 팩트의 drill-across). 결과 모양은 `emp_nm, visit_cnt, ord_cnt` 이며 김도윤은 2 / 1입니다.

:::answer 해설 보기
팩트리스 팩트의 측정은 COUNT입니다. 주문 건수는 Degenerate 차원(주문번호)의 COUNT DISTINCT입니다. 두 팩트를 사원 수준으로 각각 집계한 뒤 붙입니다.

```sql
WITH v AS (
  SELECT emp_sk, COUNT(*) AS visit_cnt FROM lab.fct_visit
   WHERE visit_dt_sk BETWEEN 20260301 AND 20260331 GROUP BY emp_sk
), o AS (
  SELECT emp_sk, COUNT(DISTINCT ord_no) AS ord_cnt FROM dw.fct_ord_line
   WHERE ord_dt_sk BETWEEN 20260301 AND 20260331 AND ord_stat_cd <> '90' GROUP BY emp_sk
)
SELECT e.emp_nm, COALESCE(v.visit_cnt, 0) AS visit_cnt, COALESCE(o.ord_cnt, 0) AS ord_cnt
  FROM dw.dim_emp e
  LEFT JOIN v ON v.emp_sk = e.emp_sk
  LEFT JOIN o ON o.emp_sk = e.emp_sk
 WHERE e.emp_sk <> -1
 ORDER BY e.emp_no;
```

김도윤 2 / 1, 이서연 2 / 2, 박지훈 2 / 1, 최하은 0 / 0입니다. 날짜 SK가 YYYYMMDD 정수라서 BETWEEN으로 기간을 바로 거를 수 있습니다.
:::

**과제 2.** 배분 결과(`lab.fct_ord_line_alloc`)를 품목 차원과 붙여 품목별 "할인 전 금액, 배분 할인, 할인 후 순금액"을 보여 주세요. 결과 모양은 `item_cd, ord_amt, alloc_dc_amt, net_amt` 이며 P10002는 1,260,000 / 27,778 / 1,232,222입니다.

:::answer 해설 보기
배분 테이블은 주문상세 grain이므로 주문상세 팩트와 grain 키(ORD_NO, ORD_SEQ)로 1:1 조인하면 fan-out 없이 품목을 붙일 수 있습니다. 배분 대상이 아닌 주문도 보이도록 LEFT JOIN을 씁니다.

```sql
SELECT i.item_cd, SUM(f.ord_amt) AS ord_amt,
       SUM(COALESCE(a.alloc_dc_amt, 0)) AS alloc_dc_amt,
       SUM(f.ord_amt - COALESCE(a.alloc_dc_amt, 0)) AS net_amt
  FROM dw.fct_ord_line f
  JOIN dw.dim_item i ON i.item_sk = f.item_sk
  LEFT JOIN lab.fct_ord_line_alloc a ON a.ord_no = f.ord_no AND a.ord_seq = f.ord_seq
 WHERE f.ord_stat_cd <> '90'
 GROUP BY i.item_cd
 ORDER BY i.item_cd;
```

P10001 1,101,000 / 22,222 / 1,078,778, P10002 1,260,000 / 27,778 / 1,232,222, P10003 50,000 / 0 / 50,000입니다. 할인 합계 50,000원이 헤더와 같습니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 차원 모델 설계서 | 팩트리스·커버리지 팩트의 grain, 브리지 구조와 배분율 출처, 집계 팩트 목록과 원천 상세 팩트 |
| 매핑정의서 | 헤더 금액 배분 기준과 1원 규칙, 추정 멤버 생성·갱신 규칙, SK 조회 = 사건 일자 기준 |
| 요구사항정의서 | 공동 담당 실적 배분율의 결정자, 가중·영향 보고 중 어느 것을 공식 실적으로 할지 |
| 데이터 품질 규칙 목록 | 배분율 합 = 1, 배분 합 = 헤더, 상세 = 집계 대사, 장기 미해결 추정 멤버 |
| 테이블정의서 | 브리지·집계 팩트의 PK와 측정값 가산성, 추정여부(INFERRED_YN) 컬럼 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 3 "Retail Sales"(팩트리스 팩트, 프로모션 커버리지), Chapter 6 "Order Management"(헤더 금액 배분), Chapter 19 "ETL Subsystems and Techniques"(늦게 도착하는 데이터 처리, 서로게이트 키 파이프라인).
- Kimball Group 웹사이트의 Dimensional Modeling Techniques 항목 — 팩트리스 팩트, 다중값 차원과 브리지 테이블, 배분 팩트, 집계 팩트, 늦게 도착하는 팩트·차원.
