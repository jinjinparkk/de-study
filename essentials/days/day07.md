# Day 7. 이력 모델링

## 오늘의 한 줄

이력 모델링은 "그때 그 값이 무엇이었나"에 답할 수 있게 시간을 데이터에 넣는 일입니다. 어떤 질문을 받을지에 따라 선분이력, 시점이력, 스냅샷, 변경로그 중 하나를 고르고, 기간의 경계 규칙을 하나로 정해 끝까지 지키는 것이 핵심입니다.

## 왜 중요한가

품목 테이블에 현재 단가만 두면, 4월 1일 기준가가 바뀌는 순간 "3월 주문의 단가가 맞게 적용됐나"를 검증할 방법이 사라집니다. 선분이력을 두었더라도 누군가 종료일을 닫지 않고 새 행을 넣으면 같은 날짜에 단가가 두 개가 되고, 주문과 조인할 때 행이 두 배로 불어나 매출이 부풀어 보입니다. 종료일을 "그날까지 포함"으로 쓰는 사람과 "그날 전까지"로 쓰는 사람이 섞이면 경계일 하루치 데이터가 비거나 겹칩니다. 이력은 만드는 것보다 **규칙을 지키게 하는 것**이 어렵습니다.

## 핵심 개념

### 1. 이력의 네 가지 형태

쉽게 말하면 이력은 "언제부터 언제까지 이 값"(선분), "이때 이 값으로 바뀜"(시점), "매일 찍은 사진"(스냅샷), "누가 무엇을 바꿨나"(변경로그) 네 가지로 남길 수 있습니다.

| 형태 | 저장하는 것 | 잘 답하는 질문 | 한빛제약그룹 예시 |
|---|---|---|---|
| 선분이력 | 적용시작일자 ~ 적용종료일자 + 값 | "3월 15일의 기준가는?" (한 행으로 바로) | TB_ITEM_UPRC_HIST, TB_CUST_EMP_HIST, TB_BOM |
| 시점이력 | 변경일자(=시작일자) + 값, 종료일 없음 | "언제 바뀌었나?" | 시작일만 있는 단가 테이블 (아래 예시) |
| 스냅샷 | 매 시점의 상태 전체 | "3월 31일 마감 재고는?" | TB_INV_DAILY |
| 변경로그 | 변경 전 값, 변경 후 값, 변경 일시, 변경자 | "누가 언제 이 단가를 고쳤나?" | 단가 변경로그 (아래 예시) |

선분이력과 시점이력은 **업무 유효 시간**(이 값이 업무상 언제 적용되는가)을, 변경로그는 **기록 시간**(DB에 언제 기록됐는가)을 남깁니다. 두 시간은 다릅니다. 4월 1일부터 적용할 단가를 3월 25일에 미리 등록할 수 있고, 반대로 3월부터 소급 적용할 단가를 4월에 등록할 수도 있습니다. 두 시간을 모두 관리하는 구조를 정확한 용어로 이원 시간(bitemporal) 모델이라고 부릅니다.

### 2. 선분이력의 경계 규칙: 이 과정의 약속

선분이력에서 가장 많은 사고는 **종료일을 포함하느냐 마느냐**가 섞여서 생깁니다. 이 과정과 공통 스키마는 아래 규칙을 따릅니다.

:::summary 이 과정의 선분이력 규칙 (TB_ITEM_UPRC_HIST, TB_CUST_EMP_HIST, TB_BOM 공통)
- 시작일자와 종료일자는 시각이 없는 `DATE`입니다.
- **종료일 포함**: APLY_END_DT 당일까지 유효합니다. 특정 일자 조회는 `기준일 BETWEEN APLY_STRT_DT AND APLY_END_DT`.
- 현재 유효한 행의 종료일은 `DATE '9999-12-31'`. NULL을 쓰지 않습니다.
- 다음 행의 시작일 = 이전 행의 종료일 + 1일. 겹침도 빈틈도 없어야 합니다.
- 같은 키(예: 품목 + 단가유형)에 대해 어떤 날짜든 유효한 행은 정확히 하나입니다.
- 시각이 있는 이력(일시, DTM)은 예외로 **반열림 구간**(시작 포함, 종료 미포함, `>=` 와 `<`)을 씁니다.
:::

종료일 포함을 고른 이유는 두 가지입니다. 현업이 "6월 30일까지 적용"이라고 말하는 방식과 같아서 정의서와 화면이 일치하고, 날짜 단위 데이터에서는 BETWEEN 한 줄로 조회가 끝납니다. 대신 시각이 있는 데이터에 같은 규칙을 쓰면 '23:59:59'처럼 끝 시각을 흉내 내야 하고 그 사이 1초가 빕니다. 그래서 일시 이력만 반열림으로 예외를 둡니다. 어느 쪽을 고르든 중요한 것은 **한 시스템 안에서 하나로 통일하고 표준 문서에 적는 것**입니다.

현재 행 종료일에 NULL 대신 9999-12-31을 쓰는 이유도 같습니다. NULL이면 모든 조회에 `COALESCE(APLY_END_DT, ...)`나 `OR APLY_END_DT IS NULL`이 붙고, 하나라도 빠뜨리면 현재 행이 조회에서 사라집니다.

### 3. 선분 정합성: DB가 막지 못하는 것

선분이력의 PK는 보통 (품목코드, 단가유형코드, 적용시작일자)입니다. 이 PK는 "같은 시작일 중복"만 막을 뿐, **기간 겹침**은 막지 못합니다. 2025-01-01 시작 행과 2026-05-01 시작 행이 둘 다 9999-12-31까지 유효해도 PK는 통과합니다.

Oracle에는 기간 겹침을 막는 선언적 제약이 없습니다. PostgreSQL에는 배제 제약(EXCLUDE)이 있지만 계열사 ERP는 Oracle이므로, 실무에서는 세 겹으로 지킵니다. 변경은 정해진 절차(이전 행 닫기 + 새 행 넣기를 한 트랜잭션)로만 하고, CHECK (시작일 <= 종료일)을 걸고, 겹침·빈틈 점검 쿼리를 품질 규칙으로 매일 돌립니다.

### 4. 어떤 형태를 고를까

| 질문의 모양 | 고를 형태 | 이유 |
|---|---|---|
| "그날의 값"을 자주 조인 | 선분이력 | BETWEEN 한 번으로 조인, 인덱스 활용 쉬움 |
| 변경이 드물고 "언제 바뀌었나"가 주 관심 | 시점이력 | 저장이 단순, 종료일 관리 부담 없음. 대신 조회가 복잡 |
| 상태 전체를 시점별로 비교 (재고, 잔액) | 스냅샷 | 계산 없이 그 시점 값이 바로 있음. 대신 저장량이 큼 |
| 감사·추적 (누가, 언제, 무엇을) | 변경로그 | 업무 유효 시간이 아니라 기록 시간을 남김 |

실무에서는 하나만 쓰지 않습니다. 단가는 **선분이력(조회용) + 변경로그(감사용)** 를 함께 두는 경우가 많습니다.

## 예시

### 특정 일자 기준 단가 조회

공통 스키마의 품목단가이력은 다음과 같습니다(모두 가상 값).

| 품목코드 (ITEM_CD) | 단가유형 (UPRC_TP_CD) | 적용시작일자 (APLY_STRT_DT) | 적용종료일자 (APLY_END_DT) | 단가 (UPRC) |
|---|---|---|---|---|
| P10001 | 01 기준가 | 2025-01-01 | 2026-03-31 | 3,200 |
| P10001 | 01 기준가 | 2026-04-01 | 9999-12-31 | 3,000 |
| P10001 | 02 보험상한가 | 2025-01-01 | 9999-12-31 | 3,500 |
| P10002 | 01 기준가 | 2025-01-01 | 9999-12-31 | 12,000 |
| P10003 | 01 기준가 | 2025-07-01 | 9999-12-31 | 2,500 |

```sql
-- 한빛펜정의 3월 15일, 4월 15일 기준 단가 (기준가·보험상한가)
SELECT d.base_dt, h.uprc_tp_cd, h.uprc
  FROM (VALUES (DATE '2026-03-15'), (DATE '2026-04-15')) AS d (base_dt)
  JOIN erp.tb_item_uprc_hist h
    ON h.item_cd = 'P10001'
   AND d.base_dt BETWEEN h.aply_strt_dt AND h.aply_end_dt
 ORDER BY d.base_dt, h.uprc_tp_cd;
```

:::note Oracle 차이
Oracle 23ai 이전에는 `FROM (VALUES ...)` 파생 테이블을 쓸 수 없습니다. `SELECT DATE '2026-03-15' AS base_dt FROM DUAL UNION ALL SELECT DATE '2026-04-15' FROM DUAL`로 대신합니다.
:::

3월 15일은 기준가 3,200원·보험상한가 3,500원, 4월 15일은 기준가 3,000원·보험상한가 3,500원입니다.

이력의 진짜 쓰임은 거래와의 조인입니다. 주문 단가가 주문일자의 기준가와 맞게 들어갔는지 검증합니다.

```sql
-- 주문상세 단가 vs 주문일자 기준가 (차이가 있으면 할인·오류 확인 대상)
SELECT o.ord_no, o.ord_dt, d.ord_seq, d.item_cd,
       d.uprc AS ord_uprc, h.uprc AS base_uprc, d.uprc - h.uprc AS diff
  FROM erp.tb_ord o
  JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
  LEFT JOIN erp.tb_item_uprc_hist h
         ON h.item_cd = d.item_cd
        AND h.uprc_tp_cd = '01'
        AND o.ord_dt BETWEEN h.aply_strt_dt AND h.aply_end_dt
 ORDER BY o.ord_no, d.ord_seq;
```

8행 모두 차이가 0입니다. 3월 주문의 한빛펜정은 3,200원, 4월 3일 주문(SO2026040001)은 3,000원으로 들어갔습니다. 이 조인이 정확히 주문상세 행 수만큼 나온다는 것이 곧 "선분이 겹치지 않는다"는 증거이기도 합니다. 겹치는 선분이 하나라도 있으면 이 쿼리의 행 수가 늘어납니다.

### 선분 겹침·빈틈 검증

일부러 잘못된 데이터를 넣어 봅니다. 운영계는 그대로 두고 `lab`에 복사본을 만듭니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;
CREATE TABLE lab.tb_item_uprc_hist (LIKE erp.tb_item_uprc_hist INCLUDING ALL);
INSERT INTO lab.tb_item_uprc_hist SELECT * FROM erp.tb_item_uprc_hist;
ALTER TABLE lab.tb_item_uprc_hist
  ADD CONSTRAINT ck_item_uprc_hist_01 CHECK (aply_strt_dt <= aply_end_dt);

-- 실수 1: 한빛록스정 5월 인상분을 넣으면서 기존 행을 닫지 않음 (겹침)
INSERT INTO lab.tb_item_uprc_hist VALUES ('P10002', '01', DATE '2026-05-01', DATE '9999-12-31', 12500);
-- 실수 2: 한빛시럽 보험상한가를 등록하면서 2월 28일 하루를 비움 (빈틈)
INSERT INTO lab.tb_item_uprc_hist VALUES
 ('P10003', '02', DATE '2025-07-01', DATE '2026-02-27', 2800),
 ('P10003', '02', DATE '2026-03-01', DATE '9999-12-31', 2900);
```

두 INSERT 모두 PK를 통과했습니다. 점검 쿼리로 찾습니다.

```sql
-- 겹침: 같은 키에서 뒤 행의 시작일이 앞 행의 기간 안에 들어오는 쌍
SELECT a.item_cd, a.uprc_tp_cd,
       a.aply_strt_dt AS a_strt, a.aply_end_dt AS a_end,
       b.aply_strt_dt AS b_strt, b.aply_end_dt AS b_end
  FROM lab.tb_item_uprc_hist a
  JOIN lab.tb_item_uprc_hist b
    ON b.item_cd = a.item_cd
   AND b.uprc_tp_cd = a.uprc_tp_cd
   AND b.aply_strt_dt > a.aply_strt_dt
   AND b.aply_strt_dt <= a.aply_end_dt;

-- 겹침과 빈틈을 한 번에: 다음 행 시작일이 "종료일 + 1"이 아닌 곳
SELECT item_cd, uprc_tp_cd, aply_strt_dt, aply_end_dt, next_strt_dt,
       CASE WHEN next_strt_dt <= aply_end_dt THEN 'OVERLAP' ELSE 'GAP' END AS issue_tp
  FROM (SELECT h.*,
               LEAD(aply_strt_dt) OVER (PARTITION BY item_cd, uprc_tp_cd ORDER BY aply_strt_dt) AS next_strt_dt
          FROM lab.tb_item_uprc_hist h) x
 WHERE next_strt_dt IS NOT NULL
   AND next_strt_dt <> aply_end_dt + 1;

-- 현재 유효 행(9999-12-31)이 키마다 정확히 1개인가
SELECT item_cd, uprc_tp_cd, COUNT(*) AS open_cnt
  FROM lab.tb_item_uprc_hist
 WHERE aply_end_dt = DATE '9999-12-31'
 GROUP BY item_cd, uprc_tp_cd
HAVING COUNT(*) <> 1;
```

| item_cd | uprc_tp_cd | aply_strt_dt | aply_end_dt | next_strt_dt | issue_tp |
|---|---|---|---|---|---|
| P10002 | 01 | 2025-01-01 | 9999-12-31 | 2026-05-01 | OVERLAP |
| P10003 | 02 | 2025-07-01 | 2026-02-27 | 2026-03-01 | GAP |

세 번째 쿼리는 P10002 기준가의 현재 행이 2개라고 알려 줍니다. `aply_end_dt + 1`은 날짜에 하루를 더하는 식이며 Oracle과 PostgreSQL 모두 같은 의미입니다.

### 변경로그를 붙이고, 정해진 절차로 고치기

감사용 변경로그를 먼저 붙입니다. 단가는 금액에 직접 영향을 주므로 "누가 언제 바꿨나"를 남기는 것이 일반적입니다.

```sql
CREATE TABLE lab.tb_item_uprc_chg_log (       -- 품목단가변경로그
  chg_seq         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  chg_dtm         TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  chg_tp_cd       CHAR(1)     NOT NULL,       -- I 등록, U 수정, D 삭제
  item_cd         VARCHAR(10) NOT NULL,
  uprc_tp_cd      VARCHAR(2)  NOT NULL,
  aply_strt_dt    DATE        NOT NULL,
  bf_aply_end_dt  DATE,
  af_aply_end_dt  DATE,
  bf_uprc         NUMERIC(15),
  af_uprc         NUMERIC(15),
  chg_id          VARCHAR(30) NOT NULL DEFAULT CURRENT_USER
);

CREATE FUNCTION lab.fn_item_uprc_chg_log() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF TG_OP = 'INSERT' THEN
    INSERT INTO lab.tb_item_uprc_chg_log (chg_tp_cd, item_cd, uprc_tp_cd, aply_strt_dt, af_aply_end_dt, af_uprc)
    VALUES ('I', NEW.item_cd, NEW.uprc_tp_cd, NEW.aply_strt_dt, NEW.aply_end_dt, NEW.uprc);
    RETURN NEW;
  ELSIF TG_OP = 'UPDATE' THEN
    INSERT INTO lab.tb_item_uprc_chg_log (chg_tp_cd, item_cd, uprc_tp_cd, aply_strt_dt,
                                          bf_aply_end_dt, af_aply_end_dt, bf_uprc, af_uprc)
    VALUES ('U', NEW.item_cd, NEW.uprc_tp_cd, NEW.aply_strt_dt,
            OLD.aply_end_dt, NEW.aply_end_dt, OLD.uprc, NEW.uprc);
    RETURN NEW;
  ELSE
    INSERT INTO lab.tb_item_uprc_chg_log (chg_tp_cd, item_cd, uprc_tp_cd, aply_strt_dt, bf_aply_end_dt, bf_uprc)
    VALUES ('D', OLD.item_cd, OLD.uprc_tp_cd, OLD.aply_strt_dt, OLD.aply_end_dt, OLD.uprc);
    RETURN OLD;
  END IF;
END $$;

CREATE TRIGGER trg_item_uprc_chg_log
AFTER INSERT OR UPDATE OR DELETE ON lab.tb_item_uprc_hist
FOR EACH ROW EXECUTE FUNCTION lab.fn_item_uprc_chg_log();
```

:::note Oracle 차이
Oracle에서는 `CREATE OR REPLACE TRIGGER ... AFTER INSERT OR UPDATE OR DELETE ON TB_ITEM_UPRC_HIST FOR EACH ROW`로 쓰고, 본문에서 `INSERTING`/`UPDATING`/`DELETING`과 `:NEW`/`:OLD`를 씁니다. 변경자는 `USER` 또는 애플리케이션이 넘긴 사용자 ID를 씁니다.
:::

이제 잘못된 행을 정해진 절차로 바로잡습니다. 단가 변경 절차는 "잘못 넣은 행 정리 → 현재 행 닫기 → 새 행 넣기"를 **한 트랜잭션**으로 처리하는 것입니다.

```sql
BEGIN;
-- 1) 닫지 않고 넣었던 5월 행을 지움
DELETE FROM lab.tb_item_uprc_hist
 WHERE item_cd = 'P10002' AND uprc_tp_cd = '01' AND aply_strt_dt = DATE '2026-05-01';
-- 2) 현재 행을 새 시작일 전날로 닫음 (새 시작일보다 앞에서 시작한 현재 행만)
UPDATE lab.tb_item_uprc_hist
   SET aply_end_dt = DATE '2026-05-01' - 1
 WHERE item_cd = 'P10002' AND uprc_tp_cd = '01'
   AND aply_end_dt = DATE '9999-12-31'
   AND aply_strt_dt < DATE '2026-05-01';
-- 3) 새 행을 현재 행으로 넣음
INSERT INTO lab.tb_item_uprc_hist VALUES ('P10002', '01', DATE '2026-05-01', DATE '9999-12-31', 12500);
-- 빈틈: 한빛시럽 보험상한가 앞 행 종료일을 2월 28일로 정정
UPDATE lab.tb_item_uprc_hist
   SET aply_end_dt = DATE '2026-02-28'
 WHERE item_cd = 'P10003' AND uprc_tp_cd = '02' AND aply_strt_dt = DATE '2025-07-01';
COMMIT;

-- 다시 점검: 0건이어야 정상
SELECT item_cd, uprc_tp_cd, aply_strt_dt, aply_end_dt, next_strt_dt
  FROM (SELECT h.*,
               LEAD(aply_strt_dt) OVER (PARTITION BY item_cd, uprc_tp_cd ORDER BY aply_strt_dt) AS next_strt_dt
          FROM lab.tb_item_uprc_hist h) x
 WHERE next_strt_dt IS NOT NULL
   AND next_strt_dt <> aply_end_dt + 1;

-- 변경로그: 언제 누가 무엇을 바꿨나
SELECT chg_seq, chg_tp_cd, item_cd, uprc_tp_cd, aply_strt_dt,
       bf_aply_end_dt, af_aply_end_dt, bf_uprc, af_uprc
  FROM lab.tb_item_uprc_chg_log
 ORDER BY chg_seq;
```

변경로그에는 정정 과정의 삭제 1건(D: 잘못 들어갔던 5월 12,500원 행), 수정 2건(U: 기존 행 종료일 9999-12-31 → 2026-04-30, 시럽 종료일 2월 27일 → 28일), 등록 1건(I)이 순서대로 남습니다. 선분이력만 보면 지금은 깨끗하지만, 변경로그는 "5월 인상분이 한 번 잘못 등록됐다가 정정됐다"는 사실까지 보여 줍니다. 감사 대응에 필요한 것이 바로 이 기록입니다.

반대로 처음의 잘못된 등록 3건은 로그에 없습니다. 트리거를 그 뒤에 만들었기 때문입니다. 변경로그는 테이블을 만들 때 **처음부터** 붙여야 하며, 나중에 붙이면 그 전의 변경은 영영 알 수 없다는 점을 이 결과가 그대로 보여 줍니다.

### 같은 데이터를 시점이력으로 두면

종료일 없이 시작일만 저장하는 방식입니다. 종료일은 조회 때 다음 행의 시작일로 계산합니다.

```sql
CREATE TABLE lab.tb_item_uprc_pnt AS        -- 시점이력 버전 (종료일 없음)
SELECT item_cd, uprc_tp_cd, aply_strt_dt, uprc FROM erp.tb_item_uprc_hist;

-- 시점이력에서 선분을 복원
SELECT item_cd, uprc_tp_cd, aply_strt_dt,
       COALESCE(LEAD(aply_strt_dt) OVER (PARTITION BY item_cd, uprc_tp_cd ORDER BY aply_strt_dt) - 1,
                DATE '9999-12-31') AS derived_end_dt,
       uprc
  FROM lab.tb_item_uprc_pnt
 ORDER BY item_cd, uprc_tp_cd, aply_strt_dt;

-- 시점이력에서 특정 일자 단가: "기준일 이전의 가장 최근 시작일" 행
SELECT p.item_cd, p.uprc
  FROM lab.tb_item_uprc_pnt p
 WHERE p.uprc_tp_cd = '01'
   AND p.aply_strt_dt = (SELECT MAX(q.aply_strt_dt)
                           FROM lab.tb_item_uprc_pnt q
                          WHERE q.item_cd = p.item_cd
                            AND q.uprc_tp_cd = p.uprc_tp_cd
                            AND q.aply_strt_dt <= DATE '2026-04-15')
 ORDER BY p.item_cd;
```

시점이력은 겹침이 구조적으로 생기지 않는다는 장점이 있습니다(종료일이 없으니까요). 대신 "그날의 값"을 구할 때마다 서브쿼리나 윈도 함수가 필요하고, 주문 수만 건과 조인하면 비용이 큽니다. 그래서 조회가 잦은 단가는 선분이력, 변경이 드물고 조회가 적은 속성은 시점이력이 어울립니다.

### 스냅샷과 담당 이력

```sql
-- 스냅샷: 3월 31일 마감 기준 창고·품목별 재고 (로트 합산)
SELECT inv_dt, wh_cd, item_cd, SUM(inv_qty) AS inv_qty
  FROM erp.tb_inv_daily
 WHERE inv_dt = DATE '2026-03-31'
 GROUP BY inv_dt, wh_cd, item_cd
 ORDER BY item_cd;

-- 선분이력: 청솔내과의원의 3월 10일, 3월 20일 담당자
SELECT d.base_dt, h.emp_no, e.emp_nm
  FROM (VALUES (DATE '2026-03-10'), (DATE '2026-03-20')) AS d (base_dt)
  JOIN erp.tb_cust_emp_hist h
    ON h.cust_no = 'C000101'
   AND d.base_dt BETWEEN h.aply_strt_dt AND h.aply_end_dt
  JOIN erp.tb_emp e ON e.emp_no = h.emp_no
 ORDER BY d.base_dt;
```

스냅샷은 같은 날짜 안에서 로트·창고를 합치는 것은 괜찮지만, **여러 날짜의 스냅샷을 더하면 안 됩니다.** 3월 30일 재고와 31일 재고를 더한 값에는 아무 뜻이 없습니다(Day 17 반가산 팩트). 담당 이력은 3월 10일 김도윤(E1001), 3월 20일 이서연(E1002)입니다. 이 선분이력이 Day 19에서 DW의 SCD Type 2로 이어집니다.

## Before / After

**Before: 현재 단가만 두고, 바뀌면 덮어쓰는 설계**

```text
TB_ITEM (ITEM_CD, ITEM_NM, ..., UPRC)   -- 4/1 UPDATE 3,200 -> 3,000
```

| 질문 | 답할 수 있나 |
|---|---|
| 3월 주문 단가가 당시 기준가와 맞나? | 불가. 3월 기준가가 사라짐 |
| 기준가가 언제 바뀌었나? | 불가 |
| 누가 바꿨나? | 불가 |
| 다음 달부터 적용할 단가를 미리 등록 | 불가. 등록하는 순간 오늘부터 적용됨 |

**After: 선분이력 + 경계 규칙 + 변경 절차 + 변경로그 + 점검 쿼리**

| 구성 요소 | 내용 |
|---|---|
| 선분이력 | TB_ITEM_UPRC_HIST, PK (ITEM_CD, UPRC_TP_CD, APLY_STRT_DT) |
| 경계 규칙 | DATE, 종료일 포함, 현재 = 9999-12-31, 다음 시작 = 종료 + 1 |
| 변경 절차 | 현재 행 닫기 + 새 행 넣기를 한 트랜잭션 (미래 일자 등록 가능) |
| 변경로그 | TB_ITEM_UPRC_CHG_LOG (변경 전후 값, 일시, 변경자) |
| 점검 | CHECK (시작 <= 종료), 겹침·빈틈 쿼리, 현재 행 1개 쿼리를 매일 실행 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 선분 vs 시점 | "그날의 값"을 거래와 자주 조인하면 선분이력 | 변경이 드물고 조회가 적으면 시점이력 (겹침 걱정 없음) |
| 종료일 포함 vs 미포함 | 날짜(DATE) 단위 업무 이력이면 종료일 포함 + BETWEEN | 시각(DTM) 단위 이력, 로그, 스트림이면 반열림 `>=`, `<` |
| 현재 행 종료일 | 기본은 9999-12-31 | 기존 시스템이 NULL을 쓰고 있으면 DW 적재 시 9999-12-31로 변환하고 매핑정의서에 명시 |
| 스냅샷 vs 수불 재계산 | 시점 상태 비교가 많고 원천이 마감 스냅샷을 주면 스냅샷 | 저장량이 부담이거나 소급 정정이 잦으면 거래로 재계산 (기초재고 확보 필요, Day 2) |
| 변경로그 필요성 | 금액·가격·권한처럼 감사 대상이면 필수 | 단순 참고 속성이면 선분이력의 감사 컬럼(UPD_DTM, UPD_ID)으로 충분 |
| 소급 정정이 잦을 때 | 업무 유효 시간만으로 충분하면 선분 + 변경로그 | "당시 우리가 알던 값"까지 재현해야 하면 이원 시간(유효 시간 + 기록 시간) 설계 |

## 흔한 실수 3가지

1. **종료일 규칙을 사람마다 다르게 쓰는 실수.** 어떤 화면은 종료일 포함, 어떤 배치는 미포함으로 처리하면 경계일 하루가 겹치거나 빕니다. 규칙을 표준 문서와 테이블정의서에 한 줄로 적고, 모든 조회를 그 규칙으로 통일합니다.
2. **새 행만 넣고 이전 행을 닫지 않는 실수.** PK는 통과하므로 아무도 모르다가 주문과 조인할 때 행이 두 배가 되어 매출이 부풀어 보입니다. 변경은 "닫기 + 넣기" 한 트랜잭션 절차로만 하고, 겹침 점검 쿼리를 매일 돌립니다.
3. **스냅샷을 여러 날짜에 걸쳐 합산하는 실수.** 월간 재고를 "일별 재고의 합"으로 내면 아무 의미 없는 큰 숫자가 나옵니다. 스냅샷은 기간 말 값이나 기간 평균으로 봅니다.

## 셀프 체크 질문

**Q1. 이 과정이 선분이력 종료일을 "포함"으로 정한 이유와, 예외를 두는 경우를 설명해 보세요.**

:::answer 모범 답안 보기
업무 이력은 날짜(DATE) 단위이고, 현업이 "6월 30일까지 적용"처럼 종료일을 포함해 말하기 때문입니다. 정의서·화면·데이터가 같은 표현을 쓰고, 조회는 `기준일 BETWEEN 시작일 AND 종료일` 한 줄로 끝납니다. 다음 행의 시작일은 종료일 + 1이라는 규칙도 단순합니다. 예외는 시각이 있는 이력입니다. 일시 데이터에 종료 포함을 쓰면 끝 시각을 '23:59:59'처럼 흉내 내야 하고 그 사이가 빕니다. 그래서 일시 이력과 로그는 시작 포함·종료 미포함의 반열림 구간을 씁니다. 핵심은 어느 쪽이든 시스템 안에서 하나로 통일하고 표준에 적는 것입니다.
:::

**Q2. 선분이력 PK가 (품목, 단가유형, 적용시작일자)인데도 기간이 겹칠 수 있는 이유와, 겹침을 어떻게 막겠습니까?**

:::answer 모범 답안 보기
PK는 같은 시작일이 두 번 들어오는 것만 막습니다. 시작일이 다르면 두 행의 기간이 겹쳐도 통과합니다. 2025-01-01 시작 행을 닫지 않고 2026-05-01 시작 행을 넣으면 5월 이후 날짜에 단가가 두 개가 됩니다. Oracle에는 기간 겹침을 막는 선언적 제약이 없으므로 세 겹으로 막습니다. 변경은 "현재 행 닫기 + 새 행 넣기"를 한 트랜잭션으로 하는 정해진 절차(또는 프로시저)로만 하고, CHECK (시작일 <= 종료일)을 걸고, LEAD로 다음 시작일이 종료일 + 1인지 보는 점검 쿼리와 현재 행 1개 점검 쿼리를 품질 규칙으로 매일 돌립니다. 겹침이 생기면 거래와 조인할 때 행이 늘어나므로, 조인 결과 행 수가 원천 행 수와 같은지 보는 것도 좋은 간접 점검입니다.
:::

**Q3. 정 과장이 "단가 이력은 있는데, 지난달 누가 단가를 잘못 넣었다가 고쳤는지도 알고 싶다"고 합니다. 선분이력만으로 답할 수 있습니까?**

:::answer 모범 답안 보기
답할 수 없습니다. 선분이력은 업무 유효 시간, 즉 "이 단가가 언제부터 언제까지 적용되는가"의 현재 상태만 담습니다. 잘못 넣었다가 고친 행은 정정 후 사라지거나 덮어써집니다. "누가 언제 무엇을 바꿨는가"는 기록 시간의 질문이므로 변경로그가 필요합니다. 변경 전후 값, 변경 일시, 변경자를 남기는 변경로그 테이블을 선분이력에 붙이고(트리거 또는 변경 절차 안에서 기록), 감사 조회는 변경로그로 답합니다. 소급 정정이 잦아 "그 시점에 우리가 알던 단가"로 과거 보고서를 재현해야 한다면 이원 시간 설계까지 검토합니다.
:::

## 오늘의 과제

**과제 1.** 정 과장이 "2026년 3~4월 동안 한빛펜정 기준가가 각각 며칠씩 적용됐는지" 묻습니다. 선분이력을 조회 기간(2026-03-01 ~ 2026-04-30)으로 잘라서 보여 주세요. 결과 모양은 `item_cd, clip_strt_dt, clip_end_dt, day_cnt, uprc` 2행이며, 일수 합이 61일이어야 합니다.

:::answer 해설 보기
두 기간이 겹치는 조건은 "선분 시작 <= 조회 끝 AND 선분 끝 >= 조회 시작"입니다. 겹친 부분은 시작일의 큰 값, 종료일의 작은 값으로 자릅니다. 종료일 포함 규칙이므로 일수는 "끝 - 시작 + 1"입니다. 이 +1을 빼먹는 것이 포함·미포함 규칙을 섞을 때 가장 흔한 실수입니다.

```sql
SELECT h.item_cd,
       GREATEST(h.aply_strt_dt, DATE '2026-03-01') AS clip_strt_dt,
       LEAST(h.aply_end_dt, DATE '2026-04-30')     AS clip_end_dt,
       LEAST(h.aply_end_dt, DATE '2026-04-30') - GREATEST(h.aply_strt_dt, DATE '2026-03-01') + 1 AS day_cnt,
       h.uprc
  FROM erp.tb_item_uprc_hist h
 WHERE h.item_cd = 'P10001' AND h.uprc_tp_cd = '01'
   AND h.aply_strt_dt <= DATE '2026-04-30'
   AND h.aply_end_dt  >= DATE '2026-03-01'
 ORDER BY clip_strt_dt;
```

결과는 3월 1일 ~ 3월 31일 31일 3,200원, 4월 1일 ~ 4월 30일 30일 3,000원입니다.
:::

:::note Oracle 차이
Oracle에서 DATE끼리 빼면 일수가 NUMBER로 나옵니다(PostgreSQL은 integer). 시각이 섞인 DATE라면 소수가 나오므로 `TRUNC`로 시각을 지운 뒤 계산합니다.
:::

**과제 2.** 선분이력을 일별 스냅샷으로 펼쳐 보세요. 한빛펜정 기준가를 2026-03-29부터 2026-04-02까지 하루 한 행으로 보여 주는 쿼리를 작성합니다. 결과 모양은 `base_dt, uprc` 5행입니다. DW에서 일 단위 가격 차원이나 팩트를 만들 때 쓰는 변환입니다.

:::answer 해설 보기
날짜 목록을 만들고 각 날짜에 유효한 선분을 BETWEEN으로 붙입니다. 선분이력 → 스냅샷 변환은 이 한 가지 패턴이면 됩니다.

```sql
SELECT d.base_dt::date AS base_dt, h.uprc
  FROM generate_series(DATE '2026-03-29', DATE '2026-04-02', INTERVAL '1 day') AS d (base_dt)
  JOIN erp.tb_item_uprc_hist h
    ON h.item_cd = 'P10001' AND h.uprc_tp_cd = '01'
   AND d.base_dt::date BETWEEN h.aply_strt_dt AND h.aply_end_dt
 ORDER BY d.base_dt;
```

결과는 3월 29일 ~ 31일 3,200원, 4월 1일 ~ 2일 3,000원입니다. 펼친 결과는 저장량이 늘어나므로, 매번 펼칠지 날짜 차원과 조인해 필요할 때만 펼칠지는 조회 빈도로 정합니다.
:::

:::note Oracle 차이
Oracle에는 `generate_series`가 없습니다. `SELECT DATE '2026-03-29' + LEVEL - 1 AS base_dt FROM DUAL CONNECT BY LEVEL <= 5`처럼 만들거나, DW의 날짜 차원 테이블을 씁니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 데이터 표준 정의서 | 선분이력 경계 규칙(종료일 포함, 9999-12-31, 다음 시작 = 종료 + 1, 일시 이력은 반열림)을 전사 규칙으로 한 번 적습니다. |
| 엔터티정의서 | 엔터티별 이력 형태(선분·시점·스냅샷·변경로그)와 선택 이유, 이력 키. |
| 테이블정의서 | PK (키 + 적용시작일자), CHECK (시작 <= 종료), 기본값 9999-12-31, 변경로그 테이블과 트리거 여부. |
| 프로그램 사양서 | 단가 변경 절차(닫기 + 넣기 한 트랜잭션, 미래 일자 등록 허용 여부, 소급 정정 승인 절차). |
| 데이터 품질 규칙 목록 | 겹침·빈틈 점검, 현재 행 1개 점검, 거래 조인 행 수 점검 쿼리와 실행 주기. |
| 매핑정의서 (DW) | 운영계 이력을 DW SCD Type 2 차원이나 일별 스냅샷으로 옮기는 규칙, 원천이 NULL 종료일을 쓸 때의 변환. |

## 참고할 원전

- Richard T. Snodgrass, "Developing Time-Oriented Database Applications in SQL" (Morgan Kaufmann, 1999) — 유효 시간·기록 시간, 기간 겹침 검사, 이원 시간 설계.
- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 4 "Inventory"(주기 스냅샷), Chapter 5 "Procurement"(천천히 변하는 차원 기법).
- Graeme Simsion, Graham Witt, "Data Modeling Essentials", 3rd ed. (Morgan Kaufmann, 2005) — 시간에 따라 변하는 데이터를 다루는 장.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 모델링 영역: 이력 관리 유형.
