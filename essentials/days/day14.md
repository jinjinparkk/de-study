# Day 14. Week 1~2 종합 실습

## 오늘의 한 줄

설계는 기법을 하나씩 적용하는 일이 아니라 **요구사항 문장 하나하나를 엔터티·키·제약·코드·품질 규칙으로 번역하고, 그 결정과 이유를 남기는 일**입니다. 오늘은 새 요구사항 하나를 Week 1~2의 결정을 재사용해 끝까지 설계하고, 리뷰 체크리스트로 스스로 검증합니다.

## 왜 중요한가

설계 리뷰에서 "반품 수량이 출고 수량보다 크면 어떻게 막나요?"에 "개발할 때 처리하겠습니다"라고 답하면, 그 규칙은 아무 산출물에도 남지 않고 결국 아무도 지키지 않습니다. Day 1~13의 기법은 각각 알아도, 하나의 설계 안에서 서로 맞물리게 결정하지 않으면 테이블정의서는 그럴듯하지만 운영 첫 달에 데이터가 깨집니다.

## 핵심 개념

### 1. 요구사항 문장을 "결정"으로 쪼갭니다

요구사항 한 문장에는 보통 여러 종류의 결정이 숨어 있습니다. "약국은 출고받은 제품을 사유와 함께 반품할 수 있다"는 엔터티(반품), 관계(출고상세와의 연결), 코드(반품사유), 제약(반품 수량 범위), 품질 규칙(누적 반품 ≤ 출고)을 모두 담고 있습니다. 문장을 읽을 때마다 **"이 문장은 무엇을 만들라고 하는가"**를 다섯 칸(엔터티·속성·관계·제약·규칙)으로 나눠 적는 습관이 설계 누락을 막습니다(Day 3).

### 2. 결정마다 근거 Day를 붙입니다

새로 고민하지 않아도 되는 결정이 대부분입니다. 식별자는 Day 4, 이력은 Day 7의 선분 규칙, 타입·NULL은 Day 8, 코드는 Day 9, 이름은 Day 10의 표준을 그대로 씁니다. 이미 정한 원칙을 다시 논쟁하지 않는 것이 설계 속도이자 일관성입니다. 진짜 고민은 **원칙끼리 부딪히는 지점**에만 씁니다. 오늘 예시에서는 "반품상세에 로트번호를 둘 것인가(조회 편의) vs 출고상세에서 가져올 것인가(정합성)"가 그런 지점입니다.

### 3. 리뷰 체크리스트는 자동 점검과 사람 판단으로 나눕니다

PK 누락, 인덱스 없는 FK, 설명 없는 컬럼, 표준 미등록 단어(Day 10)는 카탈로그 쿼리로 자동 점검할 수 있습니다. 반면 "이 관계가 업무와 맞나", "이 반정규화의 정합성 수단은 무엇인가"는 사람이 판단해야 합니다. 자동 점검을 먼저 돌려 기계적인 지적을 없애고, 리뷰 회의 시간은 판단이 필요한 질문에만 씁니다.

## 예시

### 요구사항 (한빛제약 영업기획팀 정 과장 + 한빛케미칼 QA)

> "약국·병원은 출고받은 제품을 반품할 수 있다. 반품은 접수 → 승인 → 입고완료 순으로 진행되며 반려될 수 있다. 반품 라인은 반드시 원래 출고 라인을 가리켜야 하고, 같은 출고 라인에 대한 반품 수량 합계는 출고 수량을 넘을 수 없다. 반품 사유는 정해진 목록에서 고른다. 회수 대응을 위해 반품된 로트를 추적할 수 있어야 하며, 반품 승인 상태 변경은 누가 왜 했는지 남아야 한다. 영업실적은 주문금액에서 반품금액을 뺀 순매출로도 본다."

### 요구사항 → 설계 결정

| 요구사항 조각 | 결정 | 근거 |
|---|---|---|
| 반품이 있다, 헤더·라인 | 반품(TB_RTN) / 반품상세(TB_RTN_DTL) 헤더-상세 | Day 2, 3 |
| 반품번호 | RTN_NO = 'RT' + 연월 + 4자리, PK. 상세는 (RTN_NO, RTN_SEQ) 식별 관계 | Day 4 |
| 원래 출고 라인을 가리킴 | 반품상세 → 출고상세 (SHIP_NO, SHIP_SEQ) 비식별 FK, NOT NULL | Day 3, 4 |
| 반품 로트 추적 | 로트·품목은 **저장하지 않고** 출고상세에서 가져옴 (아래 판단) | Day 5 |
| 진행 상태, 반려 | 반품상태 개별 코드 테이블 + 재고반영여부 속성 | Day 9 |
| 사유 목록 | 반품사유코드 공통코드 (RTN_RSN_CD) | Day 9 |
| 반품 합계 ≤ 출고 | 행 간 규칙이라 CHECK 불가 → 등록 절차 + 품질 규칙 | Day 8, 12 |
| 상태 변경 이력 | 감사 추적(사유·사용자 필수) | Day 12 |
| 순매출 | 반품금액 = 반품수량 × 원 주문단가. 저장하지 않고 계산 | Day 5 |
| 이름 | 반품(RTN), 사유(RSN)는 표준단어 신청 | Day 10 |
| 규모 | 반품은 출고보다 훨씬 적다고 가정 → 파티션 없음 | Day 8 |

"사유(RSN)"는 Day 12의 감사 추적 컬럼 CHG_RSN에서 이미 쓰였지만 표준 약어표에 없습니다. 이번에 함께 신청합니다. 이런 식으로 **앞선 산출물의 빈틈이 다음 설계에서 드러나는 것**이 종합 실습의 가치입니다.

### 판단이 필요한 지점: 반품상세에 로트번호를 둘까

| 안 | 장점 | 단점 |
|---|---|---|
| A. RTN_DTL에 LOT_NO, ITEM_CD 저장 | 로트별 반품 조회가 조인 없이 빠름 | 출고상세와 다른 로트가 들어갈 수 있음. 정합성 점검 필요 |
| B. 저장하지 않고 출고상세 FK로 가져옴 | 구조적으로 어긋날 수 없음 | 로트별 조회 때 출고상세 조인 필요 |

반품은 건수가 적고 출고상세는 PK로 조인되므로 조인 비용이 작습니다. **B안을 택합니다.** 반대로 반품이 많고 로트별 반품 조회가 핵심 화면이라면 A안 + 정합성 점검 규칙(Day 12의 DQ07과 같은 형태)을 택할 수 있습니다. 반품 시 다른 로트로 교환해 주는 업무가 생긴다면 그때는 "교환 출고"라는 별도 거래로 설계합니다.

### 논리 ERD

```text
TB_CUST ||--o< TB_ORD ||--|< TB_ORD_DTL ||--o< TB_SHIP_DTL
TB_SHIP_DTL >o--|| TB_LOT                 로트는 출고상세에만
TB_CUST ||--o< TB_RTN ||--|< TB_RTN_DTL   반품 헤더-상세
TB_SHIP_DTL ||--o< TB_RTN_DTL             원 출고 라인 참조
TB_RTN_STAT ||--o< TB_RTN                 반품상태 (개별 코드)
RTN_RSN_CD ..... TB_RTN_DTL               반품사유 (공통코드)
```

### 물리 테이블정의서

반품상세 (TB_RTN_DTL)

| 한글 논리명 (ENGLISH_PHYSICAL) | 타입 | NULL | 키·제약 | 비고 |
|---|---|---|---|---|
| 반품번호 (RTN_NO) | VARCHAR(14) | N | PK, FK → TB_RTN | 번호V14 |
| 반품순번 (RTN_SEQ) | NUMERIC(4) | N | PK | 순번N4 |
| 출고번호 (SHIP_NO) | VARCHAR(14) | N | FK → TB_SHIP_DTL | 번호V14 |
| 출고순번 (SHIP_SEQ) | NUMERIC(4) | N | FK → TB_SHIP_DTL | 순번N4 |
| 반품수량 (RTN_QTY) | NUMERIC(10) | N | CHECK > 0 | 수량N10. 누적 ≤ 출고수량은 품질 규칙 |
| 반품사유코드 (RTN_RSN_CD) | VARCHAR(2) | N | 공통코드 RTN_RSN_CD | 01 유효기한 임박, 02 파손, 03 오배송 |
| 등록일시·등록자ID (REG_DTM, REG_ID) | TIMESTAMP, VARCHAR(30) | N | | 감사 컬럼 |

인덱스: IX_RTN_DTL_01 (SHIP_NO, SHIP_SEQ) — 출고 라인별 누적 반품 계산과 로트 추적용. 반품(TB_RTN)은 RTN_NO, RTN_DT, CUST_NO(FK), RTN_STAT_CD(FK), 감사 컬럼으로 구성하고 IX_RTN_01 (CUST_NO, RTN_DT)를 둡니다.

### 물리 DDL

```sql
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE lab.tb_rtn_stat (                 -- 반품상태 (개별 코드)
  rtn_stat_cd  VARCHAR(2)  PRIMARY KEY,
  rtn_stat_nm  VARCHAR(30) NOT NULL,
  step_seq     NUMERIC(2)  NOT NULL,
  inv_aply_yn  CHAR(1)     NOT NULL CHECK (inv_aply_yn IN ('Y', 'N'))   -- 재고·순매출 반영 대상
);
INSERT INTO lab.tb_rtn_stat VALUES
 ('10', '접수', 1, 'N'), ('20', '승인', 2, 'N'), ('30', '입고완료', 3, 'Y'), ('90', '반려', 9, 'N');

CREATE TABLE lab.tb_rtn (                      -- 반품
  rtn_no       VARCHAR(14) PRIMARY KEY,
  rtn_dt       DATE        NOT NULL,
  cust_no      VARCHAR(10) NOT NULL REFERENCES erp.tb_cust (cust_no),
  rtn_stat_cd  VARCHAR(2)  NOT NULL REFERENCES lab.tb_rtn_stat (rtn_stat_cd),
  reg_dtm      TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reg_id       VARCHAR(30) NOT NULL DEFAULT CURRENT_USER,
  upd_dtm      TIMESTAMP,
  upd_id       VARCHAR(30)
);
CREATE INDEX ix_rtn_01 ON lab.tb_rtn (cust_no, rtn_dt);

CREATE TABLE lab.tb_rtn_dtl (                  -- 반품상세
  rtn_no      VARCHAR(14) NOT NULL REFERENCES lab.tb_rtn (rtn_no),
  rtn_seq     NUMERIC(4)  NOT NULL,
  ship_no     VARCHAR(14) NOT NULL,
  ship_seq    NUMERIC(4)  NOT NULL,
  rtn_qty     NUMERIC(10) NOT NULL CONSTRAINT ck_rtn_dtl_01 CHECK (rtn_qty > 0),
  rtn_rsn_cd  VARCHAR(2)  NOT NULL,
  reg_dtm     TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  reg_id      VARCHAR(30) NOT NULL DEFAULT CURRENT_USER,
  CONSTRAINT pk_rtn_dtl PRIMARY KEY (rtn_no, rtn_seq),
  CONSTRAINT fk_rtn_dtl_01 FOREIGN KEY (ship_no, ship_seq) REFERENCES erp.tb_ship_dtl (ship_no, ship_seq)
);

COMMENT ON TABLE  lab.tb_rtn_dtl         IS '반품상세. 로트·품목은 출고상세에서 가져옴(저장하지 않음)';
COMMENT ON COLUMN lab.tb_rtn_dtl.rtn_qty IS '반품수량. 같은 출고 라인의 누적 반품 <= 출고수량 (품질 규칙)';

-- 샘플: 햇살약국이 3/3 출고분 중 한빛펜정 2 BOX(파손), 한빛시럽 5 EA(임박)를 반품
INSERT INTO lab.tb_rtn (rtn_no, rtn_dt, cust_no, rtn_stat_cd) VALUES ('RT2026030001', DATE '2026-03-20', 'C000201', '30');
INSERT INTO lab.tb_rtn_dtl (rtn_no, rtn_seq, ship_no, ship_seq, rtn_qty, rtn_rsn_cd) VALUES
 ('RT2026030001', 1, 'SH2026030001', 1, 2, '02'),
 ('RT2026030001', 2, 'SH2026030001', 2, 5, '01');
```

존재하지 않는 출고 라인을 가리키는 반품은 FK가 막습니다.

```sql 의도된 오류 — 원래 출고 라인이 없는 반품
INSERT INTO lab.tb_rtn_dtl (rtn_no, rtn_seq, ship_no, ship_seq, rtn_qty, rtn_rsn_cd)
VALUES ('RT2026030001', 3, 'SH2026030001', 9, 1, '03');
```

행 간 규칙(누적 반품 ≤ 출고)은 CHECK로 표현할 수 없습니다. 등록 화면·프로시저가 검사하고, 같은 규칙을 품질 점검으로 매일 확인합니다. 일부러 초과 반품을 넣어 점검이 잡는지 봅니다.

```sql
BEGIN;
INSERT INTO lab.tb_rtn (rtn_no, rtn_dt, cust_no, rtn_stat_cd) VALUES ('RT2026030002', DATE '2026-03-25', 'C000201', '10');
INSERT INTO lab.tb_rtn_dtl (rtn_no, rtn_seq, ship_no, ship_seq, rtn_qty, rtn_rsn_cd)
VALUES ('RT2026030002', 1, 'SH2026030001', 1, 9, '02');      -- 출고 10, 기존 반품 2 + 9 = 11

SELECT d.ship_no, d.ship_seq, d.ship_qty, SUM(r.rtn_qty) AS rtn_qty_sum
  FROM erp.tb_ship_dtl d
  JOIN lab.tb_rtn_dtl r ON r.ship_no = d.ship_no AND r.ship_seq = d.ship_seq
  JOIN lab.tb_rtn h     ON h.rtn_no = r.rtn_no
 WHERE h.rtn_stat_cd <> '90'                                 -- 반려는 제외
 GROUP BY d.ship_no, d.ship_seq, d.ship_qty
HAVING SUM(r.rtn_qty) > d.ship_qty;
ROLLBACK;
```

SH2026030001 1번 라인(출고 10)에 반품 합계 11이 잡힙니다. 반려(90)를 빼는 조건은 코드값을 직접 쓰고 있는데, 엄밀하게는 Day 9 원칙대로 "누적 대상 여부" 속성을 반품상태에 두는 편이 낫습니다. 리뷰에서 지적받을 만한 지점으로 남겨 둡니다.

반품 로트는 출고상세를 거쳐 나옵니다.

```sql
SELECT h.rtn_no, h.rtn_dt, c.cust_nm, d.item_cd, d.lot_no, l.exp_dt, r.rtn_qty, r.rtn_rsn_cd
  FROM lab.tb_rtn h
  JOIN lab.tb_rtn_dtl r  ON r.rtn_no = h.rtn_no
  JOIN erp.tb_ship_dtl d ON d.ship_no = r.ship_no AND d.ship_seq = r.ship_seq
  JOIN erp.tb_lot l      ON l.lot_no = d.lot_no
  JOIN erp.tb_cust c     ON c.cust_no = h.cust_no
 ORDER BY h.rtn_no, r.rtn_seq;
```

한빛펜정 L250901 2 BOX, 한빛시럽 L250620 5 EA입니다. 시럽 로트 L250620은 Day 13에서 "임박"으로 잡힌 바로 그 로트이고, 반품 사유도 01(유효기한 임박)입니다. 로트 마스터, 임박 기준, 반품 사유가 하나의 이야기로 연결됩니다.

### 설계 리뷰 자동 점검

리뷰 전에 카탈로그로 기계적인 항목을 먼저 확인합니다. 대상은 오늘 만든 `lab` 스키마입니다.

```sql
-- (1) PK 없는 테이블
SELECT 'PK 없음' AS chk, c.relname AS obj_nm, NULL AS detail
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'lab' AND c.relkind IN ('r', 'p')
   AND NOT EXISTS (SELECT 1 FROM pg_constraint k WHERE k.conrelid = c.oid AND k.contype = 'p')
UNION ALL
-- (2) 인덱스가 선두에 없는 FK
SELECT 'FK 인덱스 없음', c.conrelid::regclass::text, c.conname
  FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
 WHERE c.contype = 'f' AND n.nspname = 'lab'
   AND NOT EXISTS (SELECT 1 FROM pg_index i
                    WHERE i.indrelid = c.conrelid
                      AND (i.indkey::int2[])[0:cardinality(c.conkey) - 1] = c.conkey)
UNION ALL
-- (3) 설명(COMMENT) 없는 테이블
SELECT '테이블 설명 없음', c.relname, NULL
  FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
 WHERE n.nspname = 'lab' AND c.relkind IN ('r', 'p') AND obj_description(c.oid, 'pg_class') IS NULL
UNION ALL
-- (4) NULL 허용 컬럼 (사유가 테이블정의서에 있는지 사람이 확인)
SELECT 'NULL 허용', table_name, column_name
  FROM information_schema.columns
 WHERE table_schema = 'lab' AND is_nullable = 'YES'
 ORDER BY 1, 2, 3;
```

6건이 나옵니다. FK 인덱스 없음 2건(반품 → 반품상태, 반품상세 → 출고상세. 반품 → 거래처는 IX_RTN_01이, 반품상세 → 반품은 PK가 선두에 있어 빠짐), NULL 허용 2건(TB_RTN의 UPD_DTM, UPD_ID), 테이블 설명 없음 2건(TB_RTN, TB_RTN_STAT). 하나씩 판단합니다. 반품상세 → 출고상세 인덱스는 테이블정의서에 IX_RTN_DTL_01로 적어 놓고 DDL에서 빠뜨린 것이므로 **결함**입니다. 반품 → 반품상태 FK 인덱스는 값이 네 개뿐이라 만들지 않는 것이 맞고, 그 판단을 정의서에 적습니다. UPD_* 의 NULL은 "수정 전에는 비어 있음"이라는 사유가 있어 통과, 설명 없는 두 테이블은 COMMENT를 보완합니다. 이렇게 **자동 점검 결과에도 사람의 판정 기록**이 붙어야 리뷰가 끝납니다.

### 설계 리뷰 체크리스트

| 영역 | 확인 질문 | 확인 방법 | 근거 |
|---|---|---|---|
| 요구사항 추적 | 모든 요구사항 조각이 엔터티·제약·규칙 중 어딘가에 반영됐나 | 요구사항 ↔ 설계 결정 표 | Day 3 |
| 식별자 | PK가 불변이고 업무 중복은 UNIQUE·점검으로 막았나 | 자동(PK 없음) + 사람 | Day 4 |
| 정규화 | 반정규화 컬럼마다 원천과 정합성 수단이 있나 | 사람 | Day 5 |
| 이력 | 이력 형태와 경계 규칙(9999-12-31, 종료일 포함)이 맞나 | 자동(겹침 점검) + 사람 | Day 7 |
| 타입·NULL | 도메인과 일치, NULL 허용 사유 기재 | 자동(도메인 대조, NULL 목록) | Day 8, 10 |
| 제약·인덱스 | 불변 규칙은 CHECK, FK 인덱스는 접근 경로로 판정 | 자동(FK 인덱스) + 사람 | Day 8 |
| 코드 | 담는 곳(공통/개별)과 로직이 속성에 걸렸나 | 사람 + 코드값 하드코딩 검색 | Day 9 |
| 표준 | 단어·용어 등록, 금칙어 없음 | 자동(미등록 단어) | Day 10 |
| 메타데이터 | 테이블·컬럼 설명, 오너 | 자동(설명 없음) | Day 11 |
| 품질·감사 | 행 간 규칙의 점검 쿼리, 감사 대상 여부 | 품질 규칙 목록 | Day 12 |
| 마스터·로트 | 마스터 참조가 교차참조·로트 추적과 이어지나 | 사람 + 추적 쿼리 | Day 13 |

## Before / After

**Before: 반품을 마이너스 주문으로 처리**

```text
TB_ORD_DTL  SO2026030099 / P10001 / ORD_QTY=-2 / ORD_AMT=-6400
  원 출고 라인 연결 없음, 로트 없음, 사유 없음, 상태는 주문상태 재사용
```

| 문제 | 결과 |
|---|---|
| 원 출고와 연결 없음 | 반품 로트 추적 불가, 누적 반품 ≤ 출고 검증 불가 |
| 음수 수량 | Day 8의 CHECK (수량 > 0)을 걸 수 없음, 주문 건수·평균 단가 왜곡 |
| 상태 재사용 | "출고완료"된 반품이라는 뜻 없는 상태 |

**After: 반품 엔터티 + 출고상세 FK + 상태·사유 코드 + 품질 규칙**

위 TB_RTN / TB_RTN_DTL. 순매출은 "주문금액 − 입고완료 반품금액"으로 계산하고, 반품금액의 단가는 원 주문 단가를 따라갑니다(과제 1).

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 반품 모델 | 원 거래 추적·사유·별도 상태가 필요하면 별도 엔터티 | 회계상 마이너스 전표만 필요한 단순 정정이면 원 거래 취소 + 재발행 |
| 참조 거래의 속성 복제 | 조회가 적고 조인이 PK로 가능하면 복제하지 않음 | 대량 조회가 핵심이면 복제 + 정합성 품질 규칙 |
| 행 간 규칙 | 동시 입력이 적으면 등록 절차(프로시저)에서 검사 + 품질 점검 | 동시 입력이 많으면 잠금 전략까지 설계, 트리거는 신중히 |

Week 2까지의 결정은 그대로 Week 3의 DW로 이어집니다. 반품은 출고 팩트와 같은 grain의 "반품 라인" 팩트가 될지, 출고 팩트에 음수 행으로 합쳐질지를 Day 16의 grain 결정에서 다시 만납니다.

## 흔한 실수 3가지

1. **요구사항의 "할 수 없다" 문장을 놓치는 실수.** "반품 합계는 출고 수량을 넘을 수 없다"처럼 금지 문장은 화면 기능이 아니라 제약·품질 규칙이 되어야 합니다. 요구사항 ↔ 설계 결정 표에서 금지 문장을 따로 표시합니다.
2. **테이블정의서와 DDL이 따로 노는 실수.** 오늘 예시처럼 정의서에는 인덱스가 있는데 DDL에는 없는 일이 흔합니다. DDL을 정의서에서 생성하거나, 자동 점검으로 둘을 대조합니다.
3. **앞선 결정을 매번 다시 논쟁하는 실수.** 종료일 포함 여부, 9999-12-31, 코드 문자 타입은 이미 정했습니다. 리뷰에서 같은 논쟁이 반복되면 표준 문서에 없는 것이므로 표준을 보완합니다.

## 셀프 체크 질문

**Q1. "같은 출고 라인의 반품 합계는 출고 수량을 넘을 수 없다"를 어떻게 보장하시겠습니까?**

:::answer 모범 답안 보기
행 간 규칙이라 CHECK로는 표현되지 않습니다. 반품 등록 절차(프로시저나 서비스)에서 같은 출고 라인의 기존 반품 합계(반려 제외)를 읽어 검사하고, 동시 등록이 있을 수 있으면 출고 라인 단위로 잠그는 방식까지 정합니다. 같은 규칙을 품질 점검 쿼리로 매일 돌려 절차를 우회한 입력(이관, 수작업)을 잡습니다. 트리거는 동시성·대량 이관 성능을 검토한 뒤에만 씁니다.
:::

**Q2. 반품상세에 로트번호를 저장하지 않은 이유를 설명해 보세요.**

:::answer 모범 답안 보기
반품 로트는 원 출고 라인의 로트와 같아야 하는데, 반품상세에 따로 저장하면 서로 다른 값이 들어갈 수 있고 그 정합성을 지킬 수단을 추가로 만들어야 합니다(Day 5의 반정규화 비용). 반품은 건수가 적고 출고상세는 PK로 조인되므로 조인 비용이 작습니다. 그래서 출고상세 FK로 가져오는 정규화된 구조를 택했습니다. 반품이 많고 로트별 반품 조회가 핵심 화면이 된다면 로트번호를 복제하고 "반품 로트 = 출고 로트" 품질 규칙을 붙이는 쪽으로 바꿀 수 있습니다. 결정과 전환 조건을 테이블정의서에 함께 적습니다.
:::

**Q3. 설계 리뷰를 준비하는 PL로서 무엇을 미리 해 두겠습니까?**

:::answer 모범 답안 보기
세 가지를 준비합니다. 요구사항 조각 ↔ 설계 결정 ↔ 근거 표로 누락이 없음을 보이고, 카탈로그 기반 자동 점검(PK, FK 인덱스, 설명, NULL, 표준 단어·도메인)을 돌려 결과마다 "결함·의도·조치" 판정을 붙이고, 원칙끼리 부딪힌 지점(오늘의 로트 복제 여부 같은 것)만 안건으로 올립니다.
:::

## 오늘의 과제

**과제 1.** 거래처별 순매출을 구하세요. 순매출 = 주문금액(취소 제외) − 반품금액(입고완료만), 반품금액 = 반품수량 × 원 주문단가입니다. 결과 모양은 `cust_no, cust_nm, ord_amt, rtn_amt, net_amt`이며 햇살약국은 주문 82,000원, 반품 18,900원, 순매출 63,100원이어야 합니다.

:::answer 해설 보기
반품 → 출고상세 → 주문상세로 가면 원 주문단가가 나옵니다. 반품을 거래처로 모을 때는 반품 헤더의 거래처를 씁니다. 주문과 반품을 각각 먼저 집계한 뒤 붙여야 fan-out이 생기지 않습니다(Day 16 예고).

```sql
WITH ord AS (
  SELECT o.cust_no, SUM(d.ord_amt) AS ord_amt
    FROM erp.tb_ord o JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
   WHERE o.ord_stat_cd <> '90'
   GROUP BY o.cust_no
), rtn AS (
  SELECT h.cust_no, SUM(r.rtn_qty * od.uprc) AS rtn_amt
    FROM lab.tb_rtn h
    JOIN lab.tb_rtn_stat st ON st.rtn_stat_cd = h.rtn_stat_cd AND st.inv_aply_yn = 'Y'
    JOIN lab.tb_rtn_dtl r   ON r.rtn_no = h.rtn_no
    JOIN erp.tb_ship_dtl sd ON sd.ship_no = r.ship_no AND sd.ship_seq = r.ship_seq
    JOIN erp.tb_ord_dtl od  ON od.ord_no = sd.ord_no AND od.ord_seq = sd.ord_seq
   GROUP BY h.cust_no
)
SELECT c.cust_no, c.cust_nm, COALESCE(o.ord_amt, 0) AS ord_amt, COALESCE(r.rtn_amt, 0) AS rtn_amt,
       COALESCE(o.ord_amt, 0) - COALESCE(r.rtn_amt, 0) AS net_amt
  FROM erp.tb_cust c
  LEFT JOIN ord o ON o.cust_no = c.cust_no
  LEFT JOIN rtn r ON r.cust_no = c.cust_no
 ORDER BY c.cust_no;
```

햇살약국 반품금액은 2 × 3,200 + 5 × 2,500 = 18,900원입니다. 반품 시점(3월 20일)의 기준가가 아니라 원 주문단가를 쓰는 것이 핵심이며, 4월 이후 반품이라면 기준가(3,000원)와 주문단가(3,200원)가 달라 차이가 납니다. 이 규칙은 매핑정의서와 지표 정의서에 적습니다.
:::

**과제 2.** 위 자동 점검에서 결함으로 판정한 "반품상세 → 출고상세 FK 인덱스"를 만들고, 점검 (2)만 다시 돌려 반품상태 FK 하나만 남는지 확인하세요.

:::answer 해설 보기
```sql
CREATE INDEX ix_rtn_dtl_01 ON lab.tb_rtn_dtl (ship_no, ship_seq);

SELECT c.conrelid::regclass AS table_nm, c.conname
  FROM pg_constraint c JOIN pg_namespace n ON n.oid = c.connamespace
 WHERE c.contype = 'f' AND n.nspname = 'lab'
   AND NOT EXISTS (SELECT 1 FROM pg_index i
                    WHERE i.indrelid = c.conrelid
                      AND (i.indkey::int2[])[0:cardinality(c.conkey) - 1] = c.conkey)
 ORDER BY 1, 2;
```

반품 → 반품상태(rtn_stat_cd) FK만 남습니다. 이것은 "값이 4개뿐인 코드 테이블이라 인덱스 불필요"라는 판정과 함께 정의서에 남기면 리뷰 통과입니다. 자동 점검의 목표는 0건이 아니라 **모든 결과에 판정이 붙는 것**입니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 요구사항정의서 | 요구사항 문장, 금지 규칙 표시, 요구사항 ID. |
| 요구사항 추적표 | 요구사항 ID ↔ 엔터티·제약·코드·품질 규칙 ↔ 근거 표준. |
| ERD (논리·물리) | 반품·반품상세와 출고상세의 관계, 카디널리티·옵셔널리티. |
| 테이블정의서·인덱스정의서 | 위 정의서 형식. 복제하지 않은 속성과 그 이유, 전환 조건. |
| 표준단어 신청서 | 반품(RTN), 사유(RSN). |
| 설계 리뷰 결과서 | 자동 점검 결과와 판정(결함·의도·조치), 회의 안건과 결정. |

## 참고할 원전

- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 모델링 영역 전반, 데이터 표준화 영역.
- Graeme Simsion, Graham Witt, "Data Modeling Essentials", 3rd ed. (Morgan Kaufmann, 2005).
- PostgreSQL 공식 문서 — "System Catalogs" (pg_constraint, pg_index), "Constraints".
