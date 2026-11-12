# Day 8. 물리 모델링

## 오늘의 한 줄

물리 모델링은 논리 모델의 약속을 DB가 **스스로 지키게** 만드는 일입니다. 타입·NULL·제약조건으로 잘못된 값이 들어올 길을 막고, 인덱스와 파티션은 "이 테이블을 누가 어떤 조건으로 읽고, 언제 지우는가"에서 출발해 정합니다.

## 왜 중요한가

출고일자를 `VARCHAR(8)`로 만들면 어느 날 '2026031'(7자리)이나 '20260230'(없는 날짜)이 들어와도 DB는 받아 줍니다. 월말 배치는 그 행에서 날짜 변환 오류로 멈춥니다. 반대로 출고상세가 월 1억 건(가상의 규모)으로 커졌는데 파티션 없이 한 테이블로 두면, 3년 지난 데이터를 지우는 DELETE 한 번이 몇 시간짜리 작업이 되고 그동안 운영 화면이 느려집니다. 물리 설계의 실수는 데이터가 쌓인 뒤에야 드러납니다.

## 핵심 개념

### 1. 데이터 타입: "그 값으로 무엇을 할 것인가"로 고릅니다

타입은 들어올 수 있는 값의 울타리입니다. 넓을수록 편해 보이지만 검증 책임이 애플리케이션과 배치로 넘어갑니다.

| 값의 성격 | 고를 타입 | 이유 |
|---|---|---|
| 일자 (SHIP_DT) | DATE | 없는 날짜를 DB가 거부하고, 날짜 연산·범위 파티션이 바로 됨 |
| 일시 (REG_DTM) | TIMESTAMP | 시각이 필요할 때만. 일자와 섞지 않음 |
| 금액 (ORD_AMT) | NUMERIC(15) | 원 단위 정수. 부동소수(FLOAT)는 합계가 어긋날 수 있어 금지 |
| 수량 (SHIP_QTY) | NUMERIC(10) | 낱개·BOX는 정수. KG처럼 소수가 필요한 품목은 BOM_QTY처럼 소수 자리 지정 |
| 코드 (ORD_STAT_CD) | VARCHAR(2) | '01'의 앞자리 0을 지키려면 숫자 타입이 아니라 문자 |
| 여부 (USE_YN) | CHAR(1) + CHECK ('Y','N') | 길이가 고정이고 값이 두 개뿐 |

판단 기준은 하나입니다. **계산하면 숫자, 비교·정렬만 하면 문자, 달력이면 날짜.** 사업자등록번호는 숫자로만 되어 있어도 더하지 않으므로 문자입니다.

같은 의미의 컬럼은 모든 테이블에서 같은 타입·길이여야 합니다. 이 "같은 의미 = 같은 타입"을 전사 규칙으로 만든 것이 Day 10의 표준도메인입니다.

### 2. NULL 정책: 기본은 NOT NULL, NULL은 허락받는 것

NULL은 "모른다"에 가깝습니다. 그래서 `WHERE col <> 'Y'`에서 NULL 행이 빠지고, `NOT IN` 서브쿼리에 NULL이 하나라도 있으면 결과가 통째로 빕니다.

시니어의 규칙은 단순합니다. **모든 컬럼은 NOT NULL로 시작하고, NULL을 허용하려면 "언제 비는가"를 테이블정의서에 적습니다.** 공통 스키마에서 NULL을 허용한 곳은 모두 이유가 있습니다.

| 컬럼 | NULL 허용 이유 |
|---|---|
| TB_CUST.BIZ_REG_NO | 등록 초기에 번호 확인 전일 수 있음 (Day 4) |
| TB_RCV.VNDR_NO | 생산입고(02)에는 구매처가 없음 |
| TB_ITEM.SHELF_LIFE_MM | 원료·포장재는 유효기간을 품목 단위로 관리하지 않음 |

"모름"과 "해당 없음"을 구별해야 하면 NULL 대신 값을 정합니다. 현재 유효 행의 종료일을 9999-12-31로 둔 Day 7 규칙, DW에서 알 수 없는 차원을 -1로 두는 규칙이 같은 생각입니다.

### 3. 제약조건: DB가 지키는 규칙과 사람이 지키는 규칙

PK는 유일성과 존재성, FK는 "가리키는 대상이 실제로 있다", CHECK는 "값이 허용 범위 안에 있다"를 DB가 보장합니다. 애플리케이션이 검증한다고 해도 배치, 데이터 이관, DBA의 수작업 UPDATE는 애플리케이션을 거치지 않습니다. **DB 제약은 모든 입력 경로에 공통으로 걸리는 유일한 검문소**입니다.

운영계 ERP는 성능이나 패키지 사정으로 FK를 꺼 두기도 합니다. 그렇다면 그 규칙은 사라진 것이 아니라 **품질 점검 쿼리로 옮겨 가야** 합니다(Day 12). 공통 스키마에 CHECK 제약이 하나도 없다는 점(WORLD 6절의 의도된 빈틈)도 같은 이야기입니다. 수량 0 이하, 정의되지 않은 상태코드가 들어와도 막을 것이 없습니다.

### 4. 인덱스: 접근 경로가 먼저, 컬럼 목록은 나중

인덱스는 행을 빨리 가리키는 목차이고, INSERT·UPDATE마다 함께 고쳐야 하는 비용이 있습니다. 그래서 "자주 쓰는 컬럼에 다 건다"가 아니라 **주요 조회 화면·배치의 WHERE 절과 조인 조건 목록**에서 출발합니다.

- 선두 컬럼은 등치(=) 조건으로 쓰이는 컬럼, 범위 조건(BETWEEN, >=) 컬럼은 그 뒤에 둡니다. (ITEM_CD, SHIP_DT)는 "이 품목의 3월 출고"에 맞고, 순서를 뒤집으면 3월 전체를 훑은 뒤 품목을 거릅니다.
- FK 컬럼에는 인덱스를 검토합니다. PostgreSQL과 Oracle 모두 FK에 인덱스를 자동으로 만들지 않습니다. Oracle에서는 FK 인덱스가 없으면 부모 행을 삭제하거나 PK를 바꿀 때 자식 테이블 잠금 범위가 커지는 문제가 알려져 있습니다.
- 값이 둘뿐인 USE_YN 같은 컬럼 단독 인덱스는 대개 쓰이지 않습니다.

### 5. 파티셔닝: 큰 테이블을 "지우는 단위"로 나눕니다

파티셔닝은 한 테이블을 여러 물리 조각으로 나누되 SQL에서는 하나처럼 쓰게 하는 기능입니다. 얻는 것은 두 가지입니다. 조회 조건이 파티션 키를 포함하면 해당 조각만 읽고(**파티션 프루닝**), 오래된 데이터는 DELETE가 아니라 조각을 떼어 내는 것(DETACH, DROP)으로 지웁니다.

| 방식 | 나누는 기준 | 어울리는 테이블 | 주의 |
|---|---|---|---|
| 범위 (RANGE) | 날짜 구간 | 출고상세, 일별재고, 전표 | 다음 달 파티션을 미리 만들어야 함 |
| 리스트 (LIST) | 값 목록 | 회사코드별·창고별 데이터 | 값이 늘면 파티션도 추가 |
| 해시 (HASH) | 키의 해시값 | 날짜 조건 없이 키로만 읽는 큰 테이블 | 프루닝은 키 등치 조회에서만, 보관 주기 관리에는 무력 |

파티션 키는 **"가장 자주 거는 조회 조건"과 "보관·삭제 주기"가 같은 컬럼**일 때 가장 잘 맞습니다. 출고는 거의 항상 기간으로 조회하고, 보관 기간도 일자 기준이므로 출고일자가 정답에 가깝습니다.

## 예시

### 요구사항: 월 1억 건 출고상세

한 대리의 요청입니다. "출고상세가 그룹 물류 통합 이후 한 달에 1억 건(가상) 정도로 늘 것 같습니다. 화면은 주로 '이번 달, 이 품목의 출고'를 보고, 출고 기록은 5년 보관 후 지웁니다(가상의 보관 정책)."

공통 스키마의 TB_SHIP_DTL에는 **출고일자가 없습니다.** 일자는 헤더 TB_SHIP에만 있습니다. 파티션 키는 그 테이블의 컬럼이어야 하므로, 출고일자를 상세에 내려 받는 반정규화(Day 5)를 합니다. 출고일자는 확정 후 바뀌지 않아 정합성 부담이 작습니다.

| 한글 논리명 (ENGLISH_PHYSICAL) | 타입 | NULL | 비고 |
|---|---|---|---|
| 출고일자 (SHIP_DT) | DATE | N | 파티션 키. TB_SHIP.SHIP_DT 복제 |
| 출고번호 (SHIP_NO) | VARCHAR(14) | N | PK |
| 출고순번 (SHIP_SEQ) | NUMERIC(4) | N | PK |
| 주문번호·주문순번 (ORD_NO, ORD_SEQ) | VARCHAR(14), NUMERIC(4) | N | FK → TB_ORD_DTL |
| 품목코드 (ITEM_CD) | VARCHAR(10) | N | FK → TB_ITEM |
| 로트번호 (LOT_NO) | VARCHAR(20) | N | FK → TB_LOT |
| 출고수량 (SHIP_QTY) | NUMERIC(10) | N | CHECK > 0 |
| 등록일시·등록자ID (REG_DTM, REG_ID) | TIMESTAMP, VARCHAR(30) | N | 감사 컬럼 |

먼저 흔한 실수를 봅니다. PostgreSQL은 파티션 테이블의 PK·UNIQUE에 파티션 키가 들어 있지 않으면 거부합니다. 각 파티션이 자기 안에서만 유일성을 검사하기 때문입니다.

```sql 의도된 오류 — PK에 파티션 키가 없음
CREATE TABLE tb_ship_dtl_bad (
  ship_no  VARCHAR(14) NOT NULL,
  ship_seq NUMERIC(4)  NOT NULL,
  ship_dt  DATE        NOT NULL,
  PRIMARY KEY (ship_no, ship_seq)
) PARTITION BY RANGE (ship_dt);
```

PK를 (SHIP_NO, SHIP_SEQ, SHIP_DT)로 넓힙니다. 업무 식별자는 여전히 (SHIP_NO, SHIP_SEQ)이고, 한 출고번호의 출고일자는 하나뿐이므로 실질적인 유일성은 같습니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE lab.tb_ship_dtl (                 -- 출고상세 (월 범위 파티션)
  ship_dt   DATE        NOT NULL,
  ship_no   VARCHAR(14) NOT NULL,
  ship_seq  NUMERIC(4)  NOT NULL,
  ord_no    VARCHAR(14) NOT NULL,
  ord_seq   NUMERIC(4)  NOT NULL,
  item_cd   VARCHAR(10) NOT NULL REFERENCES erp.tb_item (item_cd),
  lot_no    VARCHAR(20) NOT NULL REFERENCES erp.tb_lot (lot_no),
  ship_qty  NUMERIC(10) NOT NULL,
  reg_dtm   TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reg_id    VARCHAR(30) NOT NULL DEFAULT CURRENT_USER,
  CONSTRAINT pk_ship_dtl PRIMARY KEY (ship_no, ship_seq, ship_dt),
  CONSTRAINT fk_ship_dtl_01 FOREIGN KEY (ord_no, ord_seq) REFERENCES erp.tb_ord_dtl (ord_no, ord_seq),
  CONSTRAINT ck_ship_dtl_01 CHECK (ship_qty > 0)
) PARTITION BY RANGE (ship_dt);

CREATE TABLE lab.tb_ship_dtl_202603 PARTITION OF lab.tb_ship_dtl
  FOR VALUES FROM (DATE '2026-03-01') TO (DATE '2026-04-01');
CREATE TABLE lab.tb_ship_dtl_202604 PARTITION OF lab.tb_ship_dtl
  FOR VALUES FROM (DATE '2026-04-01') TO (DATE '2026-05-01');

-- 접근 경로 1: "이 품목의 이번 달 출고"  접근 경로 2: 주문상세 → 출고 추적
CREATE INDEX ix_ship_dtl_01 ON lab.tb_ship_dtl (item_cd, ship_dt);
CREATE INDEX ix_ship_dtl_02 ON lab.tb_ship_dtl (ord_no, ord_seq);

INSERT INTO lab.tb_ship_dtl (ship_dt, ship_no, ship_seq, ord_no, ord_seq, item_cd, lot_no, ship_qty)
SELECT s.ship_dt, d.ship_no, d.ship_seq, d.ord_no, d.ord_seq, d.item_cd, d.lot_no, d.ship_qty
  FROM erp.tb_ship s
  JOIN erp.tb_ship_dtl d ON d.ship_no = s.ship_no;

-- 행이 어느 파티션에 들어갔나
SELECT tableoid::regclass AS partition_nm, COUNT(*) AS row_cnt, SUM(ship_qty) AS ship_qty
  FROM lab.tb_ship_dtl
 GROUP BY tableoid
 ORDER BY 1;
```

출고 6행은 모두 3월이라 `lab.tb_ship_dtl_202603`에 6행, 435 BOX가 들어갑니다. 파티션 범위는 `FROM` 포함, `TO` 미포함인 반열림 구간이라 말일이 며칠인지 신경 쓸 필요가 없습니다.

이제 프루닝을 눈으로 확인합니다. 비용 숫자가 아니라 **어떤 파티션을 읽는지**만 봅니다.

```sql
EXPLAIN (COSTS OFF)
SELECT item_cd, SUM(ship_qty)
  FROM lab.tb_ship_dtl
 WHERE ship_dt BETWEEN DATE '2026-03-01' AND DATE '2026-03-31'
   AND item_cd = 'P10001'
 GROUP BY item_cd;
```

실행계획에 `tb_ship_dtl_202603`만 나오고 4월 파티션은 나오지 않습니다. 출고일자 조건을 빼면 두 파티션을 모두 읽으므로, 조회 조건에 **파티션 키가 항상 들어가는지**를 설계 리뷰에서 확인합니다.

범위를 벗어난 행은 들어갈 곳이 없어 거부됩니다. 7월 파티션을 아직 만들지 않았다면 7월 출고는 저장되지 않습니다.

```sql 의도된 오류 — 해당 월 파티션이 없음
INSERT INTO lab.tb_ship_dtl (ship_dt, ship_no, ship_seq, ord_no, ord_seq, item_cd, lot_no, ship_qty)
VALUES (DATE '2026-07-01', 'SH2026070001', 1, 'SO2026040001', 1, 'P10001', 'L260105', 15);
```

해법은 다음 몇 달 치 파티션을 미리 만드는 배치, 또는 DEFAULT 파티션입니다. DEFAULT는 출고를 멈추지 않게 해 주지만, 나중에 그 달 파티션을 만들 때 DEFAULT 안의 해당 행 때문에 생성이 막히거나 검사 비용이 듭니다. 운영계라면 **미리 만드는 배치 + 파티션 부족 알림**을 기본으로 하고, DEFAULT는 사고 대비 안전망으로만 둡니다.

보관 주기가 지난 달은 DELETE 없이 떼어 냅니다.

```sql
ALTER TABLE lab.tb_ship_dtl DETACH PARTITION lab.tb_ship_dtl_202604;
DROP TABLE lab.tb_ship_dtl_202604;

SELECT c.relname AS partition_nm, pg_get_expr(c.relpartbound, c.oid) AS bound
  FROM pg_inherits i
  JOIN pg_class c ON c.oid = i.inhrelid
 WHERE i.inhparent = 'lab.tb_ship_dtl'::regclass;
```

:::note Oracle 차이
계열사 ERP(Oracle)에서는 아래처럼 쓰며, 파티셔닝은 Enterprise Edition의 별도 옵션이므로 라이선스부터 확인합니다. Oracle은 인터벌 파티션으로 새 달 파티션을 자동으로 만들 수 있어 "미리 만드는 배치"가 필요 없습니다. 또 Oracle은 파티션 키가 없는 PK를 **글로벌 인덱스**로 만들 수 있지만, 파티션을 DROP할 때 글로벌 인덱스 유지 비용이 생기므로 로컬 인덱스(파티션마다 따로 만드는 인덱스)를 우선 검토합니다.
:::

```oracle
CREATE TABLE TB_SHIP_DTL (
  SHIP_DT  DATE         NOT NULL,
  SHIP_NO  VARCHAR2(14) NOT NULL,
  SHIP_SEQ NUMBER(4)    NOT NULL,
  ...
  SHIP_QTY NUMBER(10)   NOT NULL CONSTRAINT CK_SHIP_DTL_01 CHECK (SHIP_QTY > 0)
)
PARTITION BY RANGE (SHIP_DT) INTERVAL (NUMTOYMINTERVAL(1, 'MONTH'))
( PARTITION P202603 VALUES LESS THAN (DATE '2026-04-01') );

CREATE INDEX IX_SHIP_DTL_01 ON TB_SHIP_DTL (ITEM_CD, SHIP_DT) LOCAL;
```

### 리스트와 해시는 언제 쓰나

```sql
-- 리스트: 창고별로 운영 주체·보관 정책이 다를 때
CREATE TABLE lab.tb_inv_daily (LIKE erp.tb_inv_daily INCLUDING DEFAULTS) PARTITION BY LIST (wh_cd);
CREATE TABLE lab.tb_inv_daily_w01 PARTITION OF lab.tb_inv_daily FOR VALUES IN ('W01');
CREATE TABLE lab.tb_inv_daily_w02 PARTITION OF lab.tb_inv_daily FOR VALUES IN ('W02');
INSERT INTO lab.tb_inv_daily SELECT * FROM erp.tb_inv_daily;

-- 해시: 날짜 조건 없이 주문번호로만 읽는 큰 테이블을 고르게 나눌 때
CREATE TABLE lab.tb_ord_evt (ord_no VARCHAR(14) NOT NULL, evt_seq NUMERIC(6) NOT NULL,
                             PRIMARY KEY (ord_no, evt_seq)) PARTITION BY HASH (ord_no);
CREATE TABLE lab.tb_ord_evt_h0 PARTITION OF lab.tb_ord_evt FOR VALUES WITH (MODULUS 2, REMAINDER 0);
CREATE TABLE lab.tb_ord_evt_h1 PARTITION OF lab.tb_ord_evt FOR VALUES WITH (MODULUS 2, REMAINDER 1);
INSERT INTO lab.tb_ord_evt SELECT ord_no, 1 FROM erp.tb_ord;
```

일별재고 5행은 전부 W01 파티션에 들어가고, 주문 6건은 해시값에 따라 두 조각에 나뉩니다. 해시는 "고르게 나누기"만 해 줄 뿐 오래된 데이터를 한 번에 떼어 낼 수 없다는 점이 범위 파티션과의 결정적 차이입니다.

## Before / After

**Before: 엑셀 양식을 그대로 옮긴 출고상세**

```text
TB_SHIP_DTL_OLD
  SHIP_NO   VARCHAR(50)   NULL
  SHIP_SEQ  VARCHAR(10)   NULL      -- '1', '01', '001' 이 섞임
  SHIP_DT   VARCHAR(8)    NULL      -- '20260230' 도 들어감
  ITEM_CD   VARCHAR(50)   NULL
  SHIP_QTY  VARCHAR(20)   NULL      -- '1,000', '-5'
  PK 없음, FK 없음, 인덱스 9개 (컬럼마다 하나씩), 파티션 없음
```

결과는 월말 배치의 날짜 변환 실패(일자가 문자), 이중 적재를 모르는 상태(PK 없음), 점점 느려지는 저장(쓰지 않는 인덱스 9개 갱신), 주말 작업이 된 보관 만료 삭제(파티션 없이 DELETE)입니다.

**After: 위 예시의 lab.tb_ship_dtl**

| 항목 | 내용 |
|---|---|
| 타입 | 일자 DATE, 수량 NUMERIC(10), 코드·번호는 표준 길이 |
| NULL | 전 컬럼 NOT NULL |
| 제약 | PK (SHIP_NO, SHIP_SEQ, SHIP_DT), FK 3개, CHECK (SHIP_QTY > 0) |
| 인덱스 | 접근 경로 2개에 맞춘 2개 (ITEM_CD, SHIP_DT), (ORD_NO, ORD_SEQ) |
| 파티션 | SHIP_DT 월 범위. 다음 달 파티션 사전 생성 배치, 보관 만료 월은 DETACH 후 DROP |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| FK를 DB에 걸까 | 입력 경로가 여러 개(화면·배치·이관)면 DB 제약 | 패키지 ERP라 바꿀 수 없으면 품질 점검 쿼리로 대체하고 목록화 |
| CHECK 범위 | 업무가 바뀌어도 안 변하는 규칙(수량 > 0, YN 값)은 CHECK | 바뀔 수 있는 목록(상태코드 값)은 코드 테이블 FK나 점검 쿼리 (Day 9) |
| 인덱스 추가 | 주요 화면·배치의 조건에 등장하고 선택도가 높으면 추가 | 집계·분석 조회면 인덱스 대신 DW·마트로 |
| 파티션 도입 | 보관 주기 삭제가 있거나 조회가 기간 단위로 몰리면 범위 파티션 | 건수가 적거나 조회가 파티션 키와 무관하면 도입하지 않음 (관리 비용만 늘어남) |

## 흔한 실수 3가지

1. **일자·금액을 문자로 두는 실수.** "원천이 문자로 주니까"는 이유가 되지 않습니다. 적재 단계에서 변환하고 실패 행은 오류 테이블로 보냅니다(Day 23). 문자로 두면 변환 실패가 조회 시점으로 미뤄질 뿐입니다.
2. **파티션 키가 빠진 조회.** 파티션을 만들어 놓고 화면이 주문번호만으로 조회하면 모든 파티션을 읽습니다. 파티션 키는 조회 조건 목록을 먼저 보고 정하고, 화면 설계서에 기간 조건을 필수로 적습니다.
3. **인덱스를 "혹시 몰라" 거는 실수.** 쓰지 않는 인덱스는 쓰기 성능과 저장 공간만 잡아먹습니다. 인덱스마다 "어느 화면·배치의 어느 조건용인지"를 테이블정의서에 적고, 설명할 수 없는 인덱스는 지웁니다.

## 셀프 체크 질문

**Q1. 출고상세를 출고일자로 파티셔닝하려는데 출고일자는 헤더에만 있습니다. 어떻게 하시겠습니까?**

:::answer 모범 답안 보기
출고일자를 상세로 내려 받는 반정규화를 제안합니다. 확정 후 바뀌지 않아 어긋날 위험이 작고, 조회가 거의 기간 단위라 프루닝이 되며, 보관 만료를 DETACH로 처리할 수 있습니다. 대신 헤더·상세 출고일자 일치 점검을 품질 규칙에 넣고, 정정이 허용된다면 헤더·상세를 한 트랜잭션으로 고치는 절차를 정합니다. PostgreSQL에서는 PK에 파티션 키가 들어가야 하므로 PK가 (SHIP_NO, SHIP_SEQ, SHIP_DT)가 된다는 점도 테이블정의서에 이유와 함께 적습니다.
:::

**Q2. 개발팀이 "애플리케이션에서 다 검증하니 FK와 CHECK는 필요 없다"고 합니다. 어떻게 답하시겠습니까?**

:::answer 모범 답안 보기
애플리케이션 검증은 화면을 통한 입력만 지킵니다. 배치, 데이터 이관, 인터페이스, DBA 수작업은 애플리케이션을 거치지 않습니다. DB 제약은 모든 경로에 공통으로 걸리는 마지막 검문소이므로 최소한 "업무가 바뀌어도 변하지 않는 규칙"(PK, 수량 > 0, YN 값, 핵심 FK)은 DB에 겁니다. 성능 때문에 FK를 끄는 테이블은 목록을 남기고 같은 규칙을 품질 점검 쿼리로 매일 확인합니다. 규칙을 없애는 것이 아니라 지키는 위치를 옮기는 것입니다.
:::

**Q3. 출고상세에 해시 파티션을 쓰자는 의견이 나왔습니다. 어떤 기준으로 판단하시겠습니까?**

:::answer 모범 답안 보기
두 가지를 묻습니다. 주요 조회가 어떤 조건인가, 그리고 오래된 데이터를 어떻게 지우는가. 출고는 기간 조회가 대부분이고 보관 주기가 일자 기준이므로 범위 파티션이 맞습니다. 해시는 출고번호 등치 조회만 프루닝되고, 기간 조회는 모든 조각을 읽으며, 오래된 달만 떼어 낼 수도 없습니다. 해시는 날짜 조건 없이 키로만 읽고 보관 주기 삭제가 없는 큰 테이블에서 데이터를 고르게 나누고 싶을 때 고릅니다.
:::

## 오늘의 과제

**과제 1.** 위 예시처럼 일별재고를 월 범위 파티션으로 만들어 보세요. 3월·4월 파티션을 만들고 공통 스키마의 일별재고를 넣은 뒤, 파티션별 행 수를 확인합니다. 결과 모양은 `partition_nm, row_cnt` 1행(3월 파티션 5행)입니다. PK는 무엇으로 했는지, 왜 그런지도 적어 보세요.

:::answer 해설 보기
원래 PK (INV_DT, WH_CD, ITEM_CD, LOT_NO)에 파티션 키 INV_DT가 이미 들어 있으므로 그대로 쓸 수 있습니다. 스냅샷 테이블은 일자가 PK 선두인 경우가 많아 파티셔닝과 궁합이 좋습니다.

```sql
CREATE TABLE lab.tb_inv_daily_m (
  inv_dt   DATE        NOT NULL,
  wh_cd    VARCHAR(5)  NOT NULL REFERENCES erp.tb_wh (wh_cd),
  item_cd  VARCHAR(10) NOT NULL REFERENCES erp.tb_item (item_cd),
  lot_no   VARCHAR(20) NOT NULL REFERENCES erp.tb_lot (lot_no),
  inv_qty  NUMERIC(12) NOT NULL CHECK (inv_qty >= 0),
  PRIMARY KEY (inv_dt, wh_cd, item_cd, lot_no)
) PARTITION BY RANGE (inv_dt);
CREATE TABLE lab.tb_inv_daily_m_202603 PARTITION OF lab.tb_inv_daily_m
  FOR VALUES FROM (DATE '2026-03-01') TO (DATE '2026-04-01');
CREATE TABLE lab.tb_inv_daily_m_202604 PARTITION OF lab.tb_inv_daily_m
  FOR VALUES FROM (DATE '2026-04-01') TO (DATE '2026-05-01');
INSERT INTO lab.tb_inv_daily_m SELECT * FROM erp.tb_inv_daily;

SELECT tableoid::regclass AS partition_nm, COUNT(*) AS row_cnt
  FROM lab.tb_inv_daily_m GROUP BY tableoid;
```

재고는 0일 수 있으므로(L250901) CHECK는 `>= 0`입니다. 출고수량(`> 0`)과 다른 이유를 설명할 수 있으면 됩니다.
:::

**과제 2.** 공통 스키마 `erp`의 FK 컬럼 중 **인덱스가 없는 곳**을 카탈로그에서 찾아보세요. 결과 모양은 `table_nm, fk_nm, fk_cols` 목록입니다. 몇 건이 나오는지, 그중 무엇에 인덱스를 먼저 만들지 판단해 봅니다.

:::answer 해설 보기
FK 컬럼 목록이 어떤 인덱스의 선두 컬럼들과 같으면 "인덱스 있음"으로 봅니다. PK가 FK를 선두에 포함하면(TB_ORD_DTL의 ORD_NO) PK 인덱스가 그 역할을 합니다.

```sql
SELECT c.conrelid::regclass AS table_nm, c.conname AS fk_nm,
       (SELECT string_agg(a.attname, ', ' ORDER BY k.ord)
          FROM unnest(c.conkey) WITH ORDINALITY AS k (attnum, ord)
          JOIN pg_attribute a ON a.attrelid = c.conrelid AND a.attnum = k.attnum) AS fk_cols
  FROM pg_constraint c
  JOIN pg_namespace n ON n.oid = c.connamespace
 WHERE c.contype = 'f' AND n.nspname = 'erp'
   AND NOT EXISTS (SELECT 1
                     FROM pg_index i
                    WHERE i.indrelid = c.conrelid
                      AND (i.indkey::int2[])[0:cardinality(c.conkey) - 1] = c.conkey)
 ORDER BY 1, 2;
```

FK 38개 중 29개가 나옵니다(TB_ORD.CUST_NO, TB_SHIP_DTL.LOT_NO 등). 전부 거는 것이 아니라 그 방향으로 실제 조회하는지로 우선순위를 정합니다. 로트별 출고 추적(Day 13)은 품질 사고 때 반드시 쓰이므로 TB_SHIP_DTL.LOT_NO가 앞 순위입니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 테이블정의서 | 컬럼별 타입·길이·NULL 여부(허용 시 사유), 기본값, PK·FK·CHECK 이름과 내용, 반정규화 컬럼의 원천과 동기화 방법. |
| 인덱스정의서 | 인덱스명, 컬럼 순서, 용도(어느 화면·배치의 어느 조건), 유니크 여부. |
| 파티션정의서 (또는 테이블정의서의 물리 속성) | 파티션 방식·키·단위, 파티션 생성 배치, 보관 주기와 삭제 방법, 담당 조직. |
| DB 설계 표준 | 타입 선택 원칙, NULL 정책, 제약조건 명명규칙(PK_, FK_테이블_NN, CK_테이블_NN, IX_테이블_NN). |
| 품질 점검 목록 | DB에 걸지 못한 FK·CHECK 규칙을 점검 쿼리로 옮긴 목록 (Day 12). |

## 참고할 원전

- PostgreSQL 공식 문서 — "Data Types", "Constraints", "Indexes", "Table Partitioning".
- Oracle Database 공식 문서 — "VLDB and Partitioning Guide".
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 모델링 영역: 물리 데이터 모델링.
