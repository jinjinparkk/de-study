# Day 23. 적재 설계 디테일

## 오늘의 한 줄

팩트 적재의 품질은 정상 데이터가 아니라 **"안 맞는 데이터를 어떻게 다루는가"** 에서 갈립니다. 차원을 못 찾으면 버리지 말고 -1로 넣어 금액을 지키고, 측정값이 틀리면 오류 테이블로 보내고, 어느 쪽이든 나중에 다시 처리할 수 있게 원천 키를 남기는 것. 이 규칙을 컬럼 단위로 적은 문서가 매핑정의서입니다.

## 왜 중요한가

신규 거래처 다온약국의 첫 주문이 들어왔는데 거래처 마스터가 하루 늦게 왔습니다. 적재 SQL이 INNER JOIN이면 그 주문은 조용히 사라지고, 정 과장의 4월 매출은 ERP 화면보다 90,000원 적게 나옵니다. 원인을 찾느라 이틀을 쓰고, 찾은 뒤에는 "어느 날 어떤 건이 빠졌는지"를 알 방법이 없어 전체를 다시 적재합니다. **조인 실패 규칙, 오류 기록, 재처리 경로**를 미리 정하지 않아 생기는 일입니다.

## 핵심 개념

### 1. 서로게이트 키 매핑: 업무 키 → SK, 사건 일자 기준

팩트 적재의 첫 단계는 원천의 업무 키(CUST_NO, ITEM_CD …)를 차원의 SK로 바꾸는 조회(lookup)입니다. Type 1 차원은 업무 키 하나로 찾고, Type 2 차원(DIM_CUST)은 **업무 키 + 사건 일자 BETWEEN 유효기간**으로 찾습니다(Day 19). 조회는 반드시 LEFT JOIN이어야 합니다. INNER JOIN은 실패한 행을 오류 없이 지워 버립니다.

### 2. 조인 실패 시 -1: 행은 지키고 사실은 기록한다

차원을 못 찾았다고 행을 버리면 원천과 DW의 합계가 어긋납니다. 그래서 팩트 FK에 알 수 없음(-1)을 넣고 **행과 금액은 살립니다**. 대신 "왜 -1인가"를 오류 테이블에 경고로 남겨야 나중에 고칠 수 있습니다. 마스터가 곧 올 것이 확실하고 그 업무 키를 차원에 먼저 만들어도 된다면 추정 멤버(Day 20)가 더 낫습니다. -1은 "모름", 추정 멤버는 "아직 이름은 모르지만 누군지는 앎"입니다.

### 3. 경고와 거부: 오류의 두 등급

| 등급 | 예 | 처리 | 이유 |
|---|---|---|---|
| 경고 (W) | 거래처·품목 조회 실패, 날짜가 날짜 차원 범위 밖 | -1로 적재 + 오류 로그 | 금액은 맞으므로 합계를 지킴 |
| 거부 (E) | 수량 음수, 금액 ≠ 수량 × 단가, 필수값 NULL | 팩트 미적재 + 오류 로그 | 틀린 숫자가 대시보드에 나가면 안 됨 |

경고와 거부의 구분은 **현업 합의**입니다. 반품을 음수 수량으로 표현하는 회사라면 "수량 음수"는 거부가 아닙니다. 규칙 목록은 매핑정의서와 품질 규칙 목록(Day 12)에 같이 둡니다.

### 4. 감사 컬럼: 이 행은 언제, 어느 배치가 만들었나

공통 DW의 모든 테이블에는 LOAD_DTM(적재일시)과 BATCH_ID(배치ID)가 있어 "4월 5일 배치가 바꾼 행만 되돌리기"가 가능합니다. 여러 계열사 원천을 받기 시작하면 원천시스템코드(SRC_SYS_CD)를, 최초 적재와 최종 변경을 구분해야 하면 최초적재배치ID와 최종변경배치ID를 따로 둡니다. 감사 컬럼은 **값이 실제로 바뀔 때만** 갱신해야 의미가 있습니다(Day 22 멱등성).

### 5. 재처리 전략: 오류를 "처리 상태"가 있는 작업 목록으로

오류 테이블은 로그가 아니라 할 일 목록입니다. 원천 키, 오류 컬럼, 오류 값, 규칙 코드, 처리상태(N 미처리 / Y 처리완료)를 두면 두 가지 재처리가 가능합니다. 경고 건은 마스터가 도착한 뒤 -1을 올바른 SK로 **갱신**합니다. 거부 건은 원천이 수정된 뒤 그 키를 다음 배치 추출에 **강제로 포함**합니다. 어느 쪽이든 전체 재적재 없이 해당 건만 고칩니다.

## 예시

### 4월 5일 배치: 정상 2건, 경고 2건, 거부 2건

ERP의 4월 주문 2건에 가상의 문제 데이터 4건을 섞은 스테이징입니다. 다온약국(C000204)은 아직 거래처 차원에 없고, P10004는 ERP에 막 등록된 신규 품목이라 품목 차원에 없다고 가정합니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;
CREATE TABLE lab.dim_cust (LIKE dw.dim_cust INCLUDING ALL);
INSERT INTO lab.dim_cust SELECT * FROM dw.dim_cust;
SELECT setval(pg_get_serial_sequence('lab.dim_cust', 'cust_sk'), (SELECT MAX(cust_sk) FROM lab.dim_cust));
CREATE TABLE lab.fct_ord_line (LIKE dw.fct_ord_line INCLUDING ALL);
INSERT INTO lab.fct_ord_line SELECT * FROM dw.fct_ord_line;

-- 스테이징: 업무 키 그대로 (헤더 + 상세를 라인 grain으로)
CREATE TABLE lab.stg_ord_line AS
SELECT o.ord_no, d.ord_seq, o.ord_dt, o.cust_no, o.emp_no, d.item_cd, o.ord_stat_cd, d.ord_qty, d.uprc, d.ord_amt
  FROM erp.tb_ord o JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
 WHERE o.ord_dt >= DATE '2026-04-01';
INSERT INTO lab.stg_ord_line VALUES
 ('SO2026040004', 1, DATE '2026-04-04', 'C000204', 'E1002', 'P10001', '10',  30,  3000,  90000),  -- 거래처 미등록
 ('SO2026040005', 1, DATE '2026-04-04', 'C000301', 'E1003', 'P10004', '10', 100,  2000, 200000),  -- 품목 미등록
 ('SO2026040006', 1, DATE '2026-04-04', 'C000201', 'E1002', 'P10003', '10',  -5,  2500, -12500),  -- 수량 음수
 ('SO2026040007', 1, DATE '2026-04-04', 'C000202', 'E1004', 'P10002', '10',  10, 12000, 100000);  -- 금액 불일치

-- 오류 테이블: 할 일 목록 (처리상태 보유)
CREATE TABLE lab.etl_err_log (
  err_seq      BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  batch_id     VARCHAR(20)  NOT NULL,             -- 발생 배치
  tgt_tbl_nm   VARCHAR(30)  NOT NULL,             -- 타깃 테이블
  src_key_val  VARCHAR(50)  NOT NULL,             -- 원천 키 (주문번호-순번)
  err_col_nm   VARCHAR(30)  NOT NULL,             -- 오류 컬럼
  err_val      VARCHAR(100),                      -- 오류 값 (재처리 때 조회 키로 씀)
  err_rule_cd  VARCHAR(10)  NOT NULL,             -- 규칙 코드
  err_tp_cd    CHAR(1)      NOT NULL,             -- W 경고(-1 적재) / E 거부(미적재)
  proc_stat_cd CHAR(1)      NOT NULL DEFAULT 'N', -- N 미처리 / Y 처리완료
  reg_dtm      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  proc_dtm     TIMESTAMP
);
```

### SK 조회 → 규칙 검사 → MERGE

```sql
-- 1. SK 조회: 모두 LEFT JOIN, 못 찾으면 -1. 거래처는 주문일자에 유효한 버전
CREATE TABLE lab.wrk_ord_line AS
SELECT s.*,
       COALESCE(dd.date_sk, -1) AS ord_dt_sk, COALESCE(dc.cust_sk, -1) AS cust_sk,
       COALESCE(di.item_sk, -1) AS item_sk,   COALESCE(de.emp_sk,  -1) AS emp_sk
  FROM lab.stg_ord_line s
  LEFT JOIN dw.dim_date  dd ON dd.full_dt = s.ord_dt
  LEFT JOIN lab.dim_cust dc ON dc.cust_no = s.cust_no AND s.ord_dt BETWEEN dc.eff_strt_dt AND dc.eff_end_dt
  LEFT JOIN dw.dim_item  di ON di.item_cd = s.item_cd
  LEFT JOIN dw.dim_emp   de ON de.emp_no  = s.emp_no;

-- 2. 규칙 검사: 규칙 하나 = VALUES 한 줄. 걸린 것만 오류 테이블로
INSERT INTO lab.etl_err_log (batch_id, tgt_tbl_nm, src_key_val, err_col_nm, err_val, err_rule_cd, err_tp_cd)
SELECT 'B20260405', 'FCT_ORD_LINE', w.ord_no || '-' || w.ord_seq, v.col_nm, v.val, v.rule_cd, v.tp_cd
  FROM lab.wrk_ord_line w
 CROSS JOIN LATERAL (VALUES
   ('CUST_NO', w.cust_no,        'LKP_CUST', 'W', w.cust_sk = -1),
   ('ITEM_CD', w.item_cd,        'LKP_ITEM', 'W', w.item_sk = -1),
   ('ORD_DT',  w.ord_dt::TEXT,   'LKP_DATE', 'W', w.ord_dt_sk = -1),
   ('ORD_QTY', w.ord_qty::TEXT,  'QTY_NEG',  'E', w.ord_qty < 0),
   ('ORD_AMT', w.ord_amt::TEXT,  'AMT_CALC', 'E', w.ord_amt <> w.ord_qty * w.uprc)
 ) AS v (col_nm, val, rule_cd, tp_cd, hit)
 WHERE v.hit;

-- 3. 거부(E) 미처리 건을 뺀 나머지를 MERGE (값이 다를 때만 UPDATE)
MERGE INTO lab.fct_ord_line t
USING (SELECT w.* FROM lab.wrk_ord_line w
        WHERE NOT EXISTS (SELECT 1 FROM lab.etl_err_log e
                           WHERE e.src_key_val = w.ord_no || '-' || w.ord_seq
                             AND e.err_tp_cd = 'E' AND e.proc_stat_cd = 'N')) s
ON t.ord_no = s.ord_no AND t.ord_seq = s.ord_seq
WHEN MATCHED AND (t.ord_dt_sk, t.cust_sk, t.item_sk, t.emp_sk, t.ord_stat_cd, t.ord_qty, t.uprc, t.ord_amt)
     IS DISTINCT FROM (s.ord_dt_sk, s.cust_sk, s.item_sk, s.emp_sk, s.ord_stat_cd, s.ord_qty, s.uprc, s.ord_amt) THEN
  UPDATE SET ord_dt_sk = s.ord_dt_sk, cust_sk = s.cust_sk, item_sk = s.item_sk, emp_sk = s.emp_sk,
             ord_stat_cd = s.ord_stat_cd, ord_qty = s.ord_qty, uprc = s.uprc, ord_amt = s.ord_amt,
             load_dtm = CURRENT_TIMESTAMP, batch_id = 'B20260405'
WHEN NOT MATCHED THEN
  INSERT (ord_dt_sk, cust_sk, item_sk, emp_sk, ord_no, ord_seq, ord_stat_cd, ord_qty, uprc, ord_amt, batch_id)
  VALUES (s.ord_dt_sk, s.cust_sk, s.item_sk, s.emp_sk, s.ord_no, s.ord_seq,
          s.ord_stat_cd, s.ord_qty, s.uprc, s.ord_amt, 'B20260405');

SELECT src_key_val, err_col_nm, err_val, err_rule_cd, err_tp_cd FROM lab.etl_err_log ORDER BY err_seq;
```

| src_key_val | err_col_nm | err_val | err_rule_cd | err_tp_cd |
|---|---|---|---|---|
| SO2026040004-1 | CUST_NO | C000204 | LKP_CUST | W |
| SO2026040005-1 | ITEM_CD | P10004 | LKP_ITEM | W |
| SO2026040006-1 | ORD_QTY | -5 | QTY_NEG | E |
| SO2026040007-1 | ORD_AMT | 100000 | AMT_CALC | E |

경고 2건은 -1로 들어갔고 거부 2건은 들어가지 않았습니다. 기존 4월 2건은 값이 같아 BATCH_ID가 'INIT'로 남습니다.

### 재처리: 마스터가 도착하면 -1을 고친다

다음 날 다온약국 마스터가 왔습니다. 오류 테이블의 미처리 경고만 따라가 해당 행을 고치고 처리완료로 바꿉니다.

```sql
INSERT INTO lab.dim_cust (cust_no, cust_nm, cust_tp_cd, cust_tp_nm, rgn_cd, rgn_nm, emp_no, emp_nm, eff_strt_dt, batch_id)
VALUES ('C000204', '다온약국', '02', '약국', 'SEL', '서울', 'E1002', '이서연', DATE '2026-04-01', 'B20260406');

WITH fix AS (
  UPDATE lab.fct_ord_line f
     SET cust_sk = dc.cust_sk, load_dtm = CURRENT_TIMESTAMP, batch_id = 'B20260406'
    FROM lab.etl_err_log e, dw.dim_date d, lab.dim_cust dc
   WHERE e.err_rule_cd = 'LKP_CUST' AND e.proc_stat_cd = 'N'
     AND e.src_key_val = f.ord_no || '-' || f.ord_seq
     AND f.cust_sk = -1
     AND d.date_sk = f.ord_dt_sk
     AND dc.cust_no = e.err_val AND d.full_dt BETWEEN dc.eff_strt_dt AND dc.eff_end_dt
  RETURNING f.ord_no || '-' || f.ord_seq AS src_key_val
)
UPDATE lab.etl_err_log e
   SET proc_stat_cd = 'Y', proc_dtm = CURRENT_TIMESTAMP
  FROM fix
 WHERE e.src_key_val = fix.src_key_val AND e.err_rule_cd = 'LKP_CUST';

SELECT f.ord_no, f.cust_sk, c.cust_nm, f.batch_id
  FROM lab.fct_ord_line f JOIN lab.dim_cust c ON c.cust_sk = f.cust_sk
 WHERE f.ord_no = 'SO2026040004';
```

SO2026040004은 새 SK(7)의 다온약국으로 바뀌고 BATCH_ID가 B20260406이 됩니다. 오류 테이블의 SO2026040004-1은 처리상태 Y입니다. ERR_VAL에 남긴 업무 키 덕분에 재조회가 됩니다.

### 매핑정의서: FCT_ORD_LINE

| 타깃 컬럼 | 타깃 논리명 | 원천 (테이블.컬럼) | 변환 규칙 | 실패·예외 처리 |
|---|---|---|---|---|
| ORD_DT_SK | 주문일자SK | TB_ORD.ORD_DT | DIM_DATE.FULL_DT = ORD_DT 의 DATE_SK | 없으면 -1, 경고 LKP_DATE |
| CUST_SK | 거래처SK | TB_ORD.CUST_NO, ORD_DT | DIM_CUST 에서 CUST_NO 일치 + ORD_DT BETWEEN EFF_STRT_DT AND EFF_END_DT | 없으면 -1, 경고 LKP_CUST, 마스터 도착 후 재처리 |
| ITEM_SK | 품목SK | TB_ORD_DTL.ITEM_CD | DIM_ITEM.ITEM_CD 일치 | 없으면 -1, 경고 LKP_ITEM |
| EMP_SK | 사원SK | TB_ORD.EMP_NO | DIM_EMP.EMP_NO 일치 (주문을 받은 사원) | 없으면 -1 |
| ORD_NO | 주문번호 | TB_ORD_DTL.ORD_NO | 그대로 (Degenerate) | NULL 불가, 거부 |
| ORD_SEQ | 주문순번 | TB_ORD_DTL.ORD_SEQ | 그대로 | NULL 불가, 거부 |
| ORD_STAT_CD | 주문상태코드 | TB_ORD.ORD_STAT_CD | 그대로. 취소(90)도 적재, 지표에서 제외 | 코드 외 값은 경고 |
| ORD_QTY | 주문수량 | TB_ORD_DTL.ORD_QTY | 그대로 | 음수면 거부 QTY_NEG (반품 표현 규칙 확정 전까지) |
| UPRC | 단가 | TB_ORD_DTL.UPRC | 그대로 (비가산) | |
| ORD_AMT | 주문금액 | TB_ORD_DTL.ORD_AMT | 그대로. ORD_QTY × UPRC 와 같아야 함 | 다르면 거부 AMT_CALC |
| LOAD_DTM | 적재일시 | (시스템) | 값이 바뀐 행만 CURRENT_TIMESTAMP | |
| BATCH_ID | 배치ID | (시스템) | 'B' + 배치기준일 다음 날 YYYYMMDD | |

표 위에는 테이블 단위 정보를 적습니다. grain(주문상세 1행), 적재 유형(증분 MERGE, 키 ORD_NO + ORD_SEQ), 원천 조인·추출 조건(Day 22 워터마크), 선행 작업(DIM_* 완료), 삭제 처리입니다.

## Before / After

| 항목 | Before | After |
|---|---|---|
| 차원 조회 | INNER JOIN → 실패 행 소리 없이 누락 | LEFT JOIN + COALESCE(-1) + 경고 로그 |
| 잘못된 측정값 | 그대로 적재 → 대시보드에 음수 매출 | 거부 규칙으로 차단, 오류 테이블 보관 |
| 오류 기록 | 배치 로그에 "실패 2건" 문자열 | 원천 키·컬럼·값·규칙·처리상태가 있는 테이블 |
| 재처리 | 전체 재적재 | 미처리 오류만 따라가 해당 행 갱신 |
| 문서 | "ERP 주문 → DW 주문" 한 줄 | 컬럼별 원천·변환·예외 규칙이 있는 매핑정의서 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| -1 vs 추정 멤버 | 업무 키 자체가 없거나 엉터리면 -1 | 업무 키는 정상이고 마스터만 늦으면 추정 멤버(Day 20)로 바로 SK 부여 |
| 경고 vs 거부 | 금액·수량이 맞고 분류만 모르면 경고(-1 적재) | 측정값이 틀리면 거부. 틀린 숫자는 빠진 숫자보다 위험 |
| 거부 건과 대사 | 거부 건이 적으면 대사 결과에 "보류 N건, 금액 X원"을 함께 표시 | 거부가 많으면 배치 자체를 실패로 보고 하류(BI 갱신)를 멈춤 (임계치는 현업과 합의) |
| 오류 테이블 형태 | 규칙이 다양하면 지금처럼 세로형(오류 1건 = 1행) | 테이블별로 거부 행 전체를 보관해야 하면 타깃과 같은 모양의 거부 테이블을 추가 |
| 감사 컬럼 | 단일 원천이면 LOAD_DTM·BATCH_ID | 다원천·감사 요구가 크면 SRC_SYS_CD, 최초·최종 배치ID 분리 |

현업에 물을 질문은 둘입니다. "모르는 거래처의 매출도 합계에 보여야 합니까?"(대개 예 → -1), "틀린 금액은 보여 주지 말고 보류할까요?"(대개 예 → 거부). 이 답이 경고·거부 등급표가 됩니다.

## 흔한 실수 3가지

1. **INNER JOIN으로 SK를 찾는 실수.** 오류가 나지 않아서 더 위험합니다. 매 배치 "스테이징 건수 = 적재 + 거부"를 대사해 누락을 잡습니다.
2. **Type 2 차원을 업무 키만으로 조회하는 실수.** 버전 수만큼 팩트가 복제됩니다. 사건 일자 BETWEEN 조건을 넣고 조회 후 건수를 스테이징과 비교합니다.
3. **오류를 문자열 로그로만 남기는 실수.** 원천 키와 오류 값이 없으면 재처리를 못 하고 결국 전체를 다시 돌립니다. 처리상태가 있는 테이블로 남깁니다.

## 셀프 체크 질문

**Q1. 팩트 적재 중 거래처를 못 찾은 행을 버리지 않고 -1로 넣는 이유와, 그 대가로 해야 할 일은 무엇입니까?**

:::answer 모범 답안 보기
버리면 원천과 DW의 합계가 어긋나고, 그 차이를 아무도 모른 채 보고됩니다. -1로 넣으면 총매출은 원천과 맞고 "거래처 미확인" 항목으로 보여 문제가 드러납니다. 대가는 두 가지입니다. 왜 -1인지 원천 키와 오류 값을 오류 테이블에 남기고, 마스터가 오면 -1을 올바른 SK로 고치는 재처리 작업을 운영해야 합니다. -1 건수와 금액은 매일 모니터링 지표로 둡니다.
:::

**Q2. 매핑정의서에는 무엇을 적어야 하고, 개발자가 SQL을 보면 되는데 왜 따로 씁니까?**

:::answer 모범 답안 보기
테이블 단위로 grain, 적재 유형과 키, 원천 조인·추출 조건, 선행 작업, 삭제 처리를 적고, 컬럼 단위로 원천 컬럼, 변환 규칙, 조인 실패·예외 처리를 적습니다. 따로 쓰는 이유는 읽는 사람이 다르기 때문입니다. 현업과 품질 담당은 "취소도 들어가나, 모르는 거래처는 어떻게 되나"를 SQL 없이 확인해야 하고, 테스트 담당은 이 문서로 테스트 케이스를 만듭니다. 문서가 기준이고 SQL은 구현이므로, 둘이 다르면 어느 쪽이 틀렸는지 판단할 근거가 됩니다. 리니지(Day 11)의 원본이기도 합니다.
:::

**Q3. 거부된 행은 원천이 고쳐진 뒤 어떻게 다시 들어오게 하겠습니까?**

:::answer 모범 답안 보기
원천 수정이 수정일시를 갱신한다면 다음 증분 배치가 자연히 다시 가져옵니다. 이때 같은 키의 미처리 거부 건을 처리완료로 바꾸는 단계를 넣습니다. 수정일시가 갱신된다는 보장이 없으면, 미처리 거부 키 목록을 다음 배치 추출 조건에 OR로 강제로 포함합니다. 재검사에서 다시 걸리면 거부를 유지하고, 일정 기간 이상 미처리인 건은 현업 담당자에게 알림을 보냅니다.
:::

## 오늘의 과제

**과제 1.** 품목 P10004(품목명 '한빛펜정 250mg 30T', FG, BOX, 유효기간 36개월, 가상)가 품목 차원에 등록됐습니다. 품목 차원 복사본(lab.dim_item)을 만들어 등록하고, 미처리 LKP_ITEM 경고를 따라 팩트의 ITEM_SK를 고친 뒤 처리완료로 바꾸세요. 결과 모양은 `ord_no, item_sk, item_nm` 1행(SO2026040005, 새 SK 6, 한빛펜정 250mg 30T)입니다.

:::answer 해설 보기
거래처 재처리와 같은 모양입니다. 품목은 Type 1이라 사건 일자 조건 없이 업무 키로만 찾습니다.

```sql
CREATE TABLE lab.dim_item (LIKE dw.dim_item INCLUDING ALL);
INSERT INTO lab.dim_item SELECT * FROM dw.dim_item;
SELECT setval(pg_get_serial_sequence('lab.dim_item', 'item_sk'), (SELECT MAX(item_sk) FROM lab.dim_item));
INSERT INTO lab.dim_item (item_cd, item_nm, item_tp_cd, item_tp_nm, unit_cd, shelf_life_mm, batch_id)
VALUES ('P10004', '한빛펜정 250mg 30T', 'FG', '완제품', 'BOX', 36, 'B20260406');

WITH fix AS (
  UPDATE lab.fct_ord_line f
     SET item_sk = di.item_sk, load_dtm = CURRENT_TIMESTAMP, batch_id = 'B20260406'
    FROM lab.etl_err_log e, lab.dim_item di
   WHERE e.err_rule_cd = 'LKP_ITEM' AND e.proc_stat_cd = 'N'
     AND e.src_key_val = f.ord_no || '-' || f.ord_seq
     AND f.item_sk = -1 AND di.item_cd = e.err_val
  RETURNING f.ord_no || '-' || f.ord_seq AS src_key_val
)
UPDATE lab.etl_err_log e SET proc_stat_cd = 'Y', proc_dtm = CURRENT_TIMESTAMP
  FROM fix WHERE e.src_key_val = fix.src_key_val AND e.err_rule_cd = 'LKP_ITEM';

SELECT f.ord_no, f.item_sk, i.item_nm
  FROM lab.fct_ord_line f JOIN lab.dim_item i ON i.item_sk = f.item_sk
 WHERE f.ord_no = 'SO2026040005';
```

실무 재처리는 다른 팩트(출고 등)도 같은 품목으로 -1이 됐을 수 있으므로 TGT_TBL_NM별로 같은 로직을 돌립니다.
:::

**과제 2.** 이번 배치(B20260405)의 적재 대사 쿼리를 작성하세요. 스테이징 건수 = 팩트에 존재하는 건수 + 미처리 거부 건수인지, 금액도 같은 식으로 맞는지 1행으로 보여 줍니다. 결과 모양은 `stg_cnt, fct_cnt, rej_cnt, diff_cnt, stg_amt, fct_amt, rej_amt` 이며 6, 4, 2, 0과 447,500 / 360,000 / 87,500입니다.

:::answer 해설 보기
"이번 배치가 새로 넣은 건수"로 대사하면 값이 같아 갱신되지 않은 기존 행이 빠지므로, 스테이징 키가 팩트에 **존재하는지**로 셉니다. 금액도 함께 봐야 경고(-1) 건이 실제로 합계에 들어갔는지 확인됩니다.

```sql
WITH s AS (
  SELECT w.*,
         EXISTS (SELECT 1 FROM lab.fct_ord_line f WHERE f.ord_no = w.ord_no AND f.ord_seq = w.ord_seq) AS in_fct_yn,
         EXISTS (SELECT 1 FROM lab.etl_err_log e
                  WHERE e.src_key_val = w.ord_no || '-' || w.ord_seq
                    AND e.err_tp_cd = 'E' AND e.proc_stat_cd = 'N') AS rej_yn
    FROM lab.stg_ord_line w
)
SELECT COUNT(*) AS stg_cnt,
       COUNT(*) FILTER (WHERE in_fct_yn) AS fct_cnt,
       COUNT(*) FILTER (WHERE rej_yn) AS rej_cnt,
       COUNT(*) - COUNT(*) FILTER (WHERE in_fct_yn) - COUNT(*) FILTER (WHERE rej_yn) AS diff_cnt,
       SUM(ord_amt) AS stg_amt,
       SUM(ord_amt) FILTER (WHERE in_fct_yn) AS fct_amt,
       SUM(ord_amt) FILTER (WHERE rej_yn) AS rej_amt
  FROM s;
```

거부 금액 87,500원은 -12,500원(음수 수량)과 100,000원(금액 불일치)의 합입니다. 대시보드 주석에 "검증 보류 2건, 87,500원"을 표시하면 정 과장이 ERP 화면과의 차이를 스스로 설명할 수 있습니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 매핑정의서 | 테이블 단위(grain, 적재 유형·키, 원천 조인·추출 조건, 선행 작업, 삭제 처리) + 컬럼 단위(원천, 변환 규칙, 실패·예외 처리) |
| 데이터 품질 규칙 목록 | 규칙 코드(LKP_CUST, QTY_NEG, AMT_CALC …), 등급(W/E), 근거, 합의자 |
| 오류 처리 정의서 | 오류 테이블 구조, 처리상태 흐름, 재처리 방법과 담당, 장기 미처리 알림 기준 |
| 테이블정의서 | 감사 컬럼(LOAD_DTM, BATCH_ID, 필요 시 SRC_SYS_CD)과 갱신 규칙 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 19 "ETL Subsystems and Techniques"(서로게이트 키 파이프라인, 오류 이벤트 처리, 감사 차원), Chapter 20 "ETL System Design and Development Process and Tasks".
- Kimball Group 웹사이트의 Dimensional Modeling Techniques 항목 — 늦게 도착하는 차원, 알 수 없는 차원 행.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 아키텍처 영역: 데이터 통합과 매핑 설계.
