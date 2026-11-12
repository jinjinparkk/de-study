# Day 12. 데이터 품질

## 오늘의 한 줄

데이터 품질은 "깨끗하다"는 느낌이 아니라 **규칙으로 정의하고, 쿼리로 재고, 결과를 기록하는 것**입니다. 그리고 제약 데이터에서는 값이 맞는 것만으로 부족합니다. 누가·언제·왜 그 값을 남기고 고쳤는지까지 증명할 수 있어야 합니다(ALCOA+, 감사 추적).

## 왜 중요한가

정 과장이 "대시보드 3월 매출이 ERP보다 적다"고 합니다. 대사를 설계하지 않았다면 어느 단계에서 빠졌는지 찾느라 하루를 씁니다. 한빛케미칼에서는 더 무거운 일이 생길 수 있습니다. 생산실적 양품수량이 2,000에서 1,990으로 고쳐져 있는데 누가, 왜 고쳤는지 기록이 없다면, 값이 맞더라도 GMP 관점에서는 **신뢰할 수 없는 데이터**가 됩니다.

## 핵심 개념

### 1. 품질 차원: 무엇을 잴 것인가

| 차원 | 질문 | 한빛제약그룹 규칙 예 |
|---|---|---|
| 완전성 | 있어야 할 값이 있는가 | 거래처 사업자등록번호 누락 건수 |
| 유효성 | 형식·허용값 안에 있는가 | 사업자등록번호 형식, 주문상태코드 허용값 (Day 9) |
| 정합성 | 서로 관련된 값이 맞는가 | 주문금액 = 수량 × 단가, 출고 ≤ 주문, 차변 = 대변 |
| 유일성 | 중복이 없는가 | 같은 사업자등록번호 거래처 (Day 4, Day 13) |
| 적시성 | 필요한 때에 와 있는가 | 일별재고 최신 일자가 기준일 전날인가 |

정확성(현실과 일치하는가)은 창고 실사처럼 바깥 기준이 있어야 잴 수 있습니다. 쿼리로 잴 수 있는 것과 없는 것을 구별하는 것이 품질 계획의 출발입니다.

### 2. 품질 규칙은 "데이터"로 관리합니다

규칙 ID, 차원, 점검 SQL, 오너를 **규칙 테이블**에 넣고 실행 결과를 **결과 테이블**에 쌓습니다. 배치 코드에 흩어 두면 몇 개가 있는지, 언제 실패했는지 아무도 모릅니다. Day 8에서 DB에 걸지 못한 FK·CHECK도 이 틀로 옮깁니다.

규칙마다 **위반 시 조치**도 정합니다. 적재를 멈출 것인가(차대 불일치), 적재하고 경고할 것인가(사업자번호 형식), 오류 테이블로 분리할 것인가(Day 23).

### 3. 대사(Reconciliation): 원천과 적재가 같은가

대사는 원천과 DW의 건수·금액을 비교해 옮기다 잃거나 바뀐 것이 없음을 증명하는 일입니다. **전체 합계**(건수, 금액 합) → **차원별 합계**(월별, 회사별) → **행 단위 비교**(키로 FULL OUTER JOIN). 위 단계에서 맞으면 멈추고, 틀리면 한 단계 내려가 범위를 좁힙니다.

### 4. ALCOA+: 제약 데이터 무결성 원칙

ALCOA+는 GMP 규제를 받는 제약 제조·품질 영역의 **데이터 무결성 원칙**으로, 값이 맞는지보다 **기록을 믿을 수 있는지**를 묻습니다.

| 원칙 | 뜻 | 데이터 설계로 옮기면 |
|---|---|---|
| Attributable (귀속성) | 누가 기록·변경했는지 알 수 있다 | 공용 계정 금지, 실제 사용자 ID 기록 |
| Legible (판독성) | 읽을 수 있고 이해할 수 있다 | 코드 정의·단위 보존 (Day 9, 10) |
| Contemporaneous (동시성) | 일이 일어난 때에 기록한다 | 업무 일시와 기록 일시를 따로 저장 |
| Original (원본성) | 최초 기록 또는 그 진본 사본이다 | 덮어쓰기 금지, 원본값 보존 |
| Accurate (정확성) | 오류 없이 사실과 맞다 | 품질 규칙, 정정 시 사유·승인 |
| Complete (완전성) | 정정·재시험을 포함해 빠짐없다 | 변경 이력 전부 보존 |
| Consistent (일관성) | 순서와 시각이 앞뒤가 맞다 | 시각 기록, 순서 점검 |
| Enduring (지속성) | 보관 기간 동안 남는다 | 삭제 대신 보관, 백업 |
| Available (가용성) | 필요할 때 찾아 볼 수 있다 | 조회 가능한 구조와 색인 |

설계 요구는 하나로 모입니다. **고칠 수는 있지만 지울 수는 없게, 고친 사실과 이유는 반드시 남게.** 그 장치가 감사 추적입니다. 그룹 DW가 GMP 대상 시스템인지(DW 데이터를 품질 판단에 쓰는지)는 품질보증(QA) 부서와 함께 정하며, 대상이면 시스템 밸리데이션 범위에도 들어갑니다.

### 5. 감사 추적(Audit trail) 설계

감사 추적은 변경을 **누가, 언제, 무엇을 무엇에서 무엇으로, 왜** 남기는 별도 기록입니다. Day 7의 변경로그보다 요구가 강합니다.

- **왜(사유) 필수**: 사유 없는 변경은 거부합니다.
- **사람 기준 귀속**: DB 접속 계정은 대개 공용 계정이므로 애플리케이션이 실제 사용자 ID를 넘깁니다.
- **변경 불가(immutability)**: 감사 기록 자체의 UPDATE·DELETE를 권한(REVOKE)과 트리거로 막습니다.
- **시각은 서버가**: 사용자 입력 시각이 아니라 DB 서버 시각.

DW는 여기서 한 가지를 더 지켜야 합니다. 원천이 정정되면 DW는 **덮어쓰지 않고 새 버전으로 쌓아** 정정 전 값과 정정 시점을 보존합니다. DW가 UPDATE로 최신값만 남기면, 원천에는 남아 있는 감사 추적이 DW에서 끊깁니다.

## 예시

### 품질 규칙 테이블과 실행기

```sql
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE lab.tb_dq_rule (                  -- 품질 규칙
  rule_id    VARCHAR(10)  PRIMARY KEY,
  dq_dim_nm  VARCHAR(10)  NOT NULL,            -- 완전성·유효성·정합성·유일성·적시성
  rule_desc  VARCHAR(200) NOT NULL,
  chk_sql    TEXT         NOT NULL             -- 위반 건수 1개를 돌려주는 SQL
);
CREATE TABLE lab.tb_dq_rslt (                  -- 품질 점검 결과 (쌓기만 함)
  rule_id  VARCHAR(10) NOT NULL REFERENCES lab.tb_dq_rule (rule_id),
  chk_dtm  TIMESTAMP   NOT NULL DEFAULT clock_timestamp(),
  err_cnt  NUMERIC(12) NOT NULL
);

INSERT INTO lab.tb_dq_rule VALUES
('DQ01','완전성','거래처 사업자등록번호 누락',
 $q$SELECT COUNT(*) FROM erp.tb_cust WHERE biz_reg_no IS NULL$q$),
('DQ02','유효성','사업자등록번호 형식(000-00-00000) 위반',
 $q$SELECT COUNT(*) FROM erp.tb_cust WHERE biz_reg_no !~ '^[0-9]{3}-[0-9]{2}-[0-9]{5}$'$q$),
('DQ03','유일성','사업자등록번호 중복 거래처',
 $q$SELECT COUNT(*) FROM (SELECT biz_reg_no FROM erp.tb_cust WHERE biz_reg_no IS NOT NULL
                          GROUP BY biz_reg_no HAVING COUNT(*) > 1) x$q$),
('DQ04','정합성','주문금액 <> 수량 × 단가',
 $q$SELECT COUNT(*) FROM erp.tb_ord_dtl WHERE ord_amt <> ord_qty * uprc$q$),
('DQ05','정합성','유효기한이 지난 로트 출고',
 $q$SELECT COUNT(*) FROM erp.tb_ship s JOIN erp.tb_ship_dtl d ON d.ship_no = s.ship_no
      JOIN erp.tb_lot l ON l.lot_no = d.lot_no WHERE s.ship_dt > l.exp_dt$q$),
('DQ06','적시성','일별재고 최신 일자가 기준일(2026-04-01) 전날보다 이전',
 $q$SELECT CASE WHEN MAX(inv_dt) < DATE '2026-04-01' - 1 THEN 1 ELSE 0 END FROM erp.tb_inv_daily$q$);

CREATE FUNCTION lab.fn_run_dq() RETURNS void LANGUAGE plpgsql AS $$
DECLARE r RECORD; v_cnt NUMERIC;
BEGIN
  FOR r IN SELECT rule_id, chk_sql FROM lab.tb_dq_rule ORDER BY rule_id LOOP
    EXECUTE r.chk_sql INTO v_cnt;
    INSERT INTO lab.tb_dq_rslt (rule_id, err_cnt) VALUES (r.rule_id, v_cnt);
  END LOOP;
END $$;

SELECT lab.fn_run_dq();
SELECT r.rule_id, r.dq_dim_nm, r.rule_desc, s.err_cnt
  FROM lab.tb_dq_rule r JOIN lab.tb_dq_rslt s ON s.rule_id = r.rule_id
 ORDER BY r.rule_id;
```

공통 샘플은 6개 규칙 모두 0건입니다. 실무에서는 출고 ≤ 주문, 차변 = 대변 등으로 늘어납니다. 규칙이 잡는지 보려면 나쁜 데이터를 넣어 봐야 하므로, 트랜잭션 안에서 넣고 되돌립니다.

```sql
BEGIN;
INSERT INTO erp.tb_cust (cust_no, cust_nm, cust_tp_cd, biz_reg_no, rgn_cd) VALUES
 ('C000302', '바른팜유통 경기지점', '03', '135-86-00005', 'GGD'),   -- 같은 사업자번호
 ('C000203', '새봄약국', '02', '2011200099', 'SEL');                -- 하이픈 없음
UPDATE erp.tb_ord_dtl SET ord_amt = 5000 WHERE ord_no = 'SO2026030001' AND ord_seq = 2;  -- 금액 오타
TRUNCATE lab.tb_dq_rslt;
SELECT lab.fn_run_dq();
SELECT r.rule_id, r.rule_desc, s.err_cnt
  FROM lab.tb_dq_rule r JOIN lab.tb_dq_rslt s ON s.rule_id = r.rule_id
 WHERE s.err_cnt > 0 ORDER BY r.rule_id;
ROLLBACK;
```

DQ02(형식), DQ03(중복), DQ04(금액)가 각 1건씩 잡힙니다. 그런데 DQ03은 **정말 오류일까요?** Day 4에서 본 것처럼 한 사업자 아래 지점을 별도 거래처로 관리할 수 있습니다. 규칙을 만들 때 "중복이면 무조건 오류"인지 "확인 대상"인지 오너와 정해야 합니다. 하이픈 없는 번호는 Day 13 MDM 매칭에서 정규화가 필요한 이유입니다.

### 원천 대비 적재 대사

스테이징(가정)에 주문상세를 옮기다 한 행이 빠지고, 한 행은 금액이 잘못 변환됐다고 합시다.

```sql
CREATE TABLE lab.stg_ord_dtl AS                -- 적재된 결과 (사고 포함)
SELECT o.ord_dt, d.ord_no, d.ord_seq, d.item_cd, d.ord_qty, d.uprc, d.ord_amt
  FROM erp.tb_ord o JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
 WHERE NOT (d.ord_no = 'SO2026030003' AND d.ord_seq = 2);       -- 누락
UPDATE lab.stg_ord_dtl SET ord_amt = 5000
 WHERE ord_no = 'SO2026030001' AND ord_seq = 2;                 -- 변환 오류 (50,000 → 5,000)

-- 1단계: 전체 합계
SELECT 'SRC' AS side, COUNT(*) AS row_cnt, SUM(ord_amt) AS amt FROM erp.tb_ord_dtl
UNION ALL
SELECT 'TGT', COUNT(*), SUM(ord_amt) FROM lab.stg_ord_dtl;

-- 2단계: 월별
SELECT COALESCE(s.ym, t.ym) AS ym, s.cnt AS src_cnt, t.cnt AS tgt_cnt,
       s.amt AS src_amt, t.amt AS tgt_amt, COALESCE(s.amt, 0) - COALESCE(t.amt, 0) AS diff_amt
  FROM (SELECT to_char(o.ord_dt, 'YYYY-MM') AS ym, COUNT(*) AS cnt, SUM(d.ord_amt) AS amt
          FROM erp.tb_ord o JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no GROUP BY 1) s
  FULL JOIN (SELECT to_char(ord_dt, 'YYYY-MM') AS ym, COUNT(*) AS cnt, SUM(ord_amt) AS amt
               FROM lab.stg_ord_dtl GROUP BY 1) t ON t.ym = s.ym
 ORDER BY ym;

-- 3단계: 행 단위 (차이 나는 행만)
SELECT COALESCE(s.ord_no, t.ord_no) AS ord_no, COALESCE(s.ord_seq, t.ord_seq) AS ord_seq,
       s.ord_amt AS src_amt, t.ord_amt AS tgt_amt,
       CASE WHEN t.ord_no IS NULL THEN '적재 누락'
            WHEN s.ord_no IS NULL THEN '원천에 없음'
            ELSE '값 불일치' END AS diff_tp
  FROM erp.tb_ord_dtl s
  FULL JOIN lab.stg_ord_dtl t ON t.ord_no = s.ord_no AND t.ord_seq = s.ord_seq
 WHERE t.ord_no IS NULL OR s.ord_no IS NULL OR s.ord_amt IS DISTINCT FROM t.ord_amt
 ORDER BY 1, 2;
```

| 단계 | 결과 | 다음 행동 |
|---|---|---|
| 1. 전체 | 원천 8건 2,436,000원, 적재 7건 1,191,000원 | 건수·금액 모두 틀림 → 2단계 |
| 2. 월별 | 3월만 차이(6건 vs 5건, 1,245,000원), 4월은 일치 | 3월로 범위 축소 → 3단계 |
| 3. 행 단위 | SO2026030001-2 값 불일치(50,000 vs 5,000), SO2026030003-2 적재 누락 | 원인 조사·재적재 |

건수만 보면 금액 오류를, 금액 합만 보면 서로 상쇄되는 오류를 놓치므로 **건수·금액·수량을 함께** 봅니다.

### 감사 추적: 생산실적 정정

한빛케미칼 생산실적(WO2026010001, 로트 L260105)의 양품 2,000, 불량 12를 QA 검사 결과에 따라 양품 1,990, 불량 22로 정정해야 합니다. 운영계를 바꾸지 않도록 `lab`에 복사본을 만들고 감사 추적을 붙입니다.

```sql
CREATE TABLE lab.tb_prod_rslt (LIKE erp.tb_prod_rslt INCLUDING ALL);
INSERT INTO lab.tb_prod_rslt SELECT * FROM erp.tb_prod_rslt;

CREATE TABLE lab.tb_audit_trail (               -- 감사 추적
  audit_seq  BIGINT       GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  tbl_nm     VARCHAR(60)  NOT NULL,
  pk_val     VARCHAR(100) NOT NULL,             -- 대상 행의 키 (예: WO2026010001|L260105)
  chg_tp_cd  CHAR(1)      NOT NULL,             -- U 수정, D 삭제 (삭제 감사는 같은 방식)
  col_nm     VARCHAR(60)  NOT NULL,
  bf_val     VARCHAR(200),
  af_val     VARCHAR(200),
  chg_rsn    VARCHAR(300) NOT NULL,             -- 왜
  chg_id     VARCHAR(30)  NOT NULL,             -- 누가 (실제 사용자)
  chg_dtm    TIMESTAMP    NOT NULL DEFAULT clock_timestamp()   -- 언제 (서버 시각)
);

CREATE FUNCTION lab.fn_prod_rslt_audit() RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
  v_rsn  TEXT := NULLIF(current_setting('app.chg_rsn', true), '');
  v_user TEXT := COALESCE(NULLIF(current_setting('app.user_id', true), ''), current_user);
  v_pk   TEXT := OLD.wo_no || '|' || OLD.lot_no;
BEGIN
  IF v_rsn IS NULL THEN
    RAISE EXCEPTION '생산실적 변경에는 변경 사유(app.chg_rsn)가 필요합니다';
  END IF;
  IF NEW.good_qty IS DISTINCT FROM OLD.good_qty THEN
    INSERT INTO lab.tb_audit_trail (tbl_nm, pk_val, chg_tp_cd, col_nm, bf_val, af_val, chg_rsn, chg_id)
    VALUES ('TB_PROD_RSLT', v_pk, 'U', 'GOOD_QTY', OLD.good_qty, NEW.good_qty, v_rsn, v_user);
  END IF;
  IF NEW.defect_qty IS DISTINCT FROM OLD.defect_qty THEN
    INSERT INTO lab.tb_audit_trail (tbl_nm, pk_val, chg_tp_cd, col_nm, bf_val, af_val, chg_rsn, chg_id)
    VALUES ('TB_PROD_RSLT', v_pk, 'U', 'DEFECT_QTY', OLD.defect_qty, NEW.defect_qty, v_rsn, v_user);
  END IF;
  RETURN NEW;
END $$;
CREATE TRIGGER trg_prod_rslt_audit BEFORE UPDATE ON lab.tb_prod_rslt
FOR EACH ROW EXECUTE FUNCTION lab.fn_prod_rslt_audit();

-- 감사 기록은 고칠 수도 지울 수도 없게
CREATE FUNCTION lab.fn_audit_immutable() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  RAISE EXCEPTION '감사 추적은 수정·삭제할 수 없습니다';
END $$;
CREATE TRIGGER trg_audit_immutable BEFORE UPDATE OR DELETE ON lab.tb_audit_trail
FOR EACH ROW EXECUTE FUNCTION lab.fn_audit_immutable();
```

사유 없이 고치려 하면 거부됩니다.

```sql 의도된 오류 — 변경 사유 없음
UPDATE lab.tb_prod_rslt SET good_qty = 1990, defect_qty = 22
 WHERE wo_no = 'WO2026010001' AND lot_no = 'L260105';
```

애플리케이션은 실제 사용자와 사유를 **그 트랜잭션에만** 유효하게 넘깁니다(`set_config`의 세 번째 인자 true). 세션 전체에 걸면 다음 변경이 앞 사유를 물려받습니다.

```sql
BEGIN;
SELECT set_config('app.user_id', 'QA_E4101', true),
       set_config('app.chg_rsn', '출하 전 검사에서 불량 10 추가 확인. 승인번호 QA-2026-011 (가상)', true);
UPDATE lab.tb_prod_rslt SET good_qty = 1990, defect_qty = 22
 WHERE wo_no = 'WO2026010001' AND lot_no = 'L260105';
COMMIT;

SELECT audit_seq, pk_val, chg_tp_cd, col_nm, bf_val, af_val, chg_id, chg_rsn
  FROM lab.tb_audit_trail ORDER BY audit_seq;
```

양품 2000 → 1990, 불량 12 → 22가 같은 사용자·사유로 두 행 남습니다. 거부된 첫 시도는 남지 않으므로, 실패한 시도까지 남기려면 DB 감사 기능이 따로 필요합니다.

```sql 의도된 오류 — 감사 추적은 변경 불가
UPDATE lab.tb_audit_trail SET chg_rsn = '단순 오타 수정' WHERE audit_seq = 1;
```

:::note Oracle 차이
Oracle에서는 사용자·사유를 `DBMS_SESSION.SET_CONTEXT`로 애플리케이션 컨텍스트에 넣고 트리거에서 `SYS_CONTEXT`로 읽는 방식이 흔하며, 오류는 `RAISE_APPLICATION_ERROR`로 냅니다. 트리거는 DBA 권한의 우회를 막지 못하므로 DB 감사 기능과 권한 분리를 함께 설계합니다.
:::

### DW는 덮어쓰지 않고 쌓는다

원천이 정정되면 DW 이력 테이블에는 새 버전이 추가됩니다.

```sql
CREATE TABLE lab.ods_prod_rslt_hist (           -- 생산실적 이력 (추가만 함)
  wo_no       VARCHAR(14) NOT NULL,
  lot_no      VARCHAR(20) NOT NULL,
  ver_no      NUMERIC(4)  NOT NULL,
  good_qty    NUMERIC(10) NOT NULL,
  defect_qty  NUMERIC(10) NOT NULL,
  load_dtm    TIMESTAMP   NOT NULL,
  batch_id    VARCHAR(30) NOT NULL,
  PRIMARY KEY (wo_no, lot_no, ver_no)
);
INSERT INTO lab.ods_prod_rslt_hist VALUES
 ('WO2026010001', 'L260105', 1, 2000, 12, TIMESTAMP '2026-01-06 06:00', 'B20260106'),
 ('WO2026010001', 'L260105', 2, 1990, 22, TIMESTAMP '2026-01-09 06:00', 'B20260109');

-- 현재값 (분석용)과 1월 7일 기준 값 (그때 보고서 재현용)
SELECT 'current' AS view_tp, wo_no, lot_no, ver_no, good_qty, defect_qty
  FROM (SELECT h.*, ROW_NUMBER() OVER (PARTITION BY wo_no, lot_no ORDER BY ver_no DESC) AS rn
          FROM lab.ods_prod_rslt_hist h) x
 WHERE rn = 1
UNION ALL
SELECT 'as_of_0107', wo_no, lot_no, ver_no, good_qty, defect_qty
  FROM (SELECT h.*, ROW_NUMBER() OVER (PARTITION BY wo_no, lot_no ORDER BY ver_no DESC) AS rn
          FROM lab.ods_prod_rslt_hist h
         WHERE load_dtm < TIMESTAMP '2026-01-08') x
 WHERE rn = 1;
```

현재값은 1,990, 1월 7일 기준으로는 2,000입니다.1월 7일 보고서가 왜 2,000이었는지 DW가 스스로 설명합니다. Day 7의 기록 시간, Day 19의 SCD Type 2, Day 22의 CDC가 모두 이 생각 위에 있습니다.

## Before / After

| 항목 | Before | After |
|---|---|---|
| 품질 규칙 | 담당자 PC의 SQL 파일 몇 개 | 규칙 테이블(차원·SQL·조치·오너) + 결과 테이블, 매일 실행 |
| 대사 | 오픈 때 한 번, 건수만 | 단계마다 건수·금액·수량, 전체 → 차원별 → 행 단위 |
| 생산실적 정정 | UPDATE로 덮어씀. 공용 계정, 사유 없음 | 사유·실제 사용자 필수, 컬럼별 전후 값, 감사 기록 변경 불가 |
| DW | 매일 원천 최신값으로 UPDATE | 정정은 새 버전으로 추가, 현재값과 시점 값 모두 조회 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 위반 시 조치 | 금액·차대처럼 틀리면 보고서 전체가 틀리는 규칙은 적재 중단 | 형식·누락처럼 일부 행 문제는 적재 + 경고 + 오류 목록 |
| 감사 추적 범위 | GMP 영향 데이터(생산·품질·로트)는 컬럼 단위·사유 필수 | 일반 마스터는 Day 7 변경로그로 충분 |
| DW 적재 방식 | 원천 정정이 의미를 갖는 데이터(실적·단가)는 버전 추가 | 정정 이력이 의미 없는 참조 데이터는 덮어쓰기(Type 1) |

## 흔한 실수 3가지

1. **품질 규칙을 만들고 결과를 남기지 않는 실수.** 결과를 쌓아야 "지난달부터 늘고 있다"는 추세가 보입니다.
2. **변경 이력을 공용 계정으로 남기는 실수.** chg_id가 모두 'ERP_APP'이면 Attributable이 성립하지 않습니다. 실제 사용자 ID 전달을 설계 요구사항으로 명시합니다.
3. **DW에서 정정을 덮어쓰는 실수.** 원천의 감사 추적이 DW에서 끊깁니다. 실적·품질 데이터는 버전을 쌓습니다.

## 셀프 체크 질문

**Q1. 대사(Reconciliation)를 어떻게 설계하시겠습니까?**

:::answer 모범 답안 보기
원천 → 스테이징 → DW → 마트의 각 경계에서 건수·금액 합·수량 합을 함께 비교합니다(하나만 보면 상쇄 오류를 놓침). 비교는 전체 합계 → 차원별(일자·회사) → 행 단위(키 FULL OUTER JOIN) 순서로 내려가며, 위에서 맞으면 멈춥니다.
:::

**Q2. ALCOA+를 데이터 설계 요구사항으로 바꿔 말해 보세요.**

:::answer 모범 답안 보기
Attributable은 공용 계정이 아닌 실제 사용자 ID, Contemporaneous는 업무 일시와 별도로 서버 시각의 기록 일시, Original·Complete는 덮어쓰기 금지와 정정 전후 값 보존, Accurate는 품질 규칙과 정정 사유·승인, Enduring·Available은 보관 기간 동안 삭제 없이 조회 가능한 구조입니다. 묶으면 "고칠 수는 있지만 지울 수는 없고, 누가 언제 왜 고쳤는지 남는다"이며, 그 구현이 사유 필수·변경 불가 감사 추적과 DW의 버전 적재입니다. 대상 범위와 밸리데이션 필요 여부는 QA와 함께 정합니다.
:::

**Q3. 품질 규칙 위반이 나올 때마다 DW 적재를 멈추자는 의견이 있습니다.**

:::answer 모범 답안 보기
규칙마다 등급을 나눕니다. 차대 불일치·대사 금액 차이처럼 보고서 전체가 틀리는 규칙은 적재 중단(또는 마트 공개 보류), 형식 오류처럼 일부 행 문제는 적재 + 경고 + 오류 목록, 예외가 있을 수 있는 규칙(사업자번호 중복)은 "확인 대상"입니다. 모두 멈추면 DW가 매일 멈추고, 등급과 조치는 규칙 테이블에 적어 오너가 승인합니다.
:::

## 오늘의 과제

**과제 1.** 위 감사 추적에서 "L260105 로트의 양품수량이 지금 값이 되기까지의 이력"을 시간순으로 보여 주세요. 결과 모양은 `chg_dtm, bf_val, af_val, chg_id, chg_rsn` 1행입니다. 감사 대응 화면의 기본 질의입니다.

:::answer 해설 보기
```sql
SELECT chg_dtm, bf_val, af_val, chg_id, chg_rsn
  FROM lab.tb_audit_trail
 WHERE tbl_nm = 'TB_PROD_RSLT' AND pk_val = 'WO2026010001|L260105' AND col_nm = 'GOOD_QTY'
 ORDER BY chg_dtm, audit_seq;
```

2000 → 1990, QA_E4101, 승인번호가 들어간 사유 1행입니다. PK_VAL을 문자열로 이어 붙이는 방식은 키 조립 규칙을 표준으로 정해 두어야 검색이 깨지지 않습니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 데이터 품질 규칙 정의서 | 규칙 ID, 차원, 대상, 점검 SQL, 등급(오류·확인 대상), 위반 시 조치, 오너, 실행 주기. |
| 대사 정의서 | 대사 구간(원천 → 스테이징 → DW → 마트), 비교 항목(건수·금액·수량), 허용 오차, 차이 시 조치. |
| 감사 추적 설계서 | 대상 테이블·컬럼, 기록 항목(누가·언제·무엇·왜), 변경 불가 장치, 보관 기간, 조회 화면. |

## 참고할 원전

- MHRA, "'GXP' Data Integrity Guidance and Definitions" — ALCOA+와 감사 추적의 정의.
- U.S. FDA, "Data Integrity and Compliance With Drug CGMP: Questions and Answers" (Guidance for Industry).
- PIC/S, "Good Practices for Data Management and Integrity in Regulated GMP/GDP Environments".
- DAMA International, "DAMA-DMBOK: Data Management Body of Knowledge", 2nd ed. (Technics Publications, 2017) — Data Quality 장.
