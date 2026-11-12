# Day 6. 슈퍼타입/서브타입, 계층 구조

## 오늘의 한 줄

슈퍼타입/서브타입은 "공통인 것은 한 번, 다른 것만 따로"를 모델로 표현하는 방법이고, 계층 구조는 "같은 종류끼리의 부모·자식"을 자기참조로 표현하는 방법입니다. 둘 다 물리 변환 방식에 따라 조회 편의와 정합성 강제력이 정반대로 갈립니다.

## 왜 중요한가

병원·약국·도매상을 거래처 하나로 통합했는데(Day 3) 유형별 고유 속성이 늘어나자 누군가 거래처 테이블에 병상수, 주거래병원, 여신한도 컬럼을 계속 추가합니다. 약국 행에 여신한도가 들어가도 아무도 막지 못하고, 컬럼 절반이 NULL인 테이블이 됩니다. 반대로 유형별 테이블로 완전히 쪼개면 주문 테이블의 거래처 FK를 걸 곳이 사라집니다. BOM처럼 단계 수가 정해지지 않은 계층을 "레벨1·레벨2·레벨3 컬럼"으로 만들면, 반제품 단계가 하나 늘어나는 순간 원료 소요량 계산이 틀어집니다.

## 핵심 개념

### 1. 슈퍼타입/서브타입: 공통과 차이를 나누는 모델

쉽게 말하면 "거래처라는 큰 묶음(슈퍼타입) 안에 병원·약국·도매상이라는 작은 묶음(서브타입)이 있다"는 구조입니다. 공통 속성(거래처명, 사업자등록번호, 지역)과 공통 관계(주문)는 슈퍼타입에, 고유 속성(병상수, 여신한도)과 고유 관계(약국의 주거래병원)는 서브타입에 둡니다. 정확한 용어로 일반화(generalization)·특수화(specialization)라고 합니다.

서브타입을 나눌 때는 두 가지 규칙을 정해야 합니다.

| 규칙 | 질문 | 한빛제약 거래처 |
|---|---|---|
| 배타 vs 중복 (exclusive / inclusive) | 한 거래처가 두 서브타입에 동시에 속할 수 있나? | 배타: 한 거래처는 한 유형만 (CUST_TP_CD 하나) |
| 완전 vs 불완전 (complete / incomplete) | 모든 거래처가 반드시 어느 서브타입에 속하나? | 완전: 01·02·03 중 하나는 꼭 |

이 두 규칙이 정해져야 서브타입 판별자(CUST_TP_CD)를 NOT NULL로 할지, 한 거래처에 서브타입 행이 둘 생기는 것을 막을지가 정해집니다.

### 2. 물리 변환 3가지 방식

논리 모델의 슈퍼타입/서브타입은 물리 테이블로 바꿀 때 세 가지 방식이 있습니다.

| 방식 | 구조 | 조회 | 정합성 강제 | 확장 |
|---|---|---|---|---|
| ① 단일 테이블 (롤업, one table) | TB_CUST 하나에 모든 서브타입 컬럼 | 조인 없음, 가장 단순 | 유형별 필수 여부를 CHECK로만, 컬럼 대부분 NULL | 서브타입 추가 때마다 컬럼 추가 |
| ② 슈퍼 + 서브 테이블 (각각, one-to-one) | TB_CUST + TB_CUST_HOSP/PHAR/WHSL | 고유 속성이 필요할 때만 조인 | NOT NULL·FK를 서브 테이블에서 바로 강제 | 서브 테이블만 추가 |
| ③ 서브타입별 테이블 (롤다운, 슈퍼 없음) | TB_HOSP, TB_PHAR, TB_WHSL 각각 공통 컬럼 포함 | 유형 하나만 보면 단순, 전체를 보려면 UNION | 다른 테이블이 "거래처"를 FK로 참조할 수 없음 | 공통 컬럼 변경을 모든 테이블에 반복 |

한빛제약 주문은 모든 유형의 거래처를 하나의 FK(TB_ORD.CUST_NO)로 참조해야 하므로 ③은 사실상 탈락입니다. ①과 ② 중에서는 고유 속성의 개수와 정합성 요구로 고릅니다. 고유 속성이 한두 개면 ①, 여러 개이거나 고유 관계(약국 → 병원)가 있으면 ②가 유리합니다.

### 3. 계층 구조: 자기참조 관계

부서의 상위부서, BOM의 상위품목처럼 **같은 엔터티 안에서** 부모·자식이 생기는 구조입니다. 정확한 용어로 재귀 관계(recursive relationship) 또는 자기참조(self-referencing)라고 합니다.

| 계층 | 구조 | 특징 |
|---|---|---|
| 부서 (TB_DEPT) | 자식 → 부모 하나 (PRNT_DEPT_CD 컬럼) | 트리. 한 부서는 상위부서가 하나 |
| BOM (TB_BOM) | 상위품목·하위품목 쌍을 별도 테이블로 | 네트워크. 원료A는 여러 제품에 들어감. 관계마다 소요량·적용기간이 붙음 |

부서처럼 부모가 하나뿐이면 엔터티 안에 상위 컬럼을 두면 됩니다. BOM처럼 하위 품목이 여러 부모를 가질 수 있고 관계 자체에 속성(소요량, 적용기간)이 있으면 **관계를 별도 테이블로** 뺍니다. 품목과 품목 사이의 M:N을 교차 엔터티로 푼 것과 같습니다(Day 3).

### 4. 계층을 읽는 방법: 재귀 쿼리

단계 수가 정해지지 않은 계층은 고정된 조인 횟수로 읽을 수 없습니다. 재귀 공통 테이블 식(recursive CTE)을 씁니다. 시작점(앵커)을 고르고, "지금 찾은 행의 자식"을 반복해서 붙이는 방식입니다. 실무에서 꼭 같이 설계할 것은 세 가지입니다.

- **누적 계산**: BOM 소요량은 단계마다 곱해야 합니다(완제품 100 BOX × 정제 0.02 KG × 과립 1.02 …).
- **기준일자 필터**: BOM은 적용기간이 있으므로 모든 단계에서 같은 기준일자로 유효한 행만 따라가야 합니다.
- **순환 감지**: 잘못 등록된 관계(과립 → 완제품)가 있으면 무한 반복합니다. 순환을 감지해 멈추고 알려야 합니다.

## 예시

### 거래처 서브타입: ② 슈퍼 + 서브 테이블

거래처 유형별로 새 요구사항이 생겼습니다.

> "병원은 종별(의원·병원·종합병원)과 병상수를 관리한다. 약국은 주로 처방전을 받는 병원(주거래병원)을 관리한다. 도매상은 여신한도를 관리하며 반드시 값이 있어야 한다."

| 서브타입 테이블 | 한글 논리명 (ENGLISH_PHYSICAL) | 비고 |
|---|---|---|
| 병원거래처 (TB_CUST_HOSP) | 거래처번호 (CUST_NO), 병원종별코드 (HOSP_TP_CD), 병상수 (BED_CNT) | 종별 01 의원, 02 병원, 03 종합병원 |
| 약국거래처 (TB_CUST_PHAR) | 거래처번호 (CUST_NO), 주거래병원거래처번호 (MAIN_HOSP_CUST_NO) | 병원 서브타입을 참조 |
| 도매상거래처 (TB_CUST_WHSL) | 거래처번호 (CUST_NO), 여신한도금액 (CRDT_LMT_AMT) | NOT NULL |

HOSP(병원), PHAR(약국), WHSL(도매상), BED(병상), CNT(수), MAIN(주), CRDT(여신), LMT(한도)는 표준 약어표에 없는 단어입니다. 실제 프로젝트라면 Day 10의 표준단어 신청 대상입니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE lab.tb_cust_hosp (          -- 병원거래처
  cust_no     VARCHAR(10) PRIMARY KEY REFERENCES erp.tb_cust (cust_no),
  hosp_tp_cd  VARCHAR(2)  NOT NULL CHECK (hosp_tp_cd IN ('01', '02', '03')),
  bed_cnt     NUMERIC(5)
);
CREATE TABLE lab.tb_cust_phar (          -- 약국거래처
  cust_no            VARCHAR(10) PRIMARY KEY REFERENCES erp.tb_cust (cust_no),
  main_hosp_cust_no  VARCHAR(10) REFERENCES lab.tb_cust_hosp (cust_no)
);
CREATE TABLE lab.tb_cust_whsl (          -- 도매상거래처
  cust_no       VARCHAR(10) PRIMARY KEY REFERENCES erp.tb_cust (cust_no),
  crdt_lmt_amt  NUMERIC(15) NOT NULL
);

INSERT INTO lab.tb_cust_hosp VALUES ('C000101', '01', NULL), ('C000102', '03', 300);
INSERT INTO lab.tb_cust_phar VALUES ('C000201', 'C000101'), ('C000202', NULL);
INSERT INTO lab.tb_cust_whsl VALUES ('C000301', 50000000);
```

병상수 300, 여신한도 5천만 원은 가상 값입니다. 주목할 점은 두 가지입니다. 도매상의 여신한도 필수 규칙이 NOT NULL 한 줄로 끝났고, 약국의 주거래병원은 **병원 서브타입**을 FK로 참조하므로 약국이 다른 약국을 주거래병원으로 잡는 실수를 DB가 막습니다. 단일 테이블이었다면 둘 다 CHECK나 애플리케이션 로직으로 지켜야 합니다.

이 방식의 약점은 "판별자 CUST_TP_CD와 서브타입 테이블이 서로 맞는가"를 FK만으로는 보장하지 못한다는 점입니다. 약국(02) 거래처가 병원 서브타입 테이블에 들어가도 막히지 않습니다. 슈퍼타입에 UNIQUE (CUST_NO, CUST_TP_CD)를 두고 서브 테이블이 (CUST_NO, CUST_TP_CD)를 복합 FK로 참조하면서 `CHECK (CUST_TP_CD = '02')`를 거는 기법으로 막을 수 있지만, 운영계 TB_CUST 변경이 필요하므로 ERP 운영팀 승인 사항입니다. 그 전까지는 점검 쿼리로 지킵니다.

```sql
-- 판별자와 서브타입 테이블의 정합성: 배타·완전 규칙 점검 (0건이어야 정상)
SELECT c.cust_no, c.cust_nm, c.cust_tp_cd,
       (h.cust_no IS NOT NULL) AS in_hosp,
       (p.cust_no IS NOT NULL) AS in_phar,
       (w.cust_no IS NOT NULL) AS in_whsl
  FROM erp.tb_cust c
  LEFT JOIN lab.tb_cust_hosp h ON h.cust_no = c.cust_no
  LEFT JOIN lab.tb_cust_phar p ON p.cust_no = c.cust_no
  LEFT JOIN lab.tb_cust_whsl w ON w.cust_no = c.cust_no
 WHERE NOT ( (c.cust_tp_cd = '01' AND h.cust_no IS NOT NULL AND p.cust_no IS NULL AND w.cust_no IS NULL)
          OR (c.cust_tp_cd = '02' AND p.cust_no IS NOT NULL AND h.cust_no IS NULL AND w.cust_no IS NULL)
          OR (c.cust_tp_cd = '03' AND w.cust_no IS NOT NULL AND h.cust_no IS NULL AND p.cust_no IS NULL) );
```

조회 쪽에서는 서브타입을 펼친 뷰를 하나 두면 사용자는 ① 단일 테이블처럼 쓸 수 있습니다.

```sql
CREATE VIEW lab.v_cust_full AS
SELECT c.cust_no, c.cust_nm, c.cust_tp_cd, c.rgn_cd,
       h.hosp_tp_cd, h.bed_cnt, p.main_hosp_cust_no, w.crdt_lmt_amt
  FROM erp.tb_cust c
  LEFT JOIN lab.tb_cust_hosp h ON h.cust_no = c.cust_no
  LEFT JOIN lab.tb_cust_phar p ON p.cust_no = c.cust_no
  LEFT JOIN lab.tb_cust_whsl w ON w.cust_no = c.cust_no;

SELECT * FROM lab.v_cust_full ORDER BY cust_no;
```

### 같은 요구를 ① 단일 테이블로 만들면

```sql
CREATE TABLE lab.tb_cust_one (
  cust_no            VARCHAR(10) PRIMARY KEY,
  cust_nm            VARCHAR(100) NOT NULL,
  cust_tp_cd         VARCHAR(2)  NOT NULL CHECK (cust_tp_cd IN ('01', '02', '03')),
  hosp_tp_cd         VARCHAR(2),
  bed_cnt            NUMERIC(5),
  main_hosp_cust_no  VARCHAR(10) REFERENCES lab.tb_cust_one (cust_no),
  crdt_lmt_amt       NUMERIC(15),
  -- 유형별 필수·금지 규칙을 전부 CHECK로 표현해야 함
  CONSTRAINT ck_cust_one_hosp CHECK ((cust_tp_cd = '01') = (hosp_tp_cd IS NOT NULL)),
  CONSTRAINT ck_cust_one_bed  CHECK (cust_tp_cd = '01' OR bed_cnt IS NULL),
  CONSTRAINT ck_cust_one_phar CHECK (cust_tp_cd = '02' OR main_hosp_cust_no IS NULL),
  CONSTRAINT ck_cust_one_whsl CHECK ((cust_tp_cd = '03') = (crdt_lmt_amt IS NOT NULL))
);

INSERT INTO lab.tb_cust_one
SELECT cust_no, cust_nm, cust_tp_cd, hosp_tp_cd, bed_cnt, NULL, crdt_lmt_amt
  FROM lab.v_cust_full;
UPDATE lab.tb_cust_one o
   SET main_hosp_cust_no = v.main_hosp_cust_no
  FROM lab.v_cust_full v
 WHERE v.cust_no = o.cust_no AND v.main_hosp_cust_no IS NOT NULL;
```

```sql 의도된 오류 — 약국 행에 여신한도 입력
UPDATE lab.tb_cust_one SET crdt_lmt_amt = 10000000 WHERE cust_no = 'C000201';
```

CHECK 제약이 막아 주긴 하지만 규칙이 늘수록 CHECK도 늘어납니다. 그리고 약국의 주거래병원이 **병원인지**는 같은 테이블 자기참조 FK로는 보장할 수 없습니다(약국이 약국을 가리켜도 통과). 고유 관계가 있는 서브타입이 ②를 고르는 결정적인 이유입니다.

### BOM 자기참조: 한빛케미칼 다단계 BOM

공통 스키마의 BOM은 한빛펜정 → 원료A, PTP 호일의 1단계뿐입니다. 한빛록스정을 반제품이 있는 3단계 BOM으로 확장해 실습합니다. 운영계를 바꾸지 않도록 `lab`에 복사본을 만들고, 반제품 품목유형 SF를 추가로 씁니다.

| 상위품목 | 하위품목 | 소요량 (BOM_QTY) | 적용기간 |
|---|---|---|---|
| P10002 한빛록스정 (BOX) | S40001 록스정 나정 벌크 (KG) | 0.02 | 2025-01-01 ~ 9999-12-31 |
| P10002 | M30001 PTP 알루미늄 호일 (ROLL) | 0.003 | 2025-01-01 ~ 9999-12-31 |
| P10002 | M30002 단상자 (EA) | 1 | 2025-01-01 ~ 2026-04-30 |
| P10002 | M30003 단상자 개선형 (EA) | 1 | 2026-05-01 ~ 9999-12-31 |
| S40001 | S40002 록스정 과립 (KG) | 1.02 | 2025-01-01 ~ 9999-12-31 |
| S40002 | R20001 원료A(주성분) (KG) | 0.3 | 2025-01-01 ~ 9999-12-31 |
| S40002 | R20002 부형제B (KG) | 0.7 | 2025-01-01 ~ 9999-12-31 |

소요량은 모두 학습용 가상 값이며, 단상자 교체는 적용기간 필터를 연습하려고 넣은 것입니다.

```sql
CREATE TABLE lab.tb_item AS SELECT item_cd, item_nm, item_tp_cd, unit_cd FROM erp.tb_item;
ALTER TABLE lab.tb_item ADD PRIMARY KEY (item_cd);
INSERT INTO lab.tb_item VALUES
 ('S40001', '록스정 나정 벌크', 'SF', 'KG'),
 ('S40002', '록스정 과립', 'SF', 'KG'),
 ('R20002', '부형제B', 'RM', 'KG'),
 ('M30002', '단상자', 'PM', 'EA'),
 ('M30003', '단상자 개선형', 'PM', 'EA');

CREATE TABLE lab.tb_bom AS SELECT * FROM erp.tb_bom;
ALTER TABLE lab.tb_bom ADD PRIMARY KEY (prnt_item_cd, chld_item_cd, aply_strt_dt);
INSERT INTO lab.tb_bom VALUES
 ('P10002', 'S40001', 0.0200, DATE '2025-01-01', DATE '9999-12-31'),
 ('P10002', 'M30001', 0.0030, DATE '2025-01-01', DATE '9999-12-31'),
 ('P10002', 'M30002', 1.0000, DATE '2025-01-01', DATE '2026-04-30'),
 ('P10002', 'M30003', 1.0000, DATE '2026-05-01', DATE '9999-12-31'),
 ('S40001', 'S40002', 1.0200, DATE '2025-01-01', DATE '9999-12-31'),
 ('S40002', 'R20001', 0.3000, DATE '2025-01-01', DATE '9999-12-31'),
 ('S40002', 'R20002', 0.7000, DATE '2025-01-01', DATE '9999-12-31');
```

```text
P10002 한빛록스정                 BOX
 +-- S40001 나정 벌크      0.02   KG
 |    +-- S40002 과립      1.02   KG
 |         +-- R20001 원료A 0.3   KG
 |         +-- R20002 부형제B 0.7 KG
 +-- M30001 PTP 호일       0.003  ROLL
 +-- M30002 단상자 (~4/30) 1      EA
 +-- M30003 개선형 (5/1~)  1      EA
```

### 정전개: 100 BOX 생산 시 단계별 소요량

```sql
-- 기준일 2026-04-15, 한빛록스정 100 BOX 생산에 필요한 단계별 소요량
WITH RECURSIVE bom_tree (lvl, prnt_item_cd, chld_item_cd, req_qty) AS (
  SELECT 1, b.prnt_item_cd, b.chld_item_cd, (100 * b.bom_qty)::numeric
    FROM lab.tb_bom b
   WHERE b.prnt_item_cd = 'P10002'
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
  UNION ALL
  SELECT t.lvl + 1, b.prnt_item_cd, b.chld_item_cd, (t.req_qty * b.bom_qty)::numeric
    FROM bom_tree t
    JOIN lab.tb_bom b
      ON b.prnt_item_cd = t.chld_item_cd
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
) SEARCH DEPTH FIRST BY chld_item_cd SET ord
  CYCLE chld_item_cd SET is_cycle USING cycle_path
SELECT repeat('  ', t.lvl - 1) || t.chld_item_cd AS item_tree,
       i.item_nm, t.lvl, ROUND(t.req_qty, 4) AS req_qty, i.unit_cd, t.is_cycle
  FROM bom_tree t
  JOIN lab.tb_item i ON i.item_cd = t.chld_item_cd
 ORDER BY t.ord;
```

| item_tree | item_nm | lvl | req_qty | unit_cd |
|---|---|---|---|---|
| M30001 | PTP 알루미늄 호일 | 1 | 0.3000 | ROLL |
| M30002 | 단상자 | 1 | 100.0000 | EA |
| S40001 | 록스정 나정 벌크 | 1 | 2.0000 | KG |
| ··S40002 | 록스정 과립 | 2 | 2.0400 | KG |
| ····R20001 | 원료A(주성분) | 3 | 0.6120 | KG |
| ····R20002 | 부형제B | 3 | 1.4280 | KG |

(표의 점은 들여쓰기를 보이게 하려고 넣은 것이며, 실제 결과는 공백입니다.) 기준일이 4월 15일이므로 단상자는 M30002가 나오고 M30003은 나오지 않습니다. 소요량은 단계마다 곱해집니다. 원료A = 100 × 0.02 × 1.02 × 0.3 = 0.612 KG입니다.

:::note Oracle 차이
Oracle의 재귀 WITH는 `RECURSIVE` 키워드 없이 `WITH bom_tree (lvl, ...) AS (...)`로 쓰고, 순환 감지는 `CYCLE chld_item_cd SET is_cycle TO 'Y' DEFAULT 'N'` 형식입니다. 아래 블록은 Oracle 전용이라 실행 검증 대상이 아닙니다.
:::

```oracle
-- Oracle 재귀 WITH
WITH bom_tree (lvl, prnt_item_cd, chld_item_cd, req_qty) AS (
  SELECT 1, b.prnt_item_cd, b.chld_item_cd, 100 * b.bom_qty
    FROM TB_BOM b
   WHERE b.prnt_item_cd = 'P10002'
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
  UNION ALL
  SELECT t.lvl + 1, b.prnt_item_cd, b.chld_item_cd, t.req_qty * b.bom_qty
    FROM bom_tree t
    JOIN TB_BOM b ON b.prnt_item_cd = t.chld_item_cd
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
) SEARCH DEPTH FIRST BY chld_item_cd SET ord
  CYCLE chld_item_cd SET is_cycle TO 'Y' DEFAULT 'N'
SELECT LPAD(' ', (lvl - 1) * 2) || chld_item_cd AS item_tree, lvl, req_qty, is_cycle
  FROM bom_tree
 ORDER BY ord;

-- Oracle CONNECT BY: 구조 펼치기는 간단하지만 단계별 곱셈(누적 소요량)은 직접 지원하지 않음
SELECT LEVEL AS lvl,
       LPAD(' ', (LEVEL - 1) * 2) || chld_item_cd AS item_tree,
       bom_qty,
       SYS_CONNECT_BY_PATH(chld_item_cd, '/') AS item_path,
       CONNECT_BY_ISLEAF AS leaf_yn
  FROM TB_BOM
 START WITH prnt_item_cd = 'P10002'
        AND DATE '2026-04-15' BETWEEN aply_strt_dt AND aply_end_dt
CONNECT BY NOCYCLE PRIOR chld_item_cd = prnt_item_cd
        AND DATE '2026-04-15' BETWEEN aply_strt_dt AND aply_end_dt
 ORDER SIBLINGS BY chld_item_cd;
```

CONNECT BY는 레거시 Oracle 코드에서 자주 만나므로 읽을 줄 알아야 합니다. 하지만 누적 소요량처럼 단계마다 값을 계산해야 하면 재귀 WITH가 낫고, 표준 SQL이라 DW 플랫폼을 옮길 때도 그대로 가져갈 수 있습니다.

### 원자재 총소요량과 순환 감지

구매팀이 실제로 원하는 것은 트리가 아니라 **말단(더 이상 하위가 없는) 자재별 합계**입니다.

```sql
WITH RECURSIVE bom_tree (chld_item_cd, req_qty) AS (
  SELECT b.chld_item_cd, (100 * b.bom_qty)::numeric
    FROM lab.tb_bom b
   WHERE b.prnt_item_cd = 'P10002'
     AND DATE '2026-05-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
  UNION ALL
  SELECT b.chld_item_cd, (t.req_qty * b.bom_qty)::numeric
    FROM bom_tree t
    JOIN lab.tb_bom b
      ON b.prnt_item_cd = t.chld_item_cd
     AND DATE '2026-05-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
)
SELECT t.chld_item_cd, i.item_nm, i.item_tp_cd, ROUND(SUM(t.req_qty), 4) AS total_req_qty, i.unit_cd
  FROM bom_tree t
  JOIN lab.tb_item i ON i.item_cd = t.chld_item_cd
 WHERE NOT EXISTS (
         SELECT 1 FROM lab.tb_bom c
          WHERE c.prnt_item_cd = t.chld_item_cd
            AND DATE '2026-05-15' BETWEEN c.aply_strt_dt AND c.aply_end_dt)
 GROUP BY t.chld_item_cd, i.item_nm, i.item_tp_cd, i.unit_cd
 ORDER BY t.chld_item_cd;
```

기준일을 5월 15일로 바꿨으므로 단상자는 M30003 개선형 100 EA가 나옵니다. 원료A 0.612 KG, 부형제B 1.428 KG, PTP 호일 0.3 ROLL과 함께 말단 자재 4개입니다.

이제 누군가 과립의 하위에 완제품을 잘못 등록했다고 해 보겠습니다.

```sql
INSERT INTO lab.tb_bom VALUES ('S40002', 'P10002', 1.0000, DATE '2026-01-01', DATE '9999-12-31');

-- 순환 감지: 같은 품목을 경로에서 다시 만나면 멈추고 표시
WITH RECURSIVE bom_tree (lvl, prnt_item_cd, chld_item_cd) AS (
  SELECT 1, b.prnt_item_cd, b.chld_item_cd
    FROM lab.tb_bom b
   WHERE b.prnt_item_cd = 'P10002'
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
  UNION ALL
  SELECT t.lvl + 1, b.prnt_item_cd, b.chld_item_cd
    FROM bom_tree t
    JOIN lab.tb_bom b
      ON b.prnt_item_cd = t.chld_item_cd
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
) CYCLE chld_item_cd SET is_cycle USING cycle_path
SELECT lvl, prnt_item_cd, chld_item_cd, cycle_path::text AS cycle_path
  FROM bom_tree
 WHERE is_cycle;

DELETE FROM lab.tb_bom WHERE prnt_item_cd = 'S40002' AND chld_item_cd = 'P10002';
```

순환 경로(S40001 → S40002 → P10002 → S40001)가 표시되고 쿼리는 무한 반복 없이 끝납니다. 실무에서는 이 쿼리를 BOM 등록 후 점검 규칙으로 돌리고, 순환이 나오면 등록을 되돌립니다.

## Before / After

**Before: 고정 단계 컬럼으로 만든 BOM**

```text
TB_BOM_FLAT
  FG_ITEM_CD, LV1_ITEM_CD, LV1_QTY,
  LV2_ITEM_CD, LV2_QTY, LV3_ITEM_CD, LV3_QTY
```

| 문제 | 결과 |
|---|---|
| 반제품 단계가 하나 늘어남 | 컬럼 추가, 모든 소요량 쿼리 수정 |
| 같은 과립이 여러 제품에 들어감 | 과립 하위 구성이 제품 행마다 반복 (Day 5 갱신 이상) |
| 부형제 비율 변경 | 해당 과립을 쓰는 모든 행을 찾아 수정 |
| 적용기간 관리 | 행 전체를 복제해야 함 |

**After: 상위·하위 쌍 + 적용기간 + 재귀 쿼리**

공통 스키마의 TB_BOM 구조 그대로입니다. 과립의 구성은 (S40002 → R20001), (S40002 → R20002) 두 행에만 있고, 몇 단계든 같은 재귀 쿼리로 펼칩니다. 단상자 교체는 행 하나의 적용기간으로 끝납니다.

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 서브타입 변환 | 고유 속성이 한두 개이고 고유 관계가 없으면 ① 단일 테이블 + CHECK | 고유 속성이 많거나 서브타입 고유 관계(약국 → 병원)가 있으면 ② 슈퍼 + 서브 |
| ③ 서브타입별 테이블 | 서브타입끼리 공통으로 참조되는 일이 전혀 없을 때만 | 주문처럼 전체를 하나의 FK로 참조해야 하면 금지 |
| 판별자 정합성 | 운영계 변경 승인이 가능하면 복합 FK + CHECK로 DB가 강제 | 승인이 어려우면 점검 쿼리를 품질 규칙으로 등록 |
| 계층 저장 | 부모가 하나뿐인 트리(부서)면 엔터티 안에 상위 컬럼 | 부모가 여럿이거나 관계에 속성(소요량·기간)이 있으면 별도 관계 테이블(BOM) |
| 계층 조회 | 단계별 누적 계산, 플랫폼 이식성이 필요하면 재귀 WITH | 레거시 Oracle 코드 유지보수면 CONNECT BY를 읽고 유지 |
| DW로 가져갈 때 | 조회가 잦은 계층(부서)은 레벨 컬럼으로 펼친 차원 | 깊이가 가변이고 크면 브리지 테이블(Day 20) |

## 흔한 실수 3가지

1. **서브타입 고유 속성을 슈퍼타입 테이블에 계속 덧붙이는 실수.** 처음에는 컬럼 하나라 괜찮아 보이지만, 몇 년 뒤엔 절반이 NULL이고 어떤 유형에 어떤 컬럼이 필수인지 아무도 모르는 테이블이 됩니다.
2. **재귀 쿼리에서 기준일자를 앵커에만 거는 실수.** 첫 단계만 유효 행을 고르고 하위 단계에서 필터를 빠뜨리면 종료된 구성까지 따라가 소요량이 부풉니다. 모든 단계에 같은 기준일자를 겁니다.
3. **순환 감지 없이 재귀 쿼리를 배치에 넣는 실수.** 잘못 등록된 관계 하나로 배치가 끝나지 않거나 재귀 한도 오류로 멈춥니다. 순환 감지 절과 BOM 등록 후 점검을 함께 둡니다.

## 셀프 체크 질문

**Q1. 병원·약국·도매상 서브타입을 물리로 바꾸는 세 방식 중 하나를 고르고, 고르지 않은 방식의 탈락 이유를 말해 보세요.**

:::answer 모범 답안 보기
② 슈퍼 + 서브 테이블을 고릅니다. 주문이 모든 유형의 거래처를 하나의 FK로 참조해야 하므로 슈퍼타입 테이블(TB_CUST)이 반드시 있어야 하고, 이 때문에 ③ 서브타입별 테이블은 탈락입니다. ① 단일 테이블은 조회가 단순하지만, 유형별 필수 규칙을 모두 CHECK로 표현해야 하고, 약국의 주거래병원이 반드시 병원이어야 한다는 서브타입 간 관계를 같은 테이블 자기참조 FK로는 보장할 수 없습니다. ②는 도매상 여신한도를 NOT NULL로, 약국 → 병원 관계를 병원 서브 테이블 FK로 DB가 직접 강제합니다. 조회 편의는 서브타입을 펼친 뷰로 보완합니다.
:::

**Q2. BOM 소요량 계산에 CONNECT BY 대신 재귀 WITH를 권하는 이유는 무엇입니까?**

:::answer 모범 답안 보기
두 가지입니다. 첫째, 소요량은 단계마다 곱해야 하는 누적 계산인데 재귀 WITH는 이전 단계의 결과 컬럼(req_qty)을 다음 단계에서 그대로 받아 곱할 수 있습니다. CONNECT BY는 경로 문자열은 쉽게 만들지만 단계별 곱셈은 직접 지원하지 않아 우회 로직이 필요합니다. 둘째, 재귀 WITH는 표준 SQL이라 PostgreSQL이나 클라우드 DW로 옮길 때 거의 그대로 쓸 수 있습니다. 다만 기존 Oracle 시스템에는 CONNECT BY 코드가 많으므로 읽고 유지보수할 수는 있어야 합니다.
:::

**Q3. 같은 재귀 쿼리가 어떤 날은 결과가 맞고 어떤 날은 소요량이 부풀어 나옵니다. 무엇부터 의심하겠습니까?**

:::answer 모범 답안 보기
적용기간 필터가 모든 단계에 같은 기준일자로 걸려 있는지부터 봅니다. 앵커에만 기준일자를 걸고 재귀 단계에서 빠뜨리면, 같은 상위·하위 쌍의 과거 행과 현재 행이 둘 다 따라와 소요량이 이중으로 계산됩니다. 그다음 BOM 선분이력이 겹치지 않는지(같은 상위·하위 쌍에 같은 날짜가 유효한 행이 둘 이상인지)를 점검합니다. Day 7의 선분 중복 검증 쿼리를 BOM에도 그대로 적용할 수 있습니다. 마지막으로 순환 관계가 새로 등록됐는지 확인합니다.
:::

## 오늘의 과제

**과제 1.** 역전개(where-used)를 해 보세요. 원료A(R20001)가 직접 또는 반제품을 거쳐 들어가는 **완제품(FG)** 을 기준일 2026-04-15로 찾고, 완제품 1단위당 원료A 소요량을 구합니다. 결과 모양은 `fg_item_cd, item_nm, r20001_qty_per_unit` 2행입니다.

:::answer 해설 보기
정전개와 방향만 반대입니다. 앵커를 "R20001을 하위로 갖는 행"으로 잡고, 찾은 상위품목을 다시 하위로 갖는 행을 따라 올라갑니다. 소요량은 올라가면서 곱합니다.

```sql
WITH RECURSIVE used_in (item_cd, qty_per_unit) AS (
  SELECT b.prnt_item_cd, b.bom_qty::numeric
    FROM lab.tb_bom b
   WHERE b.chld_item_cd = 'R20001'
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
  UNION ALL
  SELECT b.prnt_item_cd, (u.qty_per_unit * b.bom_qty)::numeric
    FROM used_in u
    JOIN lab.tb_bom b
      ON b.chld_item_cd = u.item_cd
     AND DATE '2026-04-15' BETWEEN b.aply_strt_dt AND b.aply_end_dt
)
SELECT u.item_cd AS fg_item_cd, i.item_nm, ROUND(SUM(u.qty_per_unit), 6) AS r20001_qty_per_unit
  FROM used_in u
  JOIN lab.tb_item i ON i.item_cd = u.item_cd
 WHERE i.item_tp_cd = 'FG'
 GROUP BY u.item_cd, i.item_nm
 ORDER BY u.item_cd;
```

결과는 P10001 한빛펜정 0.015 KG(직접 투입), P10002 한빛록스정 0.00612 KG(0.02 × 1.02 × 0.3)입니다. 원료A 공급에 문제가 생겼을 때 영향받는 제품을 찾는 질문이 바로 이 역전개입니다.
:::

**과제 2.** 공통 스키마의 부서(TB_DEPT)를 트리로 펼치고, 부서마다 **하위 부서를 포함한** 사원 수를 구하세요. 결과 모양은 `dept_tree, dept_cd, emp_cnt_incl_sub`이며 5행입니다.

:::answer 해설 보기
각 부서를 출발점으로 자기 자신과 모든 하위 부서를 펼친 "조상-자손 쌍"을 만든 뒤, 자손 부서의 사원을 조상 부서로 합산합니다. 이 조상-자손 쌍 테이블이 Day 20에서 배울 계층 브리지 테이블의 원형입니다.

```sql
WITH RECURSIVE tree (lvl, dept_cd, dept_nm, sort_path) AS (
  SELECT 1, d.dept_cd, d.dept_nm, ARRAY[d.dept_cd::text]
    FROM erp.tb_dept d WHERE d.prnt_dept_cd IS NULL
  UNION ALL
  SELECT t.lvl + 1, d.dept_cd, d.dept_nm, t.sort_path || d.dept_cd::text
    FROM tree t JOIN erp.tb_dept d ON d.prnt_dept_cd = t.dept_cd
), anc (anc_dept_cd, desc_dept_cd) AS (
  SELECT dept_cd, dept_cd FROM erp.tb_dept
  UNION ALL
  SELECT a.anc_dept_cd, d.dept_cd
    FROM anc a JOIN erp.tb_dept d ON d.prnt_dept_cd = a.desc_dept_cd
)
SELECT repeat('  ', t.lvl - 1) || t.dept_nm AS dept_tree,
       t.dept_cd,
       COUNT(e.emp_no) AS emp_cnt_incl_sub
  FROM tree t
  JOIN anc a ON a.anc_dept_cd = t.dept_cd
  LEFT JOIN erp.tb_emp e ON e.dept_cd = a.desc_dept_cd
 GROUP BY t.lvl, t.dept_nm, t.dept_cd, t.sort_path
 ORDER BY t.sort_path;
```

결과는 영업본부 4, 서울1팀 2, 경기팀 1, 부산팀 1, 영업기획팀 0입니다. 하나의 WITH RECURSIVE 안에 재귀 CTE를 두 개 둘 수 있다는 점도 확인해 두세요.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 논리 ERD | 슈퍼타입/서브타입 표기, 배타·완전 규칙, 판별자(CUST_TP_CD). BOM은 품목의 자기참조 M:N을 TB_BOM 관계 엔터티로. |
| 물리 설계서 / 테이블정의서 | 선택한 변환 방식(①②③)과 이유, 서브 테이블 FK·NOT NULL, 판별자 정합성을 DB로 강제하는지 점검으로 지키는지. |
| 표준단어 신청서 | HOSP, PHAR, WHSL, BED, CNT, MAIN, CRDT, LMT 등 새 표준단어와 약어 (Day 10). |
| 데이터 품질 규칙 목록 | 판별자-서브타입 정합성, BOM 순환 감지, BOM 선분 중복 점검 쿼리. |
| 프로그램 사양서 | 소요량 전개 로직: 기준일자, 전개 방향(정·역), 말단 판정 기준, 반올림 규칙. |
| DW 매핑정의서 | 부서 계층을 차원의 레벨 컬럼으로 펼치는 규칙 또는 브리지 테이블 적재 규칙. |

## 참고할 원전

- Graeme Simsion, Graham Witt, "Data Modeling Essentials", 3rd ed. (Morgan Kaufmann, 2005) — 서브타입과 슈퍼타입을 다루는 장.
- Joe Celko, "Joe Celko's Trees and Hierarchies in SQL for Smarties" (Morgan Kaufmann) — 인접 리스트, 경로, 중첩 집합 등 계층 저장 방식 비교.
- PostgreSQL 공식 문서 — "WITH Queries (Common Table Expressions)"의 재귀 쿼리, SEARCH, CYCLE 절.
- Oracle Database SQL Language Reference — "Hierarchical Queries"(CONNECT BY)와 재귀 서브쿼리 팩토링.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 모델링 영역: 슈퍼타입/서브타입 변환, 순환 관계.
