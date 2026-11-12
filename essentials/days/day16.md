# Day 16. 차원 모델링 4단계

## 오늘의 한 줄

차원 모델링은 **업무 프로세스를 고르고 → 팩트 한 행의 의미(grain)를 선언하고 → 그 행을 설명하는 차원을 정하고 → 그 행에서 재는 숫자(팩트)를 정하는** 네 단계입니다. 이 중 grain 선언이 나머지 셋을 모두 결정하며, grain이 다른 숫자를 한 테이블이나 한 조인에 섞으면 금액이 조용히 불어납니다.

## 왜 중요한가

정 과장이 "3월 출고된 주문의 금액"을 요청했고, 개발자가 주문 헤더의 합계금액을 출고상세에 조인해 합산했다고 해 보겠습니다. 쿼리는 오류 없이 돌고 숫자도 그럴듯하게 큽니다. 그런데 바른팜유통 주문 한 건이 출고상세 3행과 붙으면서 216만 원이 648만 원으로 세 번 더해졌습니다. 한빛로지스는 FEFO(유효기한 빠른 로트 먼저)로 한 주문상세를 여러 로트로 나눠 출고하므로 이 사고는 예외가 아니라 매일 일어납니다. 조인 전에 "양쪽 테이블의 한 행이 각각 무엇인가"를 묻는 습관이 이 사고를 막습니다.

## 핵심 개념

### 1. 1단계: 업무 프로세스를 고른다 (부서가 아니라)

쉽게 말하면 "누가 보고 싶어 하나"가 아니라 **"어떤 사건이 일어나서 기록되나"** 로 시작합니다. 주문 접수, 출고, 입고, 일 마감 재고, 전표 기표처럼 운영계에 트랜잭션이 남는 사건이 프로세스입니다.

부서 기준으로 시작하면 영업팀 마트, 물류팀 마트, 경영지원 마트가 각자 같은 주문 데이터를 다르게 담습니다. 프로세스 기준으로 시작하면 "주문 팩트는 하나, 영업·경영지원은 같은 팩트를 다르게 자른다"가 됩니다. 프로세스를 고를 때는 현업 우선순위(정 과장의 영업실적)와 데이터 준비 상태(원천이 깨끗한가)를 함께 봅니다.

### 2. 2단계: grain을 선언한다 (가장 중요)

grain은 **팩트 테이블 한 행이 정확히 무엇을 뜻하는가**를 업무 언어로 한 문장에 적은 것입니다. "주문상세 1행 = 한 주문에서 한 품목을 주문한 한 줄", "출고상세 1행 = 한 주문상세를 한 로트에서 출고한 한 줄"처럼 씁니다.

grain이 가장 중요한 이유는 세 가지입니다. 첫째, 붙일 수 있는 차원이 grain으로 정해집니다. 주문상세 grain에는 로트 차원을 붙일 수 없습니다(주문할 때 로트는 아직 없음). 둘째, 합산이 맞는지가 grain으로 정해집니다. 서로 다른 grain의 숫자를 한 행에 두면 어느 쪽인가는 반드시 중복 합산됩니다. 셋째, 나중에 바꾸기 가장 어렵습니다. 차원 속성 추가는 컬럼 하나지만 grain 변경은 팩트 재구축입니다.

원칙은 **가능한 가장 상세한 원자(atomic) grain**입니다. 상세 grain에서는 위로 집계할 수 있지만, 집계 grain에서는 아래로 내려갈 수 없습니다.

### 3. 3단계: 차원을 정한다

grain 문장을 읽으면 차원이 보입니다. "**언제**(주문일자) **어느 거래처**가 **어느 품목**을 **어느 영업사원**을 통해 주문한 한 줄"에서 언제·누가·무엇·어디가 차원입니다. 판단 기준은 "grain 한 행에 대해 값이 **하나로** 정해지는가"입니다. 주문상세 한 줄에 대해 주문일자·거래처·품목·영업사원은 하나씩 정해지지만 로트는 여러 개일 수 있으므로 차원이 될 수 없습니다.

### 4. 4단계: 팩트(측정값)를 정한다

팩트는 grain 한 행에서 **재는 숫자**입니다. 주문수량, 주문금액처럼 grain에 딱 맞는 숫자만 넣습니다. 주문 헤더의 배송비나 할인처럼 grain보다 굵은 숫자는 그대로 넣지 않고, 배분하거나(Day 20) 헤더 grain의 별도 팩트로 둡니다. 합산 가능 여부(가산·반가산·비가산)는 Day 17에서 다룹니다.

| 단계 | 질문 | 1차 범위 답 (영업실적) |
|---|---|---|
| 1 프로세스 | 어떤 사건이 기록되나 | 한빛제약 주문 접수 |
| 2 grain | 팩트 한 행은 무엇인가 | 주문상세 1행 (ORD_NO + ORD_SEQ) |
| 3 차원 | 그 행을 무엇으로 설명하나 | 주문일자, 거래처(주문일자 기준 버전), 품목, 주문 영업사원 |
| 4 팩트 | 그 행에서 무엇을 재나 | 주문수량, 단가(비가산), 주문금액 |

## 예시

### 공통 DW의 두 팩트, 두 grain

`schema/10_dw.sql`의 두 트랜잭션 팩트는 grain이 다릅니다.

| 팩트 | grain 선언 | grain 키 | 차원 |
|---|---|---|---|
| 주문상세팩트 (FCT_ORD_LINE) | 한 주문에서 한 품목을 주문한 한 줄 | ORD_NO, ORD_SEQ | 주문일자, 거래처, 품목, 사원 |
| 출고상세팩트 (FCT_SHIP_LINE) | 한 주문상세를 한 로트에서 출고한 한 줄 | SHIP_NO, SHIP_SEQ | 출고일자, 주문일자, 거래처, 품목, 창고, 로트 |

```text
FCT_ORD_LINE (ORD_DTL grain)       FCT_SHIP_LINE (SHIP_DTL grain)
+--------------------------+       +---------------------------+
| SO2026030003 / 1  P10001 |--+--->| SH2026030003 / 1 L250901  |
|   300 BOX  960,000       |  |    |   200 BOX                 |
+--------------------------+  +--->| SH2026030003 / 2 L260105  |
                                   |   100 BOX                 |
                                   +---------------------------+
   주문상세 1행 : 출고상세 N행 (로트 분할)
```

grain 키로 실제 데이터를 확인해 봅니다. "출고상세팩트를 주문상세 단위로 묶으면 1행인가?"를 묻는 쿼리입니다.

```sql
-- 출고상세팩트에서 주문상세(ORD_NO, ORD_SEQ) 하나에 몇 행이 있나
SELECT ord_no, ord_seq, COUNT(*) AS ship_line_cnt, SUM(ship_qty) AS ship_qty
  FROM dw.fct_ship_line
 GROUP BY ord_no, ord_seq
HAVING COUNT(*) > 1;
```

SO2026030003의 1번 라인(한빛펜정 300 BOX)이 2행입니다. 이천물류센터가 오래된 로트 L250901에서 200, 새 로트 L260105에서 100을 출고했기 때문입니다. 출고상세의 grain은 주문상세가 아닙니다.

### fan-out 사고 재현

많은 ERP의 주문 헤더에는 상세 합계를 담은 "주문합계금액" 컬럼이 있습니다(Day 5의 헤더 파생 컬럼). 공통 스키마에는 없으므로 `lab`에 만들어 재현합니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;

-- 주문 헤더 + 주문합계금액(ORD_TOT_AMT)을 가진 ERP를 흉내 낸 테이블
CREATE TABLE lab.tb_ord_hdr AS
SELECT o.ord_no, o.ord_dt, o.cust_no, o.ord_stat_cd, SUM(d.ord_amt) AS ord_tot_amt
  FROM erp.tb_ord o JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
 GROUP BY o.ord_no, o.ord_dt, o.cust_no, o.ord_stat_cd;

-- 잘못된 쿼리 1: 헤더 금액(헤더 grain)을 출고상세(로트 grain)에 조인해 합산
SELECT h.ord_no, COUNT(*) AS joined_rows, SUM(h.ord_tot_amt) AS wrong_amt
  FROM lab.tb_ord_hdr h
  JOIN erp.tb_ship s      ON s.ord_no = h.ord_no
  JOIN erp.tb_ship_dtl l  ON l.ship_no = s.ship_no
 WHERE s.ship_dt BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
 GROUP BY ROLLUP (h.ord_no)
 ORDER BY h.ord_no;
```

| ord_no | joined_rows | wrong_amt |
|---|---|---|
| SO2026030001 | 2 | 164,000 |
| SO2026030002 | 1 | 60,000 |
| SO2026030003 | 3 | 6,480,000 |
| (합계) | 6 | 6,704,000 |

실제 3월 출고 주문의 금액은 82,000 + 60,000 + 2,160,000 = 2,302,000원입니다. 헤더 금액이 출고상세 행 수만큼 복제되어 세 배 가까이 부풀었습니다. 이것이 fan-out(행 폭증)입니다.

"헤더가 문제니까 상세 금액을 쓰면 되겠지"라고 생각하기 쉽지만, 주문상세도 출고상세보다 grain이 굵습니다.

```sql
-- 잘못된 쿼리 2: 주문상세 금액(주문상세 grain)을 출고상세에 조인 → 로트 분할 라인이 두 번
SELECT SUM(d.ord_amt) AS wrong_amt
  FROM erp.tb_ord_dtl d
  JOIN erp.tb_ship_dtl l ON l.ord_no = d.ord_no AND l.ord_seq = d.ord_seq
  JOIN erp.tb_ship s     ON s.ship_no = l.ship_no
 WHERE s.ship_dt BETWEEN DATE '2026-03-01' AND DATE '2026-03-31';
```

결과는 3,262,000원입니다. SO2026030003 1번 라인의 960,000원이 두 번 더해져 960,000원만큼 많습니다. 행 하나만 늘어도 숫자는 틀립니다.

### 바른 방법 두 가지

```sql
-- 바른 방법 A: 측정값을 출고상세 grain에서 만든다 (출고금액 = 출고수량 × 주문단가)
SELECT SUM(f.ship_amt) AS ship_amt
  FROM dw.fct_ship_line f
  JOIN dw.dim_date d ON d.date_sk = f.ship_dt_sk
 WHERE d.yyyymm = '202603';

-- 바른 방법 B: 굵은 grain 쪽으로 먼저 집계한 뒤 1:1로 조인한다
WITH shipped_line AS (                        -- 출고상세 → 주문상세 grain으로 접기
  SELECT l.ord_no, l.ord_seq, SUM(l.ship_qty) AS ship_qty
    FROM erp.tb_ship_dtl l
    JOIN erp.tb_ship s ON s.ship_no = l.ship_no
   WHERE s.ship_dt BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
   GROUP BY l.ord_no, l.ord_seq
)
SELECT SUM(d.ord_amt) AS ord_amt_of_shipped_line, SUM(x.ship_qty) AS ship_qty
  FROM shipped_line x
  JOIN erp.tb_ord_dtl d ON d.ord_no = x.ord_no AND d.ord_seq = x.ord_seq;
```

두 방법 모두 2,302,000원입니다. A는 "출고금액"이라는 측정값을 출고 grain에 맞게 DW에서 계산해 둔 것이고, B는 grain을 맞춘 다음 조인한 것입니다. 원칙은 같습니다. **조인하기 전에 양쪽의 grain을 같게 만든다.** 부분 출고가 생기면 A(출고된 만큼의 금액)와 B(출고된 라인의 주문금액 전체)는 달라지므로, 정 과장에게 "출고금액"이 어느 뜻인지 확인하고 측정값 이름을 따로 붙입니다.

### grain 선언서 (설계 산출물 모양)

| 항목 | 출고상세팩트 (FCT_SHIP_LINE) |
|---|---|
| 업무 프로세스 | 한빛로지스 출고 (주문 기반) |
| grain 문장 | 한 주문상세를 한 창고의 한 로트에서 한 출고 건으로 내보낸 한 줄 |
| grain 키 | SHIP_NO + SHIP_SEQ (원천 TB_SHIP_DTL PK) |
| 차원 | 출고일자, 주문일자(역할), 거래처(출고일자 기준 버전), 품목, 창고, 로트 |
| 측정값 | 출고수량(가산), 출고금액 = 출고수량 × 주문상세 단가(가산, DW 계산) |
| 넣지 않는 것 | 주문수량·주문금액(주문상세 grain), 주문합계금액(헤더 grain) |
| 검증 규칙 | grain 키 중복 0건, 주문상세별 출고수량 합 ≤ 주문수량 |

## Before / After

**Before: 대시보드 요구에 맞춰 컬럼을 모은 "주문출고 통합" 테이블**

| 주문번호 | 주문순번 | 로트번호 | 주문수량 | 주문금액 | 출고수량 | 주문합계금액 |
|---|---|---|---|---|---|---|
| SO2026030003 | 1 | L250901 | 300 | 960,000 | 200 | 2,160,000 |
| SO2026030003 | 1 | L260105 | 300 | 960,000 | 100 | 2,160,000 |
| SO2026030003 | 2 | L251110 | 100 | 1,200,000 | 100 | 2,160,000 |

출고수량은 맞게 더해지지만 주문수량·주문금액·주문합계금액은 더하는 순간 틀립니다. Power BI 사용자는 어느 컬럼이 더해도 되는지 알 수 없습니다.

**After: grain별 팩트 분리 + grain에 맞춘 측정값**

| 팩트 | grain | 넣는 측정값 |
|---|---|---|
| FCT_ORD_LINE | 주문상세 | 주문수량, 주문금액 |
| FCT_SHIP_LINE | 출고상세(로트) | 출고수량, 출고금액(수량 × 주문단가) |
| (필요 시) 헤더 grain 팩트 또는 배분 | 주문 헤더 | 헤더 할인·배송비 (Day 20) |

두 팩트는 공통 차원(품목, 거래처, 날짜)으로 각각 집계한 뒤 나란히 붙입니다(Day 18의 drill-across).

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| grain 수준 | 기본은 원천의 가장 상세한 트랜잭션 grain (출고상세, 로트까지) | 상세 데이터가 너무 크고 질문이 늘 집계 수준이면 상세 팩트는 두고 집계 팩트를 추가 (상세를 버리지 않음) |
| 측정값의 grain이 다를 때 | 배분 규칙이 업무적으로 합의되면 상세 grain으로 배분 (Day 20) | 합의가 안 되면 굵은 grain의 별도 팩트로 두고 섞지 않음 |
| 두 프로세스를 한 팩트로 | grain이 같고 늘 함께 보는 숫자면 한 팩트 가능 | grain이 다르면 반드시 분리. "보기 편하게"는 마트나 뷰에서 |
| 프로세스 선택 순서 | 현업 가치가 크고 원천 품질이 좋은 프로세스부터 (1차: 주문, 출고) | 가치는 크지만 원천이 불안정하면(예: 수기 보정이 많은 매출 조정) 원천 정비를 요구사항으로 먼저 올림 |

grain을 정할 때 시니어가 꼭 하는 질문은 "이 grain 한 행에 대해 값이 **둘 이상** 나올 수 있는 속성이 있습니까?"입니다. 로트, 프로모션, 담당자 복수 배정처럼 둘 이상 나오는 순간 그 속성은 차원이 아니라 더 상세한 grain이나 브리지(Day 20)의 신호입니다.

## 흔한 실수 3가지

1. **grain을 문장으로 적지 않고 "주문 팩트"라고만 부르는 실수.** 주문 헤더인지 상세인지 로트인지 아무도 모르는 채 개발이 시작되고, 측정값이 추가될 때마다 grain이 섞입니다. 팩트마다 grain 문장과 grain 키를 테이블정의서 첫 줄에 적습니다.
2. **헤더 금액을 상세에 반복 저장하는 실수.** "조회 편하라고" 주문합계금액을 상세 행마다 넣으면, 상세를 합산하는 모든 사용자가 fan-out을 겪습니다. 헤더 숫자는 배분하거나 헤더 grain에 둡니다.
3. **조인 후 행 수를 확인하지 않는 실수.** 금액 대사만 하고 행 수를 안 보면 fan-out을 놓칩니다. 조인 전후 행 수, grain 키 중복 0건 테스트를 적재 검증에 넣습니다(dbt라면 unique 테스트).

## 셀프 체크 질문

**Q1. 차원 모델링 4단계 중 grain 선언이 가장 중요한 이유를 설명해 보세요.**

:::answer 모범 답안 보기
grain이 나머지 세 단계를 결정하기 때문입니다. 어떤 차원을 붙일 수 있는지는 "grain 한 행에 값이 하나로 정해지는가"로 판단하고, 어떤 측정값을 넣을 수 있는지도 그 숫자가 grain에 맞는지로 판단합니다. grain이 흐리면 서로 다른 수준의 숫자가 한 팩트에 섞이고 합산할 때 중복이 생깁니다. 또 grain은 나중에 바꾸기 가장 비쌉니다. 차원 속성 추가는 컬럼 하나지만 grain 변경은 팩트 재구축과 모든 리포트 재검증입니다. 그래서 원자 grain으로, 업무 언어 한 문장과 grain 키로 명확히 선언합니다.
:::

**Q2. 출고상세팩트에 주문수량을 넣어 달라는 요청을 받았습니다. 어떻게 하겠습니까?**

:::answer 모범 답안 보기
그대로 넣지 않습니다. 주문수량은 주문상세 grain의 숫자이고, 출고상세는 한 주문상세가 로트별로 여러 행이 될 수 있어서 넣는 순간 합산 시 중복됩니다(공통 샘플의 SO2026030003 1번 라인 300 BOX가 600으로 보임). 요청의 목적을 묻습니다. "주문 대비 출고율"이 목적이면 주문 팩트와 출고 팩트를 각각 주문상세 grain이나 품목·월 수준으로 집계한 뒤 나란히 붙이는 drill-across로 답합니다. 주문~출고 진행을 한 행에서 보고 싶다면 주문상세 grain의 누적 스냅샷 팩트(Day 17)가 맞는 구조입니다.
:::

**Q3. 1차 범위에서 "주문"과 "출고" 중 어느 프로세스를 먼저 모델링하겠습니까?**

:::answer 모범 답안 보기
요청자의 "실적" 정의를 먼저 확인합니다. 정 과장의 영업실적이 수주 기준이면 주문, 매출 인식이 출고 기준이면 출고가 먼저입니다. 그다음 원천 준비 상태를 봅니다. 주문은 한빛제약 ERP 하나에서 오지만 출고는 한빛로지스 WMS에서 오고 거래처·품목 코드를 공통 차원에 맞춰야 하므로 공수가 더 큽니다. 실무에서는 주문 팩트를 먼저 열어 공통 차원(거래처·품목·날짜)을 확정하고, 그 차원을 그대로 쓰는 출고 팩트를 이어서 붙이는 순서가 안전합니다. 첫 팩트에서 공통 차원을 제대로 만들어야 두 번째 팩트가 빨라지기 때문입니다.
:::

## 오늘의 과제

**과제 1.** 정 과장이 "품목별 3월 주문수량과 출고수량을 한 표로" 요청했습니다. fan-out 없이 작성하세요. 결과 모양은 `item_cd, ord_qty, ship_qty` 이며 P10001은 주문 330(3월 주문 10 + 300 + 20), 출고 310이어야 합니다.

:::answer 해설 보기
두 팩트를 직접 조인하면 품목별로 주문 라인 × 출고 라인이 곱해집니다. 각 팩트를 공통 차원(품목) 수준으로 **따로 집계한 뒤** 품목으로 붙입니다. 한쪽에만 있는 품목도 보이도록 FULL OUTER JOIN을 씁니다.

```sql
WITH o AS (
  SELECT i.item_cd, SUM(f.ord_qty) AS ord_qty
    FROM dw.fct_ord_line f
    JOIN dw.dim_item i ON i.item_sk = f.item_sk
    JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
   WHERE d.yyyymm = '202603'
   GROUP BY i.item_cd
), s AS (
  SELECT i.item_cd, SUM(f.ship_qty) AS ship_qty
    FROM dw.fct_ship_line f
    JOIN dw.dim_item i ON i.item_sk = f.item_sk
    JOIN dw.dim_date d ON d.date_sk = f.ship_dt_sk
   WHERE d.yyyymm = '202603'
   GROUP BY i.item_cd
)
SELECT COALESCE(o.item_cd, s.item_cd) AS item_cd,
       COALESCE(o.ord_qty, 0) AS ord_qty, COALESCE(s.ship_qty, 0) AS ship_qty
  FROM o FULL OUTER JOIN s ON s.item_cd = o.item_cd
 ORDER BY item_cd;
```

P10001 330/310, P10002 105/105, P10003 20/20입니다. P10001의 차이 20은 3월 20일 주문(SO2026030004, 확정 상태)이 아직 출고되지 않았기 때문입니다. 주문월과 출고월 기준이 다르다는 점도 표 제목에 밝혀 둡니다.
:::

**과제 2.** 적재 검증 쿼리를 작성하세요. 출고상세팩트에서 (1) grain 키(SHIP_NO, SHIP_SEQ) 중복 건수, (2) 주문상세별 출고수량 합이 주문수량을 넘는 건수를 한 번에 보여 줍니다. 결과 모양은 `dup_grain_cnt, over_ship_cnt` 1행, 둘 다 0입니다.

:::answer 해설 보기
grain 키 유일성은 PK가 막아 주지만, 원천에 PK가 없거나 레이크 파일처럼 제약이 없는 환경이면 쿼리로 확인해야 합니다. 두 번째 규칙은 grain 사이의 업무 규칙(출고 ≤ 주문) 점검이며, 비교하기 전에 출고를 주문상세 grain으로 접는 것이 핵심입니다.

```sql
SELECT
  (SELECT COUNT(*) FROM (SELECT ship_no, ship_seq FROM dw.fct_ship_line
                          GROUP BY ship_no, ship_seq HAVING COUNT(*) > 1) x) AS dup_grain_cnt,
  (SELECT COUNT(*) FROM (SELECT s.ord_no, s.ord_seq
                           FROM dw.fct_ship_line s
                           JOIN dw.fct_ord_line o ON o.ord_no = s.ord_no AND o.ord_seq = s.ord_seq
                          GROUP BY s.ord_no, s.ord_seq, o.ord_qty
                         HAVING SUM(s.ship_qty) > o.ord_qty) y) AS over_ship_cnt;
```

`GROUP BY`에 `o.ord_qty`를 넣은 것은 주문상세 grain(1행)이라 값이 하나이기 때문입니다. 출고 쪽을 접지 않고 `SUM(o.ord_qty)`를 쓰면 그 자체가 또 fan-out이 됩니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 요구사항정의서 | 지표마다 기준 프로세스(주문·출고·전표)와 기준 일자. "출고금액"처럼 뜻이 둘인 말은 정의를 확정 |
| 차원 모델 설계서 (grain 선언서) | 팩트별 프로세스, grain 문장, grain 키, 차원 목록, 측정값과 가산성, 넣지 않는 숫자 |
| 테이블정의서 | 팩트 테이블 첫 줄에 grain 문장, PK = grain 키 |
| 매핑정의서 | 측정값 계산식(출고금액 = 출고수량 × 주문상세 단가)과 원천 조인 경로 |
| 테스트 시나리오 | grain 키 중복 0건, 조인 전후 행 수, 원천 대비 건수·합계 대사, 출고 ≤ 주문 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 2 "Kimball Dimensional Modeling Techniques Overview"(4단계 설계 절차, grain 선언), Chapter 3 "Retail Sales"(4단계를 처음부터 적용하는 사례), Chapter 6 "Order Management"(주문 헤더·라인).
- Kimball Group 웹사이트의 Dimensional Modeling Techniques 항목 — "Four-Step Dimensional Design Process", "Declare the Grain".
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 모델링 영역: 정보계(DW) 모델링.
