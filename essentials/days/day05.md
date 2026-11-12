# Day 5. 정규화와 반정규화

## 오늘의 한 줄

정규화는 "하나의 사실은 한 곳에만"을 지켜 갱신 지점을 줄이는 일이고, 반정규화는 그 원칙을 일부러 깨서 읽기 비용을 쓰기·정합성 비용으로 바꾸는 거래입니다. 거래를 했다면 정합성을 지킬 수단과 점검 쿼리까지 같이 설계해야 합니다.

## 왜 중요한가

영업팀의 "3월 주문 취합" 엑셀을 그대로 테이블로 올리면, 거래처 지역을 한 줄만 고쳐서 같은 병원이 두 지역에 동시에 존재하게 됩니다. 반대로 "조회가 느리다"며 주문 헤더에 합계금액 컬럼을 추가하고 갱신 로직을 빠뜨리면, 수량 정정 한 번에 화면 합계와 상세 합계가 달라집니다. 앞의 것은 정규화를 안 해서, 뒤의 것은 반정규화를 하고 정합성 설계를 안 해서 생기는 사고입니다. DW는 두 경우 모두 "어느 값이 맞나요?"라는 질문에 답하지 못합니다.

## 핵심 개념

### 1. 함수 종속: 정규화의 유일한 도구

쉽게 말하면 "A를 알면 B가 하나로 정해진다"는 관계입니다. 거래처번호를 알면 거래처명이 하나로 정해지므로 CUST_NO → CUST_NM입니다. 정확한 용어로 함수 종속(functional dependency)이라고 합니다.

정규화의 모든 단계는 한 가지 질문입니다. **"이 속성은 무엇에 종속되는가, 그리고 그것이 이 테이블의 키인가?"** 키가 아닌 것에 종속된 속성이 있으면 같은 사실이 여러 행에 반복되고, 반복되는 곳에서 이상현상이 생깁니다.

함수 종속은 데이터를 보고 추측하는 것이 아니라 **업무 규칙에서 나옵니다.** 다만 데이터로 **반례**는 찾을 수 있습니다. "같은 A인데 B가 여러 개"인 경우를 찾는 쿼리가 원천 분석에서 가장 쓸모 있는 도구입니다.

### 2. 세 가지 이상현상과 정규형

| 이상현상 | 뜻 | 엑셀 시트에서 생기는 모습 |
|---|---|---|
| 갱신 이상 | 같은 사실이 여러 행에 있어 일부만 고치면 모순 | 청솔내과의원 지역을 한 줄만 고침 |
| 삽입 이상 | 다른 사실이 없으면 이 사실을 넣을 수 없음 | 주문 없는 신규 약국을 등록할 곳이 없음 |
| 삭제 이상 | 한 사실을 지우면 다른 사실까지 사라짐 | 바른팜유통의 유일한 주문을 지우면 거래처 정보도 사라짐 |

| 정규형 | 규칙 | 없애는 것 | 이 예시에서 |
|---|---|---|---|
| 1NF | 모든 값이 원자값, 반복 그룹 없음 | 한 칸에 여러 값, 품목1·품목2 컬럼 | "한빛펜정×10, 한빛시럽×20"을 행으로 분리 |
| 2NF | 키의 **일부**에만 종속된 속성 제거 | 부분 종속 | 주문일자·거래처는 주문번호에만 종속 → 주문 헤더로 |
| 3NF | 키가 아닌 속성에 종속된 속성 제거 | 이행 종속 | 거래처명은 거래처번호에 종속 → 거래처로 |
| BCNF | 모든 결정자가 후보키 | 키 컬럼이 다른 컬럼에 종속되는 경우 | 담당자 → 창고 (아래 한빛로지스 예시) |

2NF는 키가 복합키일 때만 의미가 있습니다. BCNF 위반은 드물지만, 나타나면 대개 **후보키가 둘 이상 겹치는 배정·담당 테이블**입니다.

### 3. 반정규화는 거래입니다

정규화된 구조는 조회할 때 조인과 집계를 합니다. 반정규화는 그 결과를 미리 저장해 두는 것입니다. 얻는 것은 읽기 속도와 SQL 단순화, 내는 것은 저장 공간, 쓰기 비용, 그리고 무엇보다 **정합성 비용**입니다. 판단 변수는 네 가지입니다.

| 변수 | 반정규화 쪽으로 기울게 하는 값 | 정규화 유지 쪽으로 기울게 하는 값 |
|---|---|---|
| 조회 빈도 | 같은 계산을 화면·배치가 하루에 수없이 반복 | 가끔 보는 보고서 |
| 조인·집계 비용 | 큰 테이블 여러 개를 조인하거나 대량 집계 | 작은 마스터 하나 조인 |
| 갱신 빈도 | 원천 값이 거의 안 바뀜 (확정 후 수정 없음) | 원천 값이 자주 바뀜 |
| 정합성 비용 | 갱신 경로가 하나라 동기화가 쉬움 | 여러 화면·배치·인터페이스가 원천을 고침 |

그리고 반정규화 전에 **더 싼 대안**을 먼저 봅니다. 인덱스, 쿼리 개선, 뷰, 머티리얼라이즈드 뷰(MV), 그리고 분석용 조회라면 DW·마트로 넘기는 것입니다. 운영계 반정규화는 "운영 화면 자체가 그 값을 빠르게 써야 할 때"로 한정하는 것이 원칙입니다.

### 4. 반정규화 유형과 정합성 수단

| 유형 | 예시 | 정합성이 깨지는 순간 |
|---|---|---|
| 컬럼 중복 | 주문상세에 ORD_DT 복사 | 헤더 주문일자 정정 |
| 파생 컬럼 | 주문 헤더에 총주문금액(TOT_ORD_AMT) | 상세 수량·단가 정정, 줄 추가·삭제 |
| 집계 테이블 | 일별 거래처·품목 주문집계(TB_ORD_DAILY) | 과거 주문의 취소·정정 |
| 테이블 분할 | 큰 설명 컬럼을 별도 테이블로(수직), 연도별로(수평) | 분할 기준이 바뀔 때 (Day 8 파티셔닝) |

| 정합성 수단 | 언제 쓰나 | 약점 |
|---|---|---|
| 같은 트랜잭션에서 동시 갱신 | 갱신 경로가 서비스 하나로 모여 있을 때 | 다른 경로(배치, 직접 UPDATE)가 생기면 깨짐 |
| 트리거 | 갱신 경로가 여러 개일 때 마지막 방어선 | 숨은 로직, 대량 처리 성능, 디버깅 어려움 |
| 배치 재계산 | 집계 테이블, 실시간성이 필요 없을 때 | 배치 사이 시차, 과거분 재계산 범위 설계 필요 |
| 머티리얼라이즈드 뷰 | DB가 갱신을 관리해 주길 원할 때 | 갱신 방식·주기 제약, DBMS마다 기능 차이 |
| 대사(점검) 쿼리 | **모든 경우에 추가로** | 사후 발견이라 예방은 못 함 |

마지막 줄이 핵심입니다. 어떤 수단을 고르든 "원천과 반정규화 값이 같은가"를 확인하는 대사 쿼리는 꼭 함께 둡니다.

하나 구분할 것이 있습니다. 주문에 **주문 당시 거래처명이나 배송지**를 저장하는 것은 반정규화가 아니라 **시점의 사실 기록**입니다. 거래처명이 바뀌어도 그 주문서에는 당시 이름이 남아야 한다면 동기화하면 안 됩니다. 동기화해야 하는 값(반정규화)인지, 동기화하면 안 되는 값(스냅샷)인지 테이블정의서에 적어 두지 않으면 누군가 "불일치"를 고치겠다며 과거 기록을 덮어씁니다.

## 예시

### 정규화 1: 엑셀에서 1NF로

영업팀 취합 엑셀(0NF)은 이렇게 생겼습니다.

| 주문번호 | 주문일자 | 거래처 | 지역 | 담당자 | 품목 |
|---|---|---|---|---|---|
| SO2026030001 | 2026-03-02 | 햇살약국(약국) | SEL | 이서연(서울1팀) | 한빛펜정 500mg 30T×10, 한빛시럽 100mL×20 |
| SO2026030003 | 2026-03-10 | 바른팜유통(도매상) | GGD | 박지훈(경기팀) | 한빛펜정 500mg 30T×300, 한빛록스정 60mg 100T×100 |

칸을 쪼개고 품목마다 행을 나눈 1NF 시트를 공통 스키마에서 재현합니다. 엑셀이 ERP 화면을 내려받아 만든 것이라고 보면 됩니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;

-- 1NF: 한 칸에 값 하나, 한 행에 품목 하나. 키 = (주문번호, 주문순번)
CREATE TABLE lab.stg_ord_xls AS
SELECT o.ord_no, d.ord_seq, o.ord_dt,
       c.cust_no, c.cust_nm, c.cust_tp_cd, c.rgn_cd,
       e.emp_no, e.emp_nm, dp.dept_nm,
       d.item_cd, i.item_nm, d.ord_qty, d.uprc, d.ord_amt
  FROM erp.tb_ord o
  JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
  JOIN erp.tb_cust c    ON c.cust_no = o.cust_no
  JOIN erp.tb_emp e     ON e.emp_no = o.emp_no
  JOIN erp.tb_dept dp   ON dp.dept_cd = e.dept_cd
  JOIN erp.tb_item i    ON i.item_cd = d.item_cd
 WHERE o.ord_dt >= DATE '2026-03-01' AND o.ord_dt < DATE '2026-04-01';

ALTER TABLE lab.stg_ord_xls ADD PRIMARY KEY (ord_no, ord_seq);

SELECT ord_no, ord_seq, cust_nm, rgn_cd, emp_nm, dept_nm, item_nm, ord_qty
  FROM lab.stg_ord_xls ORDER BY ord_no, ord_seq;
```

6행이 나옵니다. 청솔내과의원의 이름·지역이 2번, 이서연의 소속팀이 3번, 한빛펜정의 품목명이 3번 반복됩니다.

### 이상현상을 실제 행으로 보기

**갱신 이상.** 청솔내과의원 지역이 바뀌었다는 연락을 받고 누군가 한 줄만 고쳤습니다.

```sql
UPDATE lab.stg_ord_xls SET rgn_cd = 'GGD'
 WHERE ord_no = 'SO2026030002' AND ord_seq = 1;

-- CUST_NO -> RGN_CD 종속의 반례 찾기
SELECT cust_no, cust_nm, COUNT(DISTINCT rgn_cd) AS rgn_cnt,
       string_agg(DISTINCT rgn_cd, ',' ORDER BY rgn_cd) AS rgn_list
  FROM lab.stg_ord_xls
 GROUP BY cust_no, cust_nm
HAVING COUNT(DISTINCT rgn_cd) > 1;
```

:::note Oracle 차이
`string_agg(DISTINCT ...)` 대신 Oracle 19c 이상은 `LISTAGG(DISTINCT RGN_CD, ',') WITHIN GROUP (ORDER BY RGN_CD)`를 씁니다.
:::

결과는 C000101 청솔내과의원, 2, GGD,SEL입니다. 이제 지역별 매출을 내면 같은 병원의 60,000원은 경기, 64,000원은 서울로 잡힙니다.

**삽입 이상.** 신규 약국 C000203 푸른숲약국이 거래를 시작했지만 아직 주문이 없습니다. 이 시트는 PK (ORD_NO, ORD_SEQ)가 비어 있는 행을 받지 않으므로 거래처를 등록할 방법이 없고, 결국 'TEMP0001' 같은 가짜 주문번호가 생깁니다.

**삭제 이상.** 바른팜유통의 주문 SO2026030003을 시트에서 지우면, 바른팜유통이 도매상이고 경기 지역이라는 사실도, 박지훈이 경기팀이라는 사실도 함께 사라집니다.

### 정규화 2: 2NF, 3NF

키 (ORD_NO, ORD_SEQ) 중 **ORD_NO에만** 종속되는 속성(주문일자, 거래처·사원 관련 전부)을 주문 헤더로 옮기면 2NF입니다. 그다음 키가 아닌 속성을 거쳐 정해지는 속성을 각 결정자의 테이블로 옮기면 3NF입니다.

- 주문: ORD_NO → CUST_NO → CUST_NM, CUST_TP_CD, RGN_CD
- 주문: ORD_NO → EMP_NO → EMP_NM, DEPT_CD → DEPT_NM
- 주문상세: (ORD_NO, ORD_SEQ) → ITEM_CD → ITEM_NM

```text
TB_CUST    (CUST_NO, CUST_NM, CUST_TP_CD, RGN_CD)
TB_EMP     (EMP_NO, EMP_NM, DEPT_CD)
TB_DEPT    (DEPT_CD, DEPT_NM, PRNT_DEPT_CD)
TB_ITEM    (ITEM_CD, ITEM_NM, ...)
TB_ORD     (ORD_NO, ORD_DT, CUST_NO, EMP_NO, ORD_STAT_CD)
TB_ORD_DTL (ORD_NO, ORD_SEQ, ITEM_CD, ORD_QTY, UPRC, ORD_AMT)
```

공통 스키마 구조 그대로입니다. 지역은 TB_CUST 한 행에만 있으니 일부만 고칠 수 없고, 푸른숲약국은 주문 없이 등록되며, 주문을 지워도 거래처와 사원은 남습니다.

### 단가는 왜 품목으로 빼지 않는가

3NF 단계에서 "단가는 품목에 종속되니 TB_ITEM으로 보내자"는 의견이 자주 나옵니다. 데이터로 반례를 찾아보면 바로 답이 나옵니다.

```sql
-- ITEM_CD -> UPRC 종속의 반례: 같은 품목인데 주문 단가가 여러 개
SELECT item_cd, COUNT(DISTINCT uprc) AS uprc_cnt,
       string_agg(DISTINCT uprc::text, ',') AS uprc_list
  FROM erp.tb_ord_dtl
 GROUP BY item_cd
HAVING COUNT(DISTINCT uprc) > 1;
```

P10001은 3,200원과 3,000원 두 값이 나옵니다. 4월 1일에 기준가가 바뀌었기 때문입니다. UPRC는 "그 주문 줄에서 적용된 값"이라 키 (ORD_NO, ORD_SEQ)에 종속되고, 기준가 자체는 (품목, 단가유형, 적용시작일자)를 키로 하는 품목단가이력(Day 7)에 둡니다. 함수 종속을 데이터 모양이 아니라 **업무 규칙으로 판단해야 하는** 대표 사례입니다.

### 정규화 3: BCNF — 한빛로지스 창고별 품목 담당자

한빛로지스의 규칙은 두 가지입니다. 한 창고의 한 품목은 담당자가 한 명이다((WH_CD, ITEM_CD) → EMP_NO). 담당자는 한 창고에만 소속된다(EMP_NO → WH_CD).

| 창고코드 (WH_CD) | 품목코드 (ITEM_CD) | 사원번호 (EMP_NO) |
|---|---|---|
| W01 | P10001 | E2001 한소율 |
| W01 | P10002 | E2001 한소율 |
| W01 | P10003 | E2002 오민재 |
| W02 | P10001 | E2003 윤가람 |

후보키는 (WH_CD, ITEM_CD)와 (EMP_NO, ITEM_CD)입니다. 모든 컬럼이 후보키에 속하므로 3NF는 만족하지만, EMP_NO → WH_CD에서 EMP_NO는 후보키가 아니므로 BCNF 위반입니다. 한소율이 양산으로 옮기면 두 행을 같이 고쳐야 하고, 담당 품목이 없는 신규 담당자의 소속 창고는 기록할 곳이 없습니다. BCNF로 분해하면 이렇습니다.

```sql
CREATE TABLE lab.tb_wh_emp (            -- 창고담당자: 담당자의 소속 창고
  emp_no  VARCHAR(10) PRIMARY KEY,
  wh_cd   VARCHAR(5)  NOT NULL REFERENCES erp.tb_wh (wh_cd)
);
CREATE TABLE lab.tb_wh_item_emp (       -- 창고품목담당: 담당자가 맡은 품목
  emp_no   VARCHAR(10) NOT NULL REFERENCES lab.tb_wh_emp (emp_no),
  item_cd  VARCHAR(10) NOT NULL REFERENCES erp.tb_item (item_cd),
  PRIMARY KEY (emp_no, item_cd)
);
INSERT INTO lab.tb_wh_emp VALUES ('E2001', 'W01'), ('E2002', 'W01'), ('E2003', 'W02');
INSERT INTO lab.tb_wh_item_emp VALUES
 ('E2001', 'P10001'), ('E2001', 'P10002'), ('E2002', 'P10003'), ('E2003', 'P10001');

-- 분해로 잃은 규칙 "(창고, 품목) -> 담당자 1명"을 점검 쿼리로 지킴 (0건이어야 정상)
SELECT we.wh_cd, ie.item_cd, COUNT(*) AS emp_cnt
  FROM lab.tb_wh_emp we
  JOIN lab.tb_wh_item_emp ie ON ie.emp_no = we.emp_no
 GROUP BY we.wh_cd, ie.item_cd
HAVING COUNT(*) > 1;
```

원래 규칙이 한 테이블 안에 없어서 UNIQUE 제약으로 강제할 수 없게 됐습니다. 정확한 용어로 **종속성 보존(dependency preservation)** 을 잃었다고 합니다. 한소율·오민재·윤가람은 이 Day에서 만든 가상 인물입니다.

### 반정규화 1: 주문 헤더의 파생 컬럼과 대사

영업 화면의 주문 목록은 주문마다 합계금액을 보여 주고, 하루에도 수없이 열립니다. 헤더에 총주문금액(TOT_ORD_AMT)을 두기로 했다고 해 보겠습니다.

```sql
CREATE TABLE lab.tb_ord_dtl AS SELECT * FROM erp.tb_ord_dtl;
ALTER TABLE lab.tb_ord_dtl ADD PRIMARY KEY (ord_no, ord_seq);

CREATE TABLE lab.tb_ord AS
SELECT o.*, (SELECT SUM(d.ord_amt) FROM lab.tb_ord_dtl d WHERE d.ord_no = o.ord_no) AS tot_ord_amt
  FROM erp.tb_ord o;
ALTER TABLE lab.tb_ord ADD PRIMARY KEY (ord_no);

-- 누군가 상세 수량만 정정하고 헤더 합계는 갱신하지 않음
UPDATE lab.tb_ord_dtl SET ord_qty = 25, ord_amt = 25 * uprc
 WHERE ord_no = 'SO2026030004' AND ord_seq = 1;

-- 대사 쿼리: 헤더 합계와 상세 합계가 다른 주문
SELECT o.ord_no, o.tot_ord_amt, COALESCE(SUM(d.ord_amt), 0) AS dtl_sum_amt
  FROM lab.tb_ord o
  LEFT JOIN lab.tb_ord_dtl d ON d.ord_no = o.ord_no
 GROUP BY o.ord_no, o.tot_ord_amt
HAVING o.tot_ord_amt <> COALESCE(SUM(d.ord_amt), 0);
```

SO2026030004가 헤더 64,000원, 상세 80,000원으로 걸립니다. 올바른 갱신 방식은 상세를 바꾸는 같은 트랜잭션 안에서 헤더를 다시 계산하는 것입니다.

```sql
BEGIN;
UPDATE lab.tb_ord_dtl SET ord_qty = 25, ord_amt = 25 * uprc
 WHERE ord_no = 'SO2026030004' AND ord_seq = 1;
UPDATE lab.tb_ord o
   SET tot_ord_amt = (SELECT COALESCE(SUM(d.ord_amt), 0) FROM lab.tb_ord_dtl d WHERE d.ord_no = o.ord_no),
       upd_dtm = CURRENT_TIMESTAMP
 WHERE o.ord_no = 'SO2026030004';
COMMIT;
```

헤더를 "더하기 16,000원"처럼 증감으로 갱신하지 않고 **상세 전체를 다시 합산**한 점에 주목하세요. 증감 방식은 한 번 어긋나면 영원히 어긋나지만, 재합산은 실행할 때마다 스스로 바로잡힙니다.

### 반정규화 2: 일별 집계 테이블과 과거분 재계산

정 과장의 "일별 거래처·품목 주문금액" 화면을 위해 집계 테이블을 둡니다. 표준 약어를 따라 TB_ORD_DAILY로 이름 짓습니다(TB_INV_DAILY와 같은 규칙).

```sql
CREATE TABLE lab.tb_ord_daily (          -- 일별주문집계
  ord_dt    DATE        NOT NULL,
  cust_no   VARCHAR(10) NOT NULL,
  item_cd   VARCHAR(10) NOT NULL,
  ord_qty   NUMERIC(12) NOT NULL,
  ord_amt   NUMERIC(15) NOT NULL,
  load_dtm  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (ord_dt, cust_no, item_cd)
);

INSERT INTO lab.tb_ord_daily (ord_dt, cust_no, item_cd, ord_qty, ord_amt)
SELECT o.ord_dt, o.cust_no, d.item_cd, SUM(d.ord_qty), SUM(d.ord_amt)
  FROM lab.tb_ord o JOIN lab.tb_ord_dtl d ON d.ord_no = o.ord_no
 WHERE o.ord_stat_cd <> '90'
   AND o.ord_dt >= DATE '2026-03-01' AND o.ord_dt < DATE '2026-04-01'
 GROUP BY o.ord_dt, o.cust_no, d.item_cd;

SELECT * FROM lab.tb_ord_daily ORDER BY ord_dt, cust_no, item_cd;
```

3월분 6행이 만들어집니다. 그런데 3월 20일 주문 SO2026030004가 3월 25일에 취소됐습니다. 원천에서 취소된 조합은 집계 원천 쿼리 결과에서 **사라지므로**, 행이 있으면 갱신하고 없으면 넣는 MERGE만으로는 3월 20일 행이 그대로 남습니다. 그래서 영향받은 일자를 통째로 지우고 다시 넣습니다.

```sql
UPDATE lab.tb_ord SET ord_stat_cd = '90', upd_dtm = TIMESTAMP '2026-03-25 10:00:00'
 WHERE ord_no = 'SO2026030004';

-- 지난 실행 이후 변경된 주문의 주문일자만 골라 그 일자를 통째로 재계산 (멱등)
BEGIN;
CREATE TEMP TABLE chg_dt AS
SELECT DISTINCT ord_dt FROM lab.tb_ord
 WHERE upd_dtm >= TIMESTAMP '2026-03-25 00:00:00';

DELETE FROM lab.tb_ord_daily WHERE ord_dt IN (SELECT ord_dt FROM chg_dt);

INSERT INTO lab.tb_ord_daily (ord_dt, cust_no, item_cd, ord_qty, ord_amt)
SELECT o.ord_dt, o.cust_no, d.item_cd, SUM(d.ord_qty), SUM(d.ord_amt)
  FROM lab.tb_ord o JOIN lab.tb_ord_dtl d ON d.ord_no = o.ord_no
 WHERE o.ord_stat_cd <> '90'
   AND o.ord_dt IN (SELECT ord_dt FROM chg_dt)
 GROUP BY o.ord_dt, o.cust_no, d.item_cd;
DROP TABLE chg_dt;
COMMIT;

SELECT ord_dt, COUNT(*) AS row_cnt, SUM(ord_amt) AS ord_amt
  FROM lab.tb_ord_daily GROUP BY ord_dt ORDER BY ord_dt;
```

:::note Oracle 차이
Oracle의 임시 테이블은 `CREATE GLOBAL TEMPORARY TABLE ... ON COMMIT DELETE ROWS`로 미리 만들어 두고 씁니다. 같은 일을 서브쿼리 하나로 처리해도 됩니다. PostgreSQL 17 이상은 `MERGE ... WHEN NOT MATCHED BY SOURCE THEN DELETE`로 사라진 조합을 지울 수 있지만 Oracle MERGE에는 이 절이 없습니다.
:::

3월 20일 행이 사라지고 3월 2일(3행, 142,000원), 3월 10일(2행, 2,160,000원)만 남습니다. 핵심은 두 가지입니다. 재계산 단위를 "변경된 주문의 **업무 일자**"로 잡았다는 점(취소가 일어난 3월 25일이 아니라 주문일자 3월 20일), 그리고 몇 번을 다시 돌려도 결과가 같은 멱등 구조라는 점입니다. 이 패턴은 Day 22의 증분 적재에서 그대로 다시 나옵니다.

## Before / After

**Before: 엑셀을 그대로 올리고, 느린 곳마다 컬럼을 덧붙인 운영계**

| 증상 | 원인 |
|---|---|
| 같은 병원이 두 지역으로 집계됨 | 거래처 속성이 주문 줄마다 반복 (3NF 위반) |
| 신규 약국 등록에 가짜 주문번호 사용 | 삽입 이상 |
| 화면 합계와 상세 합계가 다름 | 파생 컬럼을 만들고 갱신 경로 하나를 빠뜨림 |
| 취소된 주문이 일별 집계에 계속 남음 | MERGE만으로 집계, 사라진 조합 미처리 |
| "어느 값이 맞나" 아무도 모름 | 반정규화 목록·오너·점검 쿼리 없음 |

**After: 3NF를 기본으로, 반정규화는 대장으로 관리**

| 반정규화 항목 | 원천 | 갱신 시점·수단 | 점검 쿼리 | 오너 |
|---|---|---|---|---|
| TB_ORD.TOT_ORD_AMT | SUM(TB_ORD_DTL.ORD_AMT) | 상세 변경과 같은 트랜잭션에서 재합산 | 헤더·상세 합계 대사 (매일) | ERP 운영팀 |
| TB_ORD_DAILY | TB_ORD + TB_ORD_DTL, 취소 제외 | 매일 배치, 변경 주문의 주문일자 단위 DELETE+INSERT | 일자별 원천 합계 대사 | 한빛정보기술 DW팀 |
| TB_ORD.CUST_NM (검토 후 기각) | — | — | — | 주문 당시 이름이 필요 없고 조인 비용이 작아 반정규화하지 않음 |

기각한 항목도 대장에 남깁니다. 같은 요청이 반년 뒤 다시 올라올 때 판단 근거가 되기 때문입니다.

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 어디까지 정규화하나 | 운영계는 기본 3NF | DW 차원은 의도적으로 풀어 스타 스키마로 (Week 3) |
| BCNF까지 갈까 | 결정자 이동이 잦고 삽입 이상이 실제로 생기면 분해 + 점검 쿼리 | 결정자 변경이 드물고 원래 규칙을 UNIQUE로 강제하는 것이 더 중요하면 3NF에서 멈추고 절차 문서화 |
| 종속인지 애매할 때 | 현업이 "예외 없음"을 확인하면 종속으로 보고 분리 | 예외가 있으면 종속이 아님. 거래 줄의 사실로 남김 (단가처럼) |
| 운영계 반정규화 | 운영 화면이 실시간으로 그 값을 쓰고, 갱신 경로가 하나로 모여 있으면 허용 | 분석·보고용이면 운영계는 그대로 두고 DW·마트에서 해결 |
| 정합성 수단 | 갱신 경로가 하나면 같은 트랜잭션 | 경로가 여럿이면 트리거나 배치 재계산, 어느 쪽이든 대사 쿼리 추가 |
| 집계 테이블 갱신 | 과거 원천이 바뀌지 않으면 신규 일자만 추가 | 과거 취소·정정이 있으면 변경된 업무 일자 단위로 통째 재계산 |
| 값이 원천과 다를 때 | 반정규화 값이면 원천 기준으로 동기화 | 시점 스냅샷(주문 당시 거래처명)이면 동기화하지 않음 |

정규화 수준은 "높을수록 좋다"가 아니고, 반정규화는 "느리면 한다"가 아닙니다. 기준은 같습니다. **이 사실이 어디서 바뀌고, 바뀔 때 몇 군데를 누가 고쳐야 하는가.**

## 흔한 실수 3가지

1. **샘플 데이터 모양으로 종속을 판단하고, 거래 시점 값을 마스터로 옮기는 실수.** 지금 데이터에서 우연히 하나뿐이라고 종속으로 보면 안 됩니다. 단가·주문 당시 배송지처럼 거래 줄의 사실을 마스터로 보내면 마스터가 바뀔 때 과거 거래가 변합니다.
2. **반정규화를 하고 갱신 경로를 모두 막지 않는 실수.** 화면 서비스에는 동기화를 넣었는데 수량 정정 배치나 DBA의 직접 UPDATE가 헤더를 건드리지 않으면 바로 어긋납니다. 갱신 경로 목록과 대사 쿼리가 없는 반정규화는 시한폭탄입니다.
3. **집계 테이블을 "증분으로 더하기"나 MERGE만으로 유지하는 실수.** 과거 주문이 취소·정정되면 사라진 조합이 남거나 금액이 이중으로 더해집니다. 영향 범위(업무 일자)를 통째로 다시 계산하는 멱등 구조로 만듭니다.

## 셀프 체크 질문

**Q1. 2NF와 3NF의 차이를 주문 엑셀 예시로 설명해 보세요.**

:::answer 모범 답안 보기
둘 다 "키가 아닌 것에 종속된 속성"을 없애지만 무엇에 종속되었는지가 다릅니다. 2NF는 복합키 (ORD_NO, ORD_SEQ)의 일부인 ORD_NO에만 종속된 속성, 즉 주문일자·거래처·담당자를 주문 헤더로 분리합니다. 3NF는 키가 아닌 속성을 거쳐 정해지는 속성, 즉 CUST_NO를 거쳐 정해지는 거래처명·지역, ITEM_CD를 거쳐 정해지는 품목명을 각 마스터로 분리합니다. 2NF만 하면 청솔내과의원이 두 번 주문할 때 거래처 정보가 주문마다 반복되고, 3NF까지 해야 거래처 정보가 한 곳에만 남습니다.
:::

**Q2. 정 과장이 "주문 목록 화면이 느리니 헤더에 합계금액 컬럼을 넣어 달라"고 합니다. 어떻게 판단하고, 넣는다면 무엇을 같이 설계하겠습니까?**

:::answer 모범 답안 보기
먼저 더 싼 대안을 봅니다. 상세 테이블의 PK 인덱스로 주문별 합산이 충분히 빠른지, 화면 쿼리가 불필요하게 전체를 읽고 있지 않은지 확인합니다. 그래도 화면 빈도가 높고 집계 비용이 크며, 상세를 바꾸는 경로가 주문 서비스 하나로 모여 있다면 반정규화를 허용합니다. 넣는다면 세 가지를 같이 설계합니다. 상세를 바꾸는 모든 경로(화면, 정정 배치, 인터페이스)에서 같은 트랜잭션으로 헤더를 재합산하는 규칙, 헤더 합계와 상세 합계를 매일 비교하는 대사 쿼리, 그리고 반정규화 대장에 원천·갱신 수단·오너를 기록하는 것입니다. 분석용 요구라면 운영계 대신 DW 마트에서 해결하자고 제안합니다.
:::

**Q3. BCNF 분해를 하면 무엇을 잃습니까? 그래도 분해할지 어떻게 결정합니까?**

:::answer 모범 답안 보기
종속성 보존을 잃을 수 있습니다. 한빛로지스 예시에서 BCNF로 나누면 "한 창고의 한 품목은 담당자 한 명"이라는 규칙이 한 테이블 안에 없어서 UNIQUE 제약으로 강제할 수 없고 점검 쿼리로 지켜야 합니다. 담당자의 소속 창고 변경이나 품목 없는 담당자 등록이 자주 일어나 이상현상이 실제 비용이 된다면 분해하고 점검 쿼리를 품질 규칙으로 등록합니다. 소속 변경이 드물고 원래 규칙을 DB가 강제하는 것이 더 중요하다면 3NF에서 멈추고, 소속 변경 시 관련 행을 함께 바꾸는 절차를 운영 가이드에 적습니다.
:::

## 오늘의 과제

**과제 1.** 3월 2일 청솔내과의원 주문 SO2026030002가 뒤늦게 취소됐습니다(`lab.tb_ord`에서 상태를 90으로, `upd_dtm`을 2026-03-28 09:00으로 바꾸세요). 그다음 (1) `lab.tb_ord_daily`와 원천(`lab.tb_ord` + `lab.tb_ord_dtl`, 취소 제외)의 일자별 금액을 대사해 차이 나는 일자만 보여 주는 쿼리를 쓰고, (2) 차이 난 일자만 재계산한 뒤, (3) 대사 쿼리를 다시 돌려 0건임을 확인하세요. (1)의 결과 모양은 `ord_dt, daily_amt, src_amt` 1행입니다.

:::answer 해설 보기
대사 쿼리는 양쪽을 각각 일자별로 집계한 뒤 FULL OUTER JOIN 합니다. 한쪽에만 있는 일자도 잡아야 하기 때문입니다. 재계산은 본문과 같은 "업무 일자 단위 DELETE + INSERT"입니다.

```sql
UPDATE lab.tb_ord SET ord_stat_cd = '90', upd_dtm = TIMESTAMP '2026-03-28 09:00:00'
 WHERE ord_no = 'SO2026030002';

-- (1) 대사: 차이 나는 일자
WITH daily AS (
  SELECT ord_dt, SUM(ord_amt) AS amt FROM lab.tb_ord_daily GROUP BY ord_dt
), src AS (
  SELECT o.ord_dt, SUM(d.ord_amt) AS amt
    FROM lab.tb_ord o JOIN lab.tb_ord_dtl d ON d.ord_no = o.ord_no
   WHERE o.ord_stat_cd <> '90'
     AND o.ord_dt >= DATE '2026-03-01' AND o.ord_dt < DATE '2026-04-01'
   GROUP BY o.ord_dt
)
SELECT COALESCE(a.ord_dt, s.ord_dt) AS ord_dt,
       COALESCE(a.amt, 0) AS daily_amt,
       COALESCE(s.amt, 0) AS src_amt
  FROM daily a FULL OUTER JOIN src s ON s.ord_dt = a.ord_dt
 WHERE COALESCE(a.amt, 0) <> COALESCE(s.amt, 0);
```

결과는 2026-03-02, daily_amt 142,000, src_amt 82,000입니다.

```sql
-- (2) 차이 난 일자 재계산
BEGIN;
DELETE FROM lab.tb_ord_daily WHERE ord_dt = DATE '2026-03-02';
INSERT INTO lab.tb_ord_daily (ord_dt, cust_no, item_cd, ord_qty, ord_amt)
SELECT o.ord_dt, o.cust_no, d.item_cd, SUM(d.ord_qty), SUM(d.ord_amt)
  FROM lab.tb_ord o JOIN lab.tb_ord_dtl d ON d.ord_no = o.ord_no
 WHERE o.ord_stat_cd <> '90' AND o.ord_dt = DATE '2026-03-02'
 GROUP BY o.ord_dt, o.cust_no, d.item_cd;
COMMIT;

-- (3) 다시 대사: 0건이어야 정상
WITH daily AS (
  SELECT ord_dt, SUM(ord_amt) AS amt FROM lab.tb_ord_daily GROUP BY ord_dt
), src AS (
  SELECT o.ord_dt, SUM(d.ord_amt) AS amt
    FROM lab.tb_ord o JOIN lab.tb_ord_dtl d ON d.ord_no = o.ord_no
   WHERE o.ord_stat_cd <> '90'
     AND o.ord_dt >= DATE '2026-03-01' AND o.ord_dt < DATE '2026-04-01'
   GROUP BY o.ord_dt
)
SELECT COALESCE(a.ord_dt, s.ord_dt) AS ord_dt, a.amt AS daily_amt, s.amt AS src_amt
  FROM daily a FULL OUTER JOIN src s ON s.ord_dt = a.ord_dt
 WHERE COALESCE(a.amt, 0) <> COALESCE(s.amt, 0);
```

대사 쿼리를 배치 마지막 단계에 붙여 두면 "재계산 범위를 잘못 잡은" 실수도 다음 날 아침에 발견됩니다. 반정규화의 정합성은 갱신 로직과 대사 쿼리, 두 겹으로 지킵니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 요구사항정의서 / 인터뷰 기록 | 함수 종속의 근거가 되는 업무 규칙(예: "담당자는 한 창고에만 소속된다 — 한 대리 확인"), 화면별 조회 빈도와 응답 요구. |
| 논리 ERD | 3NF 기준 엔터티와 관계. 의도적으로 정규화하지 않은 곳(ORD_AMT 등)은 주석으로 이유를 답니다. |
| 물리 ERD / 테이블정의서 | 반정규화 컬럼·테이블 표시, 파생 산식, "동기화 대상(반정규화)인지 시점 스냅샷인지" 구분. |
| 반정규화 대장 | 항목, 원천, 도입 이유(빈도·비용), 갱신 시점·수단, 점검 쿼리, 오너, 기각 항목과 사유. |
| 이관 설계서 | 엑셀 → 스테이징 → 정규화 테이블 순서, 반례 점검 쿼리, 반례 발생 시 처리 절차(적재 중단, 오너 확인). |
| 데이터 품질 규칙 목록 | CUST_NO → RGN_CD 반례, 헤더·상세 합계 대사, 집계 테이블 대사, 창고·품목별 담당자 1명 규칙. |
| 배치 설계서 | 집계 테이블 재계산 범위(변경 주문의 업무 일자), 멱등 처리 방식, 실행 순서. |

## 참고할 원전

- E. F. Codd, "A Relational Model of Data for Large Shared Data Banks", Communications of the ACM, 1970 — 관계 모델과 정규화의 출발점.
- Graeme Simsion, Graham Witt, "Data Modeling Essentials", 3rd ed. (Morgan Kaufmann, 2005) — 기본 정규화와 고급 정규화를 다루는 장들.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 모델링 영역(정규화), 데이터베이스 설계와 이용 영역(반정규화, 성능 설계).
