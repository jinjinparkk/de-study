# Day 25. 대용량 SQL과 성능

## 오늘의 한 줄

성능 튜닝은 SQL을 고치기 전에 **실행계획을 읽어 "얼마나 읽는가"와 "어떻게 붙이는가"를 확인하는 일**입니다. 파티션은 조건이 파티션 키에 직접 걸릴 때만 잘리고, 인덱스는 소수 행을 찾을 때만 이기며, 자주 묻는 집계는 미리 만들어 둡니다. 판단 근거는 감이 아니라 계획입니다.

## 왜 중요한가

월 수백만 건 출고 팩트를 월별 파티션으로 나눴는데 Power BI 리포트가 여전히 느립니다. 계획을 보니 리포트 SQL이 `DIM_DATE.YYYYMM = '202603'`으로 날짜 차원에 조건을 걸고 팩트와 조인해서, 팩트 쪽 파티션이 하나도 잘리지 않고 전부 읽히고 있었습니다. 인덱스를 더 만들자는 제안이 나왔지만 그 쿼리는 한 달치 10%를 읽는 집계라 인덱스로는 빨라지지 않습니다. **계획을 읽지 못하면 틀린 처방**을 합니다.

## 핵심 개념

### 1. 실행계획 읽는 법: 안쪽부터, 아래부터

실행계획은 트리입니다. 들여쓰기가 가장 깊은 줄부터 실행되고, 위로 올라오며 결과가 합쳐집니다. 줄마다 볼 것은 세 가지입니다. **무엇을 어떻게 읽나**(Seq Scan 전체 읽기, Index Scan 인덱스로 찾기), **몇 행으로 추정하나**(rows), **어떻게 붙이나**(Join 종류). `EXPLAIN`은 추정만 보여 주고, `EXPLAIN ANALYZE`는 실제로 실행해 실제 행 수와 시간을 보여 줍니다. 추정 행 수와 실제 행 수가 크게 다르면 통계가 낡았거나 조건이 추정하기 어려운 것이므로, 그것이 튜닝의 첫 단서입니다.

### 2. 조인 방식 세 가지

| 방식 | 원리 | 잘 맞을 때 | 비유 |
|---|---|---|---|
| Nested Loop (NL) | 바깥 행마다 안쪽을 찾음 (안쪽에 인덱스 필요) | 바깥이 소수 행 (주문번호 하나로 조회) | 명단 몇 명을 전화번호부에서 하나씩 찾기 |
| Hash Join | 작은 쪽으로 해시 표를 만들고 큰 쪽을 훑으며 맞춤 | 큰 팩트 × 작은 차원, 등호 조인 | 출석부를 책상에 펴 두고 들어오는 사람 확인 |
| Merge Join | 양쪽을 조인 키로 정렬한 뒤 나란히 맞춤 | 양쪽이 이미 정렬돼 있거나 둘 다 클 때 | 정렬된 두 명단을 위에서부터 같이 내려가기 |

DW의 전형적인 쿼리(팩트 한 달치 × 작은 차원)는 Hash Join이 기본입니다. NL이 대량 행에 나오면 의심합니다.

### 3. 파티션 프루닝: 조건이 키에 "직접" 걸려야 잘린다

파티션 프루닝(partition pruning)은 조건을 보고 읽을 필요 없는 파티션을 계획에서 빼는 것입니다. 파티션 키 컬럼에 **가공하지 않은 조건**(`ORD_DT_SK BETWEEN 20260301 AND 20260331`)이 있어야 합니다. `ORD_DT_SK / 100 = 202603`처럼 컬럼을 가공하거나, 날짜 차원에만 조건을 걸고 조인하면 계획 단계에서 잘리지 않습니다. 파티션 설계 자체(키 선택, 월 단위 여부)는 Day 8에서 다뤘고, 오늘은 **쿼리가 그 설계를 살리는지**를 봅니다.

### 4. 인덱스 vs 전체 읽기

인덱스는 "소수 행을 빨리 찾는" 도구입니다. 테이블의 상당 부분을 읽는 조건(상태 = 출고완료가 95%)이면 인덱스를 타고 한 행씩 찾아가는 것보다 전체를 순서대로 읽는 편이 쌉니다. 그래서 DW 집계 쿼리는 인덱스보다 **파티션으로 읽는 범위를 줄이는 것**이 주 수단이고, 인덱스는 주문번호 조회·드릴스루 같은 점 조회용입니다. 파티션 테이블의 인덱스는 파티션마다 따로 있는 로컬 인덱스여서, 파티션 키 조건 없이 주문번호로만 찾으면 모든 파티션의 인덱스를 뒤집니다.

### 5. 집계 테이블과 MV

같은 집계를 매번 상세에서 계산하지 않도록 미리 만들어 두는 것이 집계 팩트(Day 20)이고, 그 정의를 DB 객체로 관리하는 것이 구체화 뷰(MV, Materialized View)입니다. MV는 정의가 SQL로 남고 `REFRESH` 한 번으로 다시 만들 수 있다는 점이 장점입니다. 대가는 **신선도**입니다. 새로 고침 전까지 MV는 옛 값이므로, 새로 고침을 배치 의존성(Day 24)에 넣고 상세와 대사합니다.

## 예시

### 실습 테이블: 12만 행, 월 파티션

공통 샘플은 몇 행뿐이라 어떤 쿼리든 전체 읽기가 가장 쌉니다. 계획을 읽는 연습을 위해 FCT_ORD_LINE과 같은 모양의 가상 데이터 12만 행을 2026년 월별 파티션 12개에 만듭니다. 이 정도 크기에서도 계획의 **모양**은 운영과 비슷하게 나오지만, 비용 숫자와 방식 선택은 데이터 크기·분포·통계·설정에 따라 달라지므로 운영 판단은 운영 규모의 계획으로 합니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;
CREATE TABLE lab.fct_ord_big (            -- 주문상세팩트 대용량 실습본 (가상 데이터)
  ord_dt_sk   INTEGER     NOT NULL,       -- 파티션 키
  cust_sk     INTEGER     NOT NULL,
  item_sk     INTEGER     NOT NULL,
  emp_sk      INTEGER     NOT NULL,
  ord_no      VARCHAR(14) NOT NULL,
  ord_seq     NUMERIC(4)  NOT NULL,
  ord_stat_cd VARCHAR(2)  NOT NULL,
  ord_qty     NUMERIC(10) NOT NULL,
  ord_amt     NUMERIC(15) NOT NULL
) PARTITION BY RANGE (ord_dt_sk);

DO $$
DECLARE m DATE;
BEGIN
  FOR m IN SELECT generate_series(DATE '2026-01-01', DATE '2026-12-01', INTERVAL '1 month')::DATE LOOP
    EXECUTE format('CREATE TABLE lab.fct_ord_big_%s PARTITION OF lab.fct_ord_big FOR VALUES FROM (%s) TO (%s)',
                   to_char(m, 'YYYYMM'), to_char(m, 'YYYYMMDD'), to_char(m + INTERVAL '1 month', 'YYYYMMDD'));
  END LOOP;
END $$;

-- 하루 약 330행, 거래처·품목·사원 SK는 공통 차원의 실제 SK, 5%는 취소
INSERT INTO lab.fct_ord_big
SELECT TO_CHAR(DATE '2026-01-01' + (g % 365), 'YYYYMMDD')::INT,
       2 + (g % 6), 2 + (g % 3), 2 + (g % 4),
       'SX' || LPAD((g / 3)::TEXT, 10, '0'), (g % 3) + 1,
       CASE WHEN g % 20 = 0 THEN '90' ELSE '30' END,
       1 + (g % 50), (1 + (g % 50)) * 3000
  FROM generate_series(1, 120000) AS g;

CREATE INDEX ix_fct_ord_big_01 ON lab.fct_ord_big (ord_no, ord_seq);   -- 파티션마다 로컬 인덱스
ANALYZE lab.fct_ord_big;
ANALYZE dw.dim_item;
ANALYZE dw.dim_date;
```

`ANALYZE`는 통계를 모읍니다. 대량 적재 직후 통계가 없으면 옵티마이저가 행 수를 엉뚱하게 추정해 나쁜 계획을 고르므로, 적재 배치의 마지막 단계에 통계 수집을 넣습니다.

### 프루닝: 되는 조건, 안 되는 조건

```sql
-- (가) 파티션 키에 직접 범위 조건
EXPLAIN SELECT SUM(ord_amt) FROM lab.fct_ord_big WHERE ord_dt_sk BETWEEN 20260301 AND 20260331;
-- (나) 파티션 키를 가공
EXPLAIN SELECT SUM(ord_amt) FROM lab.fct_ord_big WHERE ord_dt_sk / 100 = 202603;
-- (다) 날짜 차원에 조건을 걸고 조인 (BI 도구가 흔히 만드는 모양)
EXPLAIN SELECT SUM(f.ord_amt)
          FROM lab.fct_ord_big f JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
         WHERE d.yyyymm = '202603';
```

계획의 요지만 옮기면 이렇습니다(비용 숫자 생략).

```text
(가) Aggregate
       -> Seq Scan on fct_ord_big_202603            파티션 1개
            Filter: ord_dt_sk >= 20260301 AND <= 20260331
(나) Aggregate
       -> Append
            -> Seq Scan on fct_ord_big_202601       12개 전부
            -> ... (202602 ~ 202612)
(다) Aggregate
       -> Hash Join (f.ord_dt_sk = d.date_sk)
            -> Append -> Seq Scan 202601 ~ 202612   12개 전부
            -> Hash -> Seq Scan on dim_date          yyyymm 필터
```

(가)는 3월 파티션 하나만 읽습니다. (나)와 (다)는 결과는 같지만 12개를 모두 읽습니다. (다)가 실무에서 가장 흔한 함정입니다. 처방은 세 가지입니다. 마트나 BI 뷰에서 팩트의 파티션 키에 직접 조건이 걸리도록 SQL을 만들고(예: 리포트 기간 파라미터를 ORD_DT_SK 범위로), 팩트에 연월(YYYYMM) 같은 파티션 친화 컬럼을 두거나, 월 단위 리포트는 아예 월 집계(MV)로 보냅니다.

:::note Oracle 차이
Oracle 실행계획은 `EXPLAIN PLAN FOR ...` 후 `SELECT * FROM TABLE(DBMS_XPLAN.DISPLAY)`로 보고, 실제 실행 통계는 `DBMS_XPLAN.DISPLAY_CURSOR`로 봅니다. 프루닝은 계획의 Pstart/Pstop 열로 확인합니다. Oracle은 `/*+ USE_HASH(f) */`, `/*+ USE_NL */`, `/*+ INDEX(...) */`, `/*+ FULL(...) */` 같은 힌트로 방식을 지정할 수 있지만 PostgreSQL에는 힌트가 없고 `enable_*` 설정으로 실험만 합니다. 조인 결과로 실행 중에 파티션을 거르는 기능은 DBMS와 버전마다 다르므로, 계획으로 확인하기 전에는 기대하지 않습니다.
:::

### 인덱스가 이기는 경우와 지는 경우

```sql
-- (라) 주문번호 하나: 파티션 키 조건 없음
EXPLAIN SELECT * FROM lab.fct_ord_big WHERE ord_no = 'SX0000012345';
-- (마) 주문번호 + 주문일자 범위
EXPLAIN SELECT * FROM lab.fct_ord_big WHERE ord_no = 'SX0000012345' AND ord_dt_sk BETWEEN 20260301 AND 20260331;
-- (바) 95%가 해당하는 조건
EXPLAIN SELECT COUNT(*) FROM lab.fct_ord_big WHERE ord_stat_cd = '30';
```

```text
(라) Append
       -> Index Scan using fct_ord_big_202601_..._idx   12개 파티션 인덱스
       -> ... (12개)
(마) Index Scan using fct_ord_big_202603_..._idx         1개
       Index Cond: ord_no = 'SX0000012345'
(바) Aggregate -> Append -> Seq Scan 12개 (Filter: ord_stat_cd = '30')
```

(라)는 인덱스를 타지만 12개 파티션의 인덱스를 모두 뒤집니다. 화면에서 주문번호로 드릴스루할 때 주문일자를 함께 넘기면(마) 하나로 줄어듭니다. (바)는 상태코드 인덱스를 만들어도 전체 읽기가 낫습니다. 이런 저선택도 컬럼에 인덱스를 거는 것은 적재만 느리게 합니다.

### 조인 방식 바꿔 보기

옵티마이저가 고른 방식과 다른 방식을 강제로 비교해 보면 각 방식의 모양이 눈에 들어옵니다. `SET LOCAL`은 트랜잭션 안에서만 유효하고 ROLLBACK으로 원래대로 돌아갑니다. 운영 쿼리에 이런 설정을 쓰지 않습니다.

```sql
-- 3월 품목별 금액: 기본 선택
EXPLAIN SELECT i.item_nm, SUM(f.ord_amt)
          FROM lab.fct_ord_big f JOIN dw.dim_item i ON i.item_sk = f.item_sk
         WHERE f.ord_dt_sk BETWEEN 20260301 AND 20260331
         GROUP BY i.item_nm;

BEGIN;
SET LOCAL enable_hashjoin = off;          -- Hash 금지 → NL
EXPLAIN SELECT i.item_nm, SUM(f.ord_amt)
          FROM lab.fct_ord_big f JOIN dw.dim_item i ON i.item_sk = f.item_sk
         WHERE f.ord_dt_sk BETWEEN 20260301 AND 20260331
         GROUP BY i.item_nm;
SET LOCAL enable_nestloop = off;          -- NL도 금지 → Merge
EXPLAIN SELECT i.item_nm, SUM(f.ord_amt)
          FROM lab.fct_ord_big f JOIN dw.dim_item i ON i.item_sk = f.item_sk
         WHERE f.ord_dt_sk BETWEEN 20260301 AND 20260331
         GROUP BY i.item_nm;
ROLLBACK;
```

```text
기본  HashAggregate
        -> Hash Join (f.item_sk = i.item_sk)
             -> Seq Scan on fct_ord_big_202603 f      큰 쪽: 훑기
             -> Hash -> Seq Scan on dim_item i        작은 쪽: 해시 표
NL    HashAggregate
        -> Nested Loop
             -> Seq Scan on fct_ord_big_202603 f
             -> Memoize -> Index Scan using dim_item_pkey   행마다 찾기
Merge HashAggregate
        -> Merge Join (f.item_sk = i.item_sk)
             -> Sort -> Seq Scan on fct_ord_big_202603 f    정렬 비용
             -> Sort -> Seq Scan on dim_item i
```

세 계획 모두 같은 결과를 내지만, 팩트 한 달치를 차원 하나와 붙이는 이 모양에서는 Hash가 기본으로 선택됩니다. NL은 바깥 행 수만큼 안쪽을 찾고(Memoize는 같은 키 결과를 캐시하는 PostgreSQL의 장치), Merge는 큰 팩트를 정렬하는 비용이 듭니다.

### MV: 월 × 품목 집계

```sql
CREATE MATERIALIZED VIEW lab.mv_ord_mm_item AS        -- 월 × 품목 집계 (취소 제외)
SELECT ord_dt_sk / 100 AS yyyymm, item_sk,
       SUM(ord_qty) AS ord_qty, SUM(ord_amt) AS ord_amt, COUNT(*) AS line_cnt
  FROM lab.fct_ord_big
 WHERE ord_stat_cd <> '90'
 GROUP BY 1, 2;
CREATE UNIQUE INDEX ux_mv_ord_mm_item ON lab.mv_ord_mm_item (yyyymm, item_sk);

-- 배치 마지막 단계: 새로 고침 (유일 인덱스가 있으면 조회를 막지 않는 CONCURRENTLY 가능)
REFRESH MATERIALIZED VIEW CONCURRENTLY lab.mv_ord_mm_item;

-- 상세와 대사: 0이어야 정상
SELECT (SELECT SUM(ord_amt) FROM lab.fct_ord_big WHERE ord_stat_cd <> '90')
     - (SELECT SUM(ord_amt) FROM lab.mv_ord_mm_item) AS diff_amt;
```

MV는 36행(12개월 × 3품목)이고 차이는 0입니다. MV 정의 안의 `ORD_DT_SK / 100`은 집계를 **만들 때** 한 번 계산하므로 문제가 없습니다. 조회 때 컬럼을 가공하는 것이 문제입니다.

:::note Oracle 차이
Oracle MV는 `REFRESH FAST`(MV 로그 기반 증분 새로 고침)와 `ENABLE QUERY REWRITE`(상세 테이블을 조회해도 옵티마이저가 MV로 바꿔 읽음)를 지원합니다. PostgreSQL MV는 전체 재계산만 하고 쿼리 재작성이 없으므로, BI가 MV를 직접 읽게 연결합니다.
:::

## Before / After

| 상황 | Before | After |
|---|---|---|
| 월 리포트 | 날짜 차원 조건 + 팩트 조인 → 전 파티션 | 팩트 파티션 키 범위 조건, 또는 월 집계 MV |
| 기간 조건 | `TO_CHAR(dt, 'YYYYMM') = '202603'` | `dt >= DATE '2026-03-01' AND dt < DATE '2026-04-01'` |
| 느린 쿼리 대응 | 인덱스 추가 | 계획 확인 → 읽는 범위(파티션) → 조인 방식 → 통계 순으로 점검 |
| 드릴스루 | 주문번호만 넘김 | 주문번호 + 주문일자 (파티션 1개) |
| 집계 | BI가 매번 상세 집계 | 자주 쓰는 수준은 MV, 새로 고침은 배치 의존성에 포함 + 대사 |
| 적재 후 | 통계 그대로 | 적재 마지막에 통계 수집 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 인덱스 vs 파티션 | 소수 행 점 조회(주문번호, 거래처 상세)면 인덱스 | 기간 집계면 파티션 프루닝 + 전체 읽기 |
| 인덱스 추가 | 조회 패턴이 반복되고 선택도가 높으면 | 선택도가 낮거나 적재가 SLA에 빠듯하면 추가하지 않음 (인덱스는 적재 비용) |
| 집계 MV | 같은 수준의 질문이 반복되고 몇 시간 늦어도 되면 | 실시간성이 필요하거나 질문 수준이 제각각이면 상세 + 파티션 |
| NL이 보이면 | 바깥 행이 소수면 정상 | 바깥 행 추정이 크게 틀렸다면 통계부터 다시 |
| 튜닝 순서 | 1) 읽는 양(프루닝·필터 위치) 2) 조인 방식 3) 통계 4) 인덱스 | 마지막 수단이 힌트·설정 변경 (운영에서 고정된 힌트는 데이터가 바뀌면 독이 됨) |

## 흔한 실수 3가지

1. **파티션 키를 함수로 감싸는 실수.** `TO_CHAR`, `TRUNC`, 나눗셈 하나로 프루닝이 사라집니다. 범위 조건으로 바꾸고, BI 도구가 만드는 SQL도 계획으로 확인합니다.
2. **EXPLAIN 없이 인덱스부터 만드는 실수.** 집계 쿼리는 대개 인덱스로 빨라지지 않고, 인덱스만 늘어 적재가 느려집니다.
3. **작은 개발 DB의 계획으로 결론 내는 실수.** 몇 백 행이면 모든 것이 Seq Scan입니다. 운영 규모 데이터(또는 오늘처럼 부풀린 데이터)와 최신 통계로 봅니다.

## 셀프 체크 질문

**Q1. 월별 파티션을 했는데 리포트가 빨라지지 않았습니다. 무엇부터 확인하겠습니까?**

:::answer 모범 답안 보기
리포트가 실제로 보내는 SQL의 실행계획을 봅니다. 팩트 쪽에 Append 아래 파티션이 몇 개 나오는지가 첫 확인입니다. 전부 나오면 조건이 파티션 키에 직접 걸리지 않은 것입니다. 흔한 원인은 날짜 차원에만 조건을 걸고 조인하는 경우, 파티션 키를 함수로 가공하는 경우, 파티션 키와 다른 날짜 컬럼(출고일 vs 주문일)으로 거르는 경우입니다. 처방은 팩트 키 범위 조건이 들어가도록 뷰·파라미터를 바꾸거나, 월 단위면 집계 MV로 보내는 것입니다. 프루닝이 되는데도 느리면 조인 방식과 통계를 봅니다.
:::

**Q2. Nested Loop, Hash, Merge Join은 각각 언제 유리합니까?**

:::answer 모범 답안 보기
NL은 바깥 행이 적고 안쪽에 조인 키 인덱스가 있을 때 유리합니다. 주문번호 하나로 상세와 차원을 붙이는 점 조회가 전형입니다. Hash는 한쪽이 작아 메모리에 해시 표를 만들 수 있고 등호 조인일 때 유리해서, 큰 팩트 × 작은 차원 집계의 기본입니다. Merge는 양쪽이 조인 키로 이미 정렬돼 있거나 둘 다 커서 해시 표가 메모리에 안 들어갈 때 유리합니다. 대량 행에 NL이 나오면 대개 행 수 추정이 틀린 것이므로 통계부터 봅니다.
:::

**Q3. 집계 테이블(또는 MV)을 만들자는 요청에 무엇을 따져 보겠습니까?**

:::answer 모범 답안 보기
첫째, 같은 수준의 질문이 반복되는지입니다. 질문마다 수준이 다르면 집계가 늘어나기만 합니다. 둘째, 신선도 요구입니다. 새로 고침 주기를 배치에 넣고 상세보다 늦어도 되는지 현업과 합의합니다. 셋째, 가산성입니다. 거래처 수처럼 COUNT DISTINCT는 집계끼리 더할 수 없으므로 그 수준 전용으로 표시합니다(Day 20). 넷째, 대사입니다. 새로 고침 후 상세와 금액 차이 0을 품질 규칙으로 돌립니다. 마지막으로 BI 쪽 집계 기능(Power BI 집계 테이블, Tableau 추출)으로 대신할 수 있는지도 비교합니다(Day 26).
:::

## 오늘의 과제

**과제 1.** 정 과장이 "3월 첫째 주(3/2~3/8) 품목별 매출"을 요청했습니다. 파티션 프루닝이 되는 SQL을 쓰고 EXPLAIN으로 3월 파티션 하나만 읽는지 확인한 뒤 결과를 내세요. 결과 모양은 `item_nm, ord_amt` 3행이고, 계획의 팩트 쪽 스캔은 fct_ord_big_202603 하나입니다.

:::answer 해설 보기
날짜를 사람이 읽기 좋은 DATE로 받더라도, 팩트에는 DATE_SK 정수 범위로 바꿔 직접 겁니다. 날짜 차원은 표시용 속성이 필요할 때만 조인합니다.

```sql
EXPLAIN SELECT i.item_nm, SUM(f.ord_amt) AS ord_amt
          FROM lab.fct_ord_big f JOIN dw.dim_item i ON i.item_sk = f.item_sk
         WHERE f.ord_dt_sk BETWEEN 20260302 AND 20260308
           AND f.ord_stat_cd <> '90'
         GROUP BY i.item_nm;

SELECT i.item_nm, SUM(f.ord_amt) AS ord_amt
  FROM lab.fct_ord_big f JOIN dw.dim_item i ON i.item_sk = f.item_sk
 WHERE f.ord_dt_sk BETWEEN 20260302 AND 20260308
   AND f.ord_stat_cd <> '90'
 GROUP BY i.item_nm
 ORDER BY i.item_nm;
```

주가 월을 걸치는 경우(3/30~4/5)에도 범위 조건이면 3월·4월 두 파티션만 읽습니다.
:::

**과제 2.** (다)의 쿼리를 프루닝이 되도록 바꾸되, 사용자는 여전히 '202603'이라는 연월만 넘긴다고 가정합니다. 날짜 차원에서 그 달의 최소·최대 DATE_SK를 먼저 구해 팩트 범위 조건으로 쓰는 방법을 작성하고 금액이 (가)와 같은지 확인하세요. 결과 모양은 `ord_amt` 1행입니다.

:::answer 해설 보기
조인 대신 범위를 먼저 계산해 팩트에 넘깁니다. EXPLAIN에는 12개 파티션이 모두 보이지만 조건이 `(InitPlan ...)` 값으로 바뀐 것이 보입니다. PostgreSQL은 이런 값으로 **실행 시점에** 범위 밖 파티션을 건너뛸 수 있고, 이는 `EXPLAIN ANALYZE`에서 실행되지 않은 파티션으로 확인합니다. 계획 단계에서 확실히 자르려면 애플리케이션이나 BI 파라미터에서 범위를 계산해 리터럴로 넘깁니다.

```sql
EXPLAIN SELECT SUM(f.ord_amt)
          FROM lab.fct_ord_big f
         WHERE f.ord_dt_sk BETWEEN (SELECT MIN(date_sk) FROM dw.dim_date WHERE yyyymm = '202603')
                               AND (SELECT MAX(date_sk) FROM dw.dim_date WHERE yyyymm = '202603');

SELECT SUM(f.ord_amt) AS ord_amt
  FROM lab.fct_ord_big f
 WHERE f.ord_dt_sk BETWEEN (SELECT MIN(date_sk) FROM dw.dim_date WHERE yyyymm = '202603')
                       AND (SELECT MAX(date_sk) FROM dw.dim_date WHERE yyyymm = '202603');
```

금액은 (가)의 `SUM(ord_amt)`와 같습니다. 마트 설계 관점에서는 팩트에 연월 컬럼을 두고 그 컬럼으로 파티션하는 대안도 있습니다(Day 8).
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 물리 설계서 (테이블정의서 보강) | 파티션 키·단위, 인덱스 목록과 각 인덱스가 지원하는 조회 패턴, 통계 수집 시점 |
| SQL 작성 표준 | 파티션 키 가공 금지, 기간은 반열림 범위, 드릴스루 시 일자 동반, 힌트 사용 승인 절차 |
| 성능 테스트 계획서 | 운영 규모 데이터, 대표 쿼리 목록(BI 리포트별), 계획 확인 항목(프루닝, 조인 방식) |
| 마트 설계서 | 집계·MV 목록, 수준(grain), 새로 고침 시점, 상세 대사 규칙 |

## 참고할 원전

- PostgreSQL 공식 문서 — Using EXPLAIN, Table Partitioning(Partition Pruning), Materialized Views, Planner Method Configuration(`enable_*`).
- Oracle Database SQL Tuning Guide — 실행계획 읽기, 조인 방식, 파티션 프루닝, 힌트.
- Oracle Database Data Warehousing Guide — Materialized Views와 Query Rewrite.
- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — 집계 팩트(aggregate fact) 기법.
