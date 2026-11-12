# Day 4. 식별자 설계

## 오늘의 한 줄

식별자는 "이 행이 바로 그 행"임을 시스템이 살아 있는 동안 보장하는 약속입니다. 그래서 업무 의미가 바뀔 수 있는 값에는 그 약속을 맡기지 않는 것이 핵심입니다.

## 왜 중요한가

주문상세의 PK를 (주문번호, 품목코드)로 잡았다고 해 보겠습니다. 어느 날 도매상 대량 주문에 "같은 품목을 증정으로 10 BOX 더" 넣는 요청이 오면 PK 위반으로 저장이 안 됩니다. 현업은 급한 마음에 'P10001F 한빛펜정(증정)' 같은 가짜 품목을 등록하고, 그때부터 재고·출고·원가가 같은 제품을 두 코드로 나눠 집계합니다. PK 하나를 잘못 고른 결과가 마스터 오염과 재고 불일치로 번지는 것입니다. 데이터가 쌓인 뒤의 PK는 바꾸기 가장 어려운 구조입니다.

## 핵심 개념

### 1. 좋은 식별자의 네 가지 조건

쉽게 말하면 식별자는 "겹치지 않고, 군더더기 없고, 바뀌지 않고, 비어 있지 않은" 값이어야 합니다. 정확한 용어로는 유일성, 최소성, 불변성, 존재성입니다.

| 조건 | 뜻 | 한빛제약 예시 |
|---|---|---|
| 유일성 | 모든 행을 구별한다 | ORD_NO는 주문마다 다르다 |
| 최소성 | 빼도 유일하다면 그 컬럼은 군더더기다 | (ORD_NO, ORD_DT)에서 ORD_DT는 군더더기 |
| 불변성 | 한번 정하면 바뀌지 않는다 | 거래처명은 바뀌므로 식별자로 부적합 |
| 존재성 | 반드시 값이 있다 | 사업자등록번호는 등록 초기에 비어 있을 수 있음 |

시니어가 가장 무겁게 보는 것은 **불변성**입니다. 유일성과 존재성은 DB 제약이 지켜 주지만 "이 값이 몇 년 뒤에도 안 바뀔까"는 업무를 알아야만 판단할 수 있습니다. PK가 바뀌면 그 값을 FK로 들고 있는 모든 자식 테이블과 DW 적재 이력까지 같이 고쳐야 합니다.

### 2. 본질 식별자 vs 인조 식별자

**본질 식별자**는 업무에 원래 있는 값으로 행을 구별하는 것입니다(사업자등록번호, 주문번호 + 품목코드 등). **인조 식별자**는 구별만을 위해 시스템이 만든 값입니다(CUST_NO 'C000101', ORD_SEQ 1·2·3).

| 기준 | 본질 식별자가 유리 | 인조 식별자가 유리 |
|---|---|---|
| 값의 안정성 | 업무 규칙상 절대 안 바뀜 | 바뀔 가능성이 조금이라도 있음 |
| 중복 방지 | PK 자체가 업무 중복을 막아 줌 | 별도 UNIQUE 제약으로 막아야 함 |
| 자식 테이블 | 자식이 적고 깊지 않음 | 자식이 많아 FK 전파 폭이 부담 |
| 외부 연계 | 다른 시스템도 그 값으로 말함 | 시스템 내부에서만 쓰임 |

놓치기 쉬운 점이 있습니다. **인조 식별자를 쓰면 본질 식별자는 UNIQUE 제약이나 점검으로 꼭 남겨야 합니다.** 거래처를 CUST_NO로 식별해도 같은 사업자등록번호로 거래처가 두 번 등록되는 것은 막아야 합니다. 인조키만 두고 업무 중복 방지를 잊으면 같은 약국이 C000201, C000257로 두 번 생깁니다. Day 13 MDM에서 다룰 중복 거래처의 시작입니다.

한빛제약은 사업자등록번호를 PK로 쓰지 않습니다. 등록 초기에는 번호 확인 전이라 비어 있을 수 있고(존재성), 한 사업자 아래 배송·청구 단위가 다른 거래처를 나눠 관리할 수 있으며(유일성), 폐업 후 재개업처럼 번호가 바뀌는 경우도 생길 수 있기 때문입니다(불변성). 공통 스키마에서도 BIZ_REG_NO는 NULL을 허용합니다.

### 3. 식별 관계 vs 비식별 관계

**식별 관계**는 부모의 PK가 자식 PK의 일부가 되는 관계입니다. **비식별 관계**는 부모의 PK가 자식의 일반 컬럼(FK)으로만 들어가는 관계입니다.

```text
식별    TB_ORD (PK ORD_NO)
          ||--|<  TB_ORD_DTL (PK ORD_NO + ORD_SEQ)

비식별  TB_ITEM (PK ITEM_CD)
          ||--o<  TB_ORD_DTL (FK ITEM_CD)

비식별  TB_ORD_DTL (PK ORD_NO + ORD_SEQ)
          ||--o<  TB_SHIP_DTL (FK ORD_NO, ORD_SEQ)
```

어느 쪽으로 할지는 아래 질문으로 정합니다.

- 자식이 부모 없이 의미가 있는가? 주문상세는 주문 없이 존재할 수 없습니다. 식별 관계가 자연스럽습니다.
- 자식이 살아 있는 동안 부모가 바뀔 수 있는가? 주문의 거래처는 잘못 입력하면 정정할 수 있습니다. 바뀔 수 있는 부모를 PK에 넣으면 PK를 수정해야 하므로 비식별로 둡니다.
- 자식을 주로 부모 단위로 조회하는가? 주문상세는 거의 항상 주문번호로 읽습니다. PK 선두에 ORD_NO가 있으면 PK 인덱스가 그대로 조회에 쓰입니다.
- 손자, 증손자까지 PK가 계속 길어지는가? 그렇다면 어느 지점에서 끊어야 합니다.

### 4. 복합키의 함정

복합키 자체가 나쁜 것은 아닙니다. 주문상세의 (ORD_NO, ORD_SEQ)는 좋은 복합키입니다. 문제는 아래 네 가지 경우입니다.

**업무 규칙이 바뀌면 깨지는 복합키.** (ORD_NO, ITEM_CD)는 "한 주문에 같은 품목은 한 줄"이라는 규칙을 PK에 박아 넣은 것입니다. 증정, 납기 분할처럼 같은 품목이 두 줄 필요한 요구가 생기면 PK부터 깨집니다.

**자식으로 갈수록 넓어지는 복합키.** 식별 관계를 계속 이으면 손자 테이블의 PK가 4~5개 컬럼이 되고 조인 조건도 그만큼 길어집니다. 조인 조건 하나를 빠뜨리면 행이 불어납니다.

**NULL이 들어올 수 있는 컬럼을 포함한 복합키.** PK 컬럼은 NULL을 허용하지 않으므로 "아직 모르는 값"에 가짜 값('-', '9999')을 넣게 됩니다.

**FK 하나를 걸기 위해 컬럼을 중복하게 만드는 복합키.** 출고상세가 주문상세를 참조하려면 (ORD_NO, ORD_SEQ) 두 컬럼이 모두 필요합니다. 그래서 공통 스키마의 TB_SHIP_DTL은 헤더 TB_SHIP에 이미 ORD_NO가 있는데도 ORD_NO를 또 들고 있습니다. 이 중복은 "헤더와 상세의 ORD_NO가 같아야 한다"는 새 규칙을 만듭니다.

### 5. 의미를 담은 번호(스마트 키)는 표시용으로만

공통 스키마의 주문번호 'SO2026030001'은 SO + 연월(YYYYMM) + 일련번호 4자리입니다. 사람이 보기 편하고 번호만으로 월을 짐작할 수 있습니다. 하지만 주문일자를 정정해도 번호는 바꾸지 않습니다. 번호 속 연월은 "채번 당시 연월"일 뿐이며 **업무 로직이 번호를 잘라서 월로 쓰면 안 됩니다.**

샘플 거래처번호도 C0001xx는 병원, C0002xx는 약국처럼 보입니다. 우연히 보이는 패턴이지 규칙이 아닙니다. 번호에 유형을 담으면 유형이 재분류될 때 번호를 바꿔야 하는 문제가 생깁니다. 유형은 CUST_TP_CD로만 판단합니다.

## 예시

### 추가 요구사항

영업기획팀이 요구사항을 하나 더 줬습니다.

> "도매상 대량 주문에는 같은 품목을 증정(무상)으로 추가할 수 있다. 증정분도 출고·재고에서는 같은 제품으로 관리한다."

### 주문상세 PK 후보 비교

| 후보 | PK | 증정 라인 저장 | 자식(출고상세) FK | 판정 |
|---|---|---|---|---|
| A | (ORD_NO, ITEM_CD) | 불가 (PK 중복) | (ORD_NO, ITEM_CD) | 탈락: 업무 규칙이 PK에 묶임 |
| B | (ORD_NO, ORD_SEQ) | 가능 | (ORD_NO, ORD_SEQ) | **채택** (공통 스키마 구조) |
| C | ORD_DTL_NO (단일 일련번호) | 가능 | ORD_DTL_NO 하나 | 대안: 참조하는 자식이 많고 깊을 때 |

B를 고른 이유는 세 가지입니다. 주문상세는 거의 항상 주문 단위로 조회하므로 ORD_NO 선두 PK가 유리합니다. 주문상세를 참조하는 자식이 출고상세 정도로 많지 않습니다. ORD_SEQ는 화면의 줄 번호와 일치해서 현업과 대화하기 쉽습니다.

### 후보 A가 실제로 깨지는 모습

실습은 `lab` 스키마에 복사본을 만들어 진행합니다. 운영계(`erp`) 테이블 구조는 바꾸지 않습니다.

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

-- 후보 A: (주문번호, 품목코드)를 PK로 잡은 주문상세
CREATE TABLE lab.tb_ord_dtl_a (
  ord_no   VARCHAR(14) NOT NULL,
  item_cd  VARCHAR(10) NOT NULL,
  ord_qty  NUMERIC(10) NOT NULL,
  uprc     NUMERIC(15) NOT NULL,
  ord_amt  NUMERIC(15) NOT NULL,
  PRIMARY KEY (ord_no, item_cd)
);
INSERT INTO lab.tb_ord_dtl_a
SELECT ord_no, item_cd, ord_qty, uprc, ord_amt FROM erp.tb_ord_dtl;
```

```sql 의도된 오류 — PK 위반
-- 바른팜유통 주문(SO2026030003)에 한빛펜정 증정 10 BOX 추가 시도
INSERT INTO lab.tb_ord_dtl_a VALUES ('SO2026030003', 'P10001', 10, 0, 0);
```

PK 위반(duplicate key)으로 실패합니다. 현업이 가짜 품목코드를 만들기 시작하는 지점이 바로 여기입니다.

### 후보 B: PK는 구별만, 업무 규칙은 UNIQUE로

| 한글 논리명 (ENGLISH_PHYSICAL) | 타입 | PK/FK | 비고 |
|---|---|---|---|
| 주문번호 (ORD_NO) | VARCHAR(14) | PK, FK | TB_ORD 식별 관계 |
| 주문순번 (ORD_SEQ) | NUMERIC(4) | PK | 주문 안에서 1부터 |
| 품목코드 (ITEM_CD) | VARCHAR(10) | FK | TB_ITEM 비식별 관계 |
| 주문상세유형코드 (ORD_DTL_TP_CD) | VARCHAR(2) | | 01 일반, 02 증정 (신규) |
| 주문수량 (ORD_QTY) | NUMERIC(10) | | > 0 |
| 단가 (UPRC) | NUMERIC(15) | | 증정이면 0 |
| 주문금액 (ORD_AMT) | NUMERIC(15) | | |

```sql
-- 공통 스키마 구조(B안)를 복사하고 주문상세유형코드를 추가
CREATE TABLE lab.tb_ord_dtl (LIKE erp.tb_ord_dtl INCLUDING ALL);
INSERT INTO lab.tb_ord_dtl SELECT * FROM erp.tb_ord_dtl;

ALTER TABLE lab.tb_ord_dtl ADD COLUMN ord_dtl_tp_cd VARCHAR(2) NOT NULL DEFAULT '01';
ALTER TABLE lab.tb_ord_dtl ADD CONSTRAINT ck_tb_ord_dtl_02 CHECK (ord_dtl_tp_cd IN ('01', '02'));
-- 업무 규칙: 한 주문 안에서 같은 품목은 일반 1줄, 증정 1줄까지
ALTER TABLE lab.tb_ord_dtl ADD CONSTRAINT uk_tb_ord_dtl_01 UNIQUE (ord_no, item_cd, ord_dtl_tp_cd);
ALTER TABLE lab.tb_ord_dtl ADD CONSTRAINT fk_tb_ord_dtl_01 FOREIGN KEY (ord_no) REFERENCES erp.tb_ord (ord_no);

INSERT INTO lab.tb_ord_dtl (ord_no, ord_seq, item_cd, ord_qty, uprc, ord_amt, ord_dtl_tp_cd)
VALUES ('SO2026030003', 3, 'P10001', 10, 0, 0, '02');

SELECT * FROM lab.tb_ord_dtl WHERE ord_no = 'SO2026030003' ORDER BY ord_seq;
```

:::note Oracle 차이
Oracle에는 `CREATE TABLE ... (LIKE ...)`가 없습니다. `CREATE TABLE ... AS SELECT * FROM ... WHERE 1 = 0` 후 PK를 따로 추가합니다. 컬럼 추가는 `ALTER TABLE ... ADD (ORD_DTL_TP_CD VARCHAR2(2) DEFAULT '01' NOT NULL)` 형식입니다.
:::

| 주문번호 (ORD_NO) | 주문순번 (ORD_SEQ) | 품목코드 (ITEM_CD) | 주문상세유형 (ORD_DTL_TP_CD) | 주문수량 (ORD_QTY) | 단가 (UPRC) | 주문금액 (ORD_AMT) |
|---|---|---|---|---|---|---|
| SO2026030003 | 1 | P10001 | 01 일반 | 300 | 3,200 | 960,000 |
| SO2026030003 | 2 | P10002 | 01 일반 | 100 | 12,000 | 1,200,000 |
| SO2026030003 | 3 | P10001 | 02 증정 | 10 | 0 | 0 |

PK는 행을 구별하는 역할만 하고, "같은 품목 중복 금지"는 UNIQUE 제약으로 따로 표현했습니다. 나중에 "납기 분할 때문에 일반 라인도 두 줄 허용"으로 규칙이 바뀌어도 UNIQUE 제약만 조정하면 되고, PK와 자식 테이블은 손대지 않습니다.

### 순번 채번

```sql
-- 주문 헤더 행을 잠가 같은 주문에 동시에 줄을 추가하는 경우를 막고 다음 순번을 구함
BEGIN;
SELECT ord_no FROM erp.tb_ord WHERE ord_no = 'SO2026030003' FOR UPDATE;
SELECT COALESCE(MAX(ord_seq), 0) + 1 AS next_seq
  FROM lab.tb_ord_dtl
 WHERE ord_no = 'SO2026030003';
COMMIT;
```

주문 하나를 여러 사람이 동시에 고치는 일은 드물기 때문에 헤더 잠금 방식이 단순하고 충분합니다. 주문번호처럼 전사에서 동시에 채번하는 값은 시퀀스나 채번 테이블을 씁니다.

### 출고상세의 PK는 왜 (ORD_NO, ORD_SEQ)가 아닌가

출고상세가 주문상세를 참조하니 PK도 (ORD_NO, ORD_SEQ)로 하면 되지 않을까요? 공통 샘플이 답을 보여 줍니다.

```sql
-- 한 주문상세 줄이 여러 로트로 나뉘어 출고된 경우
SELECT sd.ship_no, sd.ship_seq, sd.ord_no, sd.ord_seq, sd.item_cd, sd.lot_no, sd.ship_qty
  FROM erp.tb_ship_dtl sd
 WHERE sd.ord_no = 'SO2026030003'
 ORDER BY sd.ship_seq;
```

SO2026030003의 1번 줄(300 BOX)이 로트 L250901 200 BOX와 L260105 100 BOX, 두 행으로 나갔습니다. 출고는 출고번호로 식별되는 독립된 물류 사건이고, 한 주문상세가 여러 출고상세 행이 될 수 있으므로 출고상세는 (SHIP_NO, SHIP_SEQ)를 PK로 하고 주문상세는 비식별 FK로 참조합니다.

복합 FK 때문에 생긴 "헤더와 상세의 ORD_NO 일치" 규칙과 증정 라인의 출고 잔량은 아래처럼 점검합니다.

```sql
-- 출고 헤더와 상세의 주문번호가 다른 행 (0건이어야 정상)
SELECT s.ship_no, s.ord_no AS hdr_ord_no, d.ship_seq, d.ord_no AS dtl_ord_no
  FROM erp.tb_ship s
  JOIN erp.tb_ship_dtl d ON d.ship_no = s.ship_no
 WHERE d.ord_no <> s.ord_no;

-- 주문상세 줄별 미출고 잔량 (lab 주문상세 기준)
SELECT od.ord_no, od.ord_seq, od.item_cd, od.ord_dtl_tp_cd, od.ord_qty,
       COALESCE(SUM(sd.ship_qty), 0)              AS ship_qty,
       od.ord_qty - COALESCE(SUM(sd.ship_qty), 0) AS remain_qty
  FROM lab.tb_ord_dtl od
  LEFT JOIN erp.tb_ship_dtl sd ON sd.ord_no = od.ord_no AND sd.ord_seq = od.ord_seq
 WHERE od.ord_no = 'SO2026030003'
 GROUP BY od.ord_no, od.ord_seq, od.item_cd, od.ord_dtl_tp_cd, od.ord_qty
 ORDER BY od.ord_seq;
```

잔량은 1번 줄 0, 2번 줄 0, 3번(증정) 줄 10입니다. 주문 단위가 아니라 **주문상세 줄 단위로 출고를 연결**했기 때문에 같은 P10001이라도 일반분과 증정분의 출고를 따로 추적할 수 있습니다.

### 본질 식별자와 스마트 키 점검

```sql
-- 인조키를 써도 본질 식별자 중복은 점검해야 함 (0건이어야 정상)
SELECT biz_reg_no, COUNT(*) AS cust_cnt, string_agg(cust_no, ',') AS cust_nos
  FROM erp.tb_cust
 WHERE biz_reg_no IS NOT NULL
 GROUP BY biz_reg_no
HAVING COUNT(*) > 1;

-- 번호 속 연월과 실제 주문일자가 어긋난 주문: 일치하더라도 로직에 쓰지 않음
SELECT ord_no, ord_dt
  FROM erp.tb_ord
 WHERE SUBSTR(ord_no, 3, 6) <> TO_CHAR(ord_dt, 'YYYYMM');
```

두 번째 쿼리는 품질 점검용입니다. 지금은 0건이지만 일자 정정이 한 번이라도 일어나면 어긋납니다. 그래서 월별 집계는 반드시 ORD_DT로 합니다.

## Before / After

**Before: 업무 규칙을 PK에 묶고, 식별 관계를 끝까지 이어 간 설계**

```text
TB_ORD_DTL   PK (ORD_NO, ITEM_CD)
TB_SHIP_DTL  PK (ORD_NO, ITEM_CD, SHIP_NO, SHIP_SEQ)
```

| 무슨 일이 생기나 | 결과 |
|---|---|
| 증정 라인을 넣을 수 없음 | 현업이 'P10001F 한빛펜정(증정)' 가짜 품목 등록 |
| 같은 제품이 두 품목코드로 존재 | 재고·출고·원가가 둘로 쪼개짐, DW 품목 차원 오염 |
| 출고상세 PK가 4개 컬럼 | 조인 조건이 길어지고, 하나 빠뜨리면 행이 불어남 |
| 품목코드 정정이 PK 수정이 됨 | 출고상세까지 연쇄 수정 필요 |

**After: PK는 구별만, 업무 규칙은 UNIQUE와 코드로**

```text
TB_ORD_DTL   PK (ORD_NO, ORD_SEQ)
             UK (ORD_NO, ITEM_CD, ORD_DTL_TP_CD)
TB_SHIP_DTL  PK (SHIP_NO, SHIP_SEQ)
             FK (ORD_NO, ORD_SEQ) -> TB_ORD_DTL
```

출고상세는 출고 헤더와 식별 관계, 주문상세와는 비식별 관계로 끊었습니다. 품목코드를 잘못 넣었다면 일반 컬럼 UPDATE로 고치면 됩니다.

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 본질 vs 인조 | 값이 업무 규정상 바뀌지 않고, 외부와 같은 값으로 소통하면 본질 식별자 | 조금이라도 바뀔 수 있거나 늦게 확정되면 인조 식별자 + 본질 값은 UNIQUE·점검 |
| 식별 vs 비식별 | 자식이 부모 없이 무의미하고 주로 부모 단위로 조회하면 식별 (주문 → 주문상세) | 자식이 독립된 업무 사건이거나 부모가 바뀔 수 있으면 비식별 (주문상세 → 출고상세) |
| 복합키 유지 vs 단일 일련번호 | 자식이 적고 계층이 2단계 정도면 복합키 (ORD_NO, ORD_SEQ) | 참조하는 자식이 많고(반품, 세금계산서, 수금배분…) 3단계 이상 깊어지면 단일 일련번호 |
| 업무 중복 방지 | 규칙이 안정적이면 UNIQUE 제약으로 DB가 강제 | 규칙이 자주 바뀌면 애플리케이션 검증 + 품질 점검 쿼리 |
| 스마트 키 | 사람이 읽기 위한 표시용이면 허용 | 번호를 잘라서 로직에 쓰는 순간 금지 |

DW 관점도 같이 봅니다. DW는 운영계 PK를 **자연키(natural key)** 로 받아 서로게이트 키(_SK)와 매핑합니다(Day 23). 운영계 PK가 바뀌면 DW는 "같은 대상인데 키가 달라진" 상황을 처리해야 합니다. 운영계 식별자의 불변성이 곧 DW 품질입니다.

## 흔한 실수 3가지

1. **"한 주문에 같은 품목은 한 줄"을 PK로 강제하는 실수.** 규칙을 지키고 싶은 마음은 맞지만 PK에 넣으면 규칙이 바뀔 때 구조를 바꿔야 합니다. 규칙은 UNIQUE 제약이나 검증 로직으로 표현합니다.
2. **인조키를 도입하고 본질 식별자의 중복 방지를 잊는 실수.** 거래처를 CUST_NO로만 식별하고 사업자등록번호 중복을 점검하지 않으면 같은 약국이 두 번 등록됩니다. 인조키는 중복을 막아 주지 않습니다.
3. **번호에 의미를 담고 그 의미를 로직에 쓰는 실수.** `SUBSTR(ORD_NO, 3, 6)`으로 주문월을 구하거나 거래처번호 앞자리로 유형을 판단하면, 일자 정정이나 유형 재분류 때 데이터와 번호가 어긋납니다.

## 셀프 체크 질문

**Q1. 주문상세 PK로 (ORD_NO, ITEM_CD) 대신 (ORD_NO, ORD_SEQ)를 고른 이유를 설명하고, 그래도 같은 품목 중복을 막고 싶다면 어떻게 하겠습니까?**

:::answer 모범 답안 보기
(ORD_NO, ITEM_CD)는 "한 주문에 같은 품목은 한 줄"이라는 업무 규칙을 PK에 묶습니다. 증정이나 납기 분할처럼 같은 품목이 두 줄 필요한 요구가 생기면 PK부터 깨지고, 현업은 가짜 품목코드로 우회합니다. (ORD_NO, ORD_SEQ)는 행을 구별하는 역할만 하므로 업무 규칙이 바뀌어도 안정적입니다. 중복을 막고 싶다면 UNIQUE (ORD_NO, ITEM_CD, ORD_DTL_TP_CD)처럼 규칙을 별도 제약으로 표현합니다. 규칙이 바뀌면 제약만 조정하고 PK와 자식 테이블은 그대로 둡니다.
:::

**Q2. 출고상세가 주문상세를 참조하는데, 출고상세 PK를 (ORD_NO, ORD_SEQ)로 하지 않은 이유는 무엇입니까?**

:::answer 모범 답안 보기
주문상세 1줄이 여러 출고상세 행이 될 수 있기 때문입니다. 공통 샘플에서 SO2026030003의 1번 줄은 로트 L250901과 L260105로 나뉘어 두 행으로 출고됐고, 부분 출고라면 출고번호 자체도 여러 개가 됩니다. 또 출고는 출고번호로 식별되는 독립된 물류 사건이라서 출고 헤더와 식별 관계를 맺는 것이 자연스럽습니다. 그래서 PK는 (SHIP_NO, SHIP_SEQ), 주문상세는 비식별 FK로 참조합니다. 대가로 헤더와 상세에 ORD_NO가 중복되므로 둘이 일치하는지 점검 쿼리로 지킵니다.
:::

**Q3. 거래처 PK를 사업자등록번호로 하자는 의견이 나왔습니다. 어떻게 판단하겠습니까?**

:::answer 모범 답안 보기
식별자 조건 중 존재성, 유일성, 불변성을 하나씩 확인합니다. 등록 초기에는 번호 확인 전이라 비어 있을 수 있고, 한 사업자 아래 배송·청구 단위가 다른 거래처를 나눠 관리할 수 있으며, 폐업 후 재개업처럼 번호가 바뀌는 경우도 생길 수 있습니다. 하나라도 걸리면 PK로 쓰지 않습니다. 대신 인조 식별자 CUST_NO를 PK로 두고, 사업자등록번호는 중복 점검 대상(규칙이 확정되면 UNIQUE 제약)으로 남깁니다. 그룹 MDM에서 계열사 거래처를 통합할 때 사업자등록번호가 매칭 키로 쓰이므로 값 자체의 품질 관리는 오히려 더 엄격해야 합니다.
:::

## 오늘의 과제

**과제 1.** 주문상세를 참조하는 테이블이 반품상세, 세금계산서상세 등으로 늘어난다고 가정하고 후보 C(단일 일련번호)를 만들어 보세요. 조건은 세 가지입니다. PK는 자동 증가하는 `ord_dtl_no` 하나, 기존 (ord_no, ord_seq)는 UNIQUE로 유지, 업무 규칙 UNIQUE (ord_no, item_cd, ord_dtl_tp_cd)도 유지. `lab.tb_ord_dtl`의 9행(증정 포함)을 옮긴 뒤 `ord_dtl_no, ord_no, ord_seq, item_cd, ord_dtl_tp_cd`를 조회하면 9행이 나와야 합니다.

:::answer 해설 보기
단일 일련번호를 PK로 쓰더라도 원래의 자연키 (ord_no, ord_seq)는 UNIQUE로 남겨야 합니다. 그래야 운영계와 DW가 같은 줄을 같은 키로 부를 수 있고, 일련번호가 중복 행을 숨기지 않습니다.

```sql
CREATE TABLE lab.tb_ord_dtl_c (
  ord_dtl_no    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  ord_no        VARCHAR(14) NOT NULL REFERENCES erp.tb_ord (ord_no),
  ord_seq       NUMERIC(4)  NOT NULL,
  item_cd       VARCHAR(10) NOT NULL REFERENCES erp.tb_item (item_cd),
  ord_dtl_tp_cd VARCHAR(2)  NOT NULL DEFAULT '01',
  ord_qty       NUMERIC(10) NOT NULL,
  uprc          NUMERIC(15) NOT NULL,
  ord_amt       NUMERIC(15) NOT NULL,
  CONSTRAINT uk_tb_ord_dtl_c_01 UNIQUE (ord_no, ord_seq),
  CONSTRAINT uk_tb_ord_dtl_c_02 UNIQUE (ord_no, item_cd, ord_dtl_tp_cd)
);

INSERT INTO lab.tb_ord_dtl_c (ord_no, ord_seq, item_cd, ord_dtl_tp_cd, ord_qty, uprc, ord_amt)
SELECT ord_no, ord_seq, item_cd, ord_dtl_tp_cd, ord_qty, uprc, ord_amt
  FROM lab.tb_ord_dtl
 ORDER BY ord_no, ord_seq;

SELECT ord_dtl_no, ord_no, ord_seq, item_cd, ord_dtl_tp_cd
  FROM lab.tb_ord_dtl_c
 ORDER BY ord_dtl_no;
```

얻는 것은 자식 테이블이 컬럼 하나로 참조한다는 점, 잃는 것은 키만 보고 어느 주문의 몇 번째 줄인지 알 수 없다는 점과 이관·병합 시 일련번호 재매핑 부담입니다. 자식 수와 깊이를 기준으로 고릅니다.
:::

:::note Oracle 차이
`GENERATED ALWAYS AS IDENTITY`는 Oracle 12c부터 지원합니다. 그 이전 버전이면 시퀀스(`CREATE SEQUENCE`)와 `시퀀스명.NEXTVAL`을 씁니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 논리 ERD | 식별 관계는 실선, 비식별 관계는 점선(도구 관례에 따름)으로 구분하고 PK를 표시합니다. |
| 엔터티정의서 | 엔터티별 "식별자와 선택 이유" 한 줄. 예: "주문상세: (주문번호, 주문순번). 같은 품목 복수 라인 허용 위해 품목코드 제외." |
| 테이블정의서 | PK·UK·FK 제약 이름과 컬럼 구성(uk_tb_ord_dtl_01 등), 순번 채번 방식(헤더 잠금 후 MAX+1). |
| 채번 규칙서 | 주문번호 'SO' + YYYYMM + 4자리, 출고번호 'SH' + YYYYMM + 4자리. "번호 속 연월은 로직에 쓰지 않음"을 명시합니다. |
| 품질 규칙 목록 | 출고 헤더·상세 주문번호 일치, 사업자등록번호 중복, 번호 연월과 일자 불일치 점검 쿼리. |
| 매핑정의서 (DW) | 운영계 자연키 (ORD_NO, ORD_SEQ)를 DW 팩트의 어떤 컬럼으로 받고, 차원 SK와 어떻게 매핑하는지. |

## 참고할 원전

- Graeme Simsion, Graham Witt, "Data Modeling Essentials", 3rd ed. (Morgan Kaufmann, 2005) — 기본키 선택과 식별(identity)을 다루는 장.
- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 3 "Retail Sales": 자연키와 서로게이트 키를 구분하는 이유.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드"(DAP·DAsP 공통 교재) — 데이터 모델링 과목: 식별자 도출, 식별·비식별 관계.
