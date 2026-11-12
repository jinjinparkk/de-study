# Day 22. ETL vs ELT, CDC, 증분 적재

## 오늘의 한 줄

증분 적재는 "바뀐 것만 가져온다"가 아니라 **"무엇이 바뀌었는지 어떻게 알고, 몇 번을 다시 돌려도 같은 결과가 나오게 한다"** 는 설계입니다. 워터마크 구간, MERGE 반영, 별도 삭제 감지, 실패 시 워터마크 고정. 이 넷이 견고한 복제 작업의 뼈대입니다.

## 왜 중요한가

한빛제약 ERP(Oracle)에서 DW로 주문을 옮기는 기존 작업이 "어제 등록된 주문만 INSERT"라고 해 봅시다. 4월 3일 접수된 주문이 4월 4일 확정으로 바뀌어도 DW는 계속 접수 상태로 남고, ERP 운영팀이 잘못 들어간 주문을 지우면 DW에는 유령 주문이 남습니다. 배치가 중간에 죽어 다시 돌리면 같은 주문이 두 번 들어가 정 과장의 대시보드 매출이 부풉니다. 모두 **변경 감지·삭제·재실행 규칙**이 없어서 생기는 사고입니다.

## 핵심 개념

### 1. ETL과 ELT: 변환을 어디서 하나

ETL은 꺼낸 데이터를 **중간 서버에서 고친 뒤** 넣고, ELT는 **원본 그대로 DW에 내려놓은 뒤** DW 안에서 SQL로 고칩니다. 차이는 변환 엔진의 위치와 원본 보관 여부입니다.

| 기준 | ETL | ELT |
|---|---|---|
| 변환 위치 | 별도 ETL 서버·도구 | DW 엔진 안 (SQL, dbt 등) |
| 원본 보관 | 변환 결과만 남기 쉬움 | Staging에 원본이 남음 → 재처리·감사에 유리 |
| 잘 맞는 곳 | DW 연산이 귀하거나 적재 전에 마스킹할 데이터가 있을 때 | DW가 연산을 감당하고 변환을 SQL로 버전 관리할 때 |
| 약점 | 로직이 도구 안에 숨어 리니지 추적이 어려움 | DW 연산 비용 증가, 민감 정보가 원본째 들어옴 |

실무는 섞어 씁니다. 형 변환·문자셋 같은 최소 정리는 추출 단계에서, 업무 변환(SK 매핑, 차원 결합)은 DW 안에서 합니다. 한빛 그룹 DW의 선택 근거는 Day 28의 ADR에서 다룹니다.

### 2. 전체 적재와 증분 적재

전체 적재(full load)는 매번 전체를 지우고 다시 넣어 단순하고 삭제까지 반영되지만, 커지면 원천 부하와 배치 시간이 감당이 안 됩니다. 증분 적재(incremental load)는 바뀐 행만 가져오므로 빠르지만 "바뀐 행"을 아는 수단이 필요합니다.

판단 기준은 크기보다 **변경을 알 수 있는가**입니다. 거래처·품목처럼 작은 마스터는 전체 적재 + 비교(스냅샷 diff)가 가장 견고합니다. 주문·출고처럼 크고 계속 쌓이는 트랜잭션만 증분으로 갑니다.

### 3. CDC: 변경을 아는 네 가지 방법

변경 데이터 캡처(CDC, Change Data Capture)는 원천의 변경을 잡아내는 방법의 총칭입니다.

| 방식 | 원리 | 장점 | 약점 |
|---|---|---|---|
| 타임스탬프(워터마크) | UPD_DTM > 지난 기준시각 | 구현이 쉬움, 원천 변경 불필요 | 수정일시를 안 채우는 프로그램, 물리 삭제를 못 잡음 |
| 스냅샷 비교 | 원천 전체(또는 키 목록)와 타깃 비교 | 삭제까지 정확 | 큰 테이블은 비교 비용이 큼 |
| 트리거 | 원천 테이블 트리거가 변경로그 기록 | 삭제 포함, 실시간에 가까움 | 운영계 성능·변경 승인 부담 (ERP 운영팀이 대개 거절) |
| 로그 기반 | DB 변경 로그(redo/WAL)를 읽음 | 원천 부하 적음, 삭제·순서 정확 | 별도 도구·권한·운영 역량 필요 |

TB_ORD에는 REG_DTM·UPD_DTM이 있지만 **TB_ORD_DTL에는 UPD_DTM이 없습니다**(Day 2의 의도된 빈틈). 그래서 헤더는 워터마크로, 상세는 "바뀐 헤더의 상세를 비교·교체"로 처리하는 것이 오늘의 핵심 결정입니다.

### 4. 워터마크와 겹침 구간

워터마크(watermark)는 "어디까지 가져왔는가"를 기록한 기준시각입니다. 이번 배치는 `(지난 워터마크, 이번 기준시각]`을 가져오고, 성공하면 워터마크를 옮깁니다. 함정은 둘입니다. 00:59에 수정되고 01:02에 커밋된 행은 01:00 배치도, 다음 배치도 못 봅니다. 그래서 몇 분을 **겹쳐서** 다시 읽습니다. 또 기준시각은 배치 시작 때 한 번 정해 끝까지 씁니다. 겹쳐 읽으면 같은 행이 두 번 오므로 반영은 반드시 MERGE(UPSERT)입니다.

### 5. 멱등성: 몇 번을 돌려도 같은 결과

멱등성(idempotency)은 같은 입력으로 작업을 여러 번 실행해도 결과가 한 번 실행한 것과 같은 성질입니다. 재시도·백필(Day 24)이 안전하려면 필수입니다. 조건은 세 가지입니다. INSERT 대신 키 기준 MERGE, "값이 실제로 달라졌을 때만" UPDATE, 워터마크 전진은 모든 단계가 성공한 같은 트랜잭션 안에서. 하나라도 빠지면 재실행이 데이터를 바꿉니다.

## 예시

### 원천·워터마크·타깃 준비

기존 작업은 "매일 01:00, ERP.TB_ORD WHERE REG_DTM >= 어제 → INSERT"입니다. 이것을 워터마크 + MERGE + 삭제 감지로 다시 짭니다. erp 테이블을 바꾸지 않도록 원천을 lab으로 복사해 "Oracle 원천" 역할을 맡기고, 등록·수정 일시는 가상 값으로 둡니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;

-- (1) 원천 흉내: 주문 헤더·상세 복사, 등록·수정 일시는 가상 값으로 고정
CREATE TABLE lab.src_ord AS
SELECT ord_no, ord_dt, cust_no, emp_no, ord_stat_cd,
       ord_dt + TIME '09:00' AS reg_dtm,
       CASE WHEN ord_stat_cd IN ('20','30','90') THEN ord_dt + TIME '18:00' END AS upd_dtm
  FROM erp.tb_ord;
ALTER TABLE lab.src_ord ADD PRIMARY KEY (ord_no);
CREATE TABLE lab.src_ord_dtl AS SELECT * FROM erp.tb_ord_dtl;
ALTER TABLE lab.src_ord_dtl ADD PRIMARY KEY (ord_no, ord_seq);

-- (2) 워터마크 테이블: 작업마다 "어디까지 가져왔나" 한 행
CREATE TABLE lab.etl_wtrmk (
  job_nm         VARCHAR(50) PRIMARY KEY,         -- 작업명
  last_wtrmk_dtm TIMESTAMP   NOT NULL,            -- 마지막 성공 기준시각
  last_batch_id  VARCHAR(20),
  upd_dtm        TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP
);
INSERT INTO lab.etl_wtrmk (job_nm, last_wtrmk_dtm) VALUES ('ODS_ORD', TIMESTAMP '1900-01-01 00:00');

-- (3) 타깃: ODS 주문 헤더·상세 (원천 컬럼 + 삭제여부 + 감사 컬럼)
CREATE TABLE lab.ods_ord (
  ord_no VARCHAR(14) PRIMARY KEY, ord_dt DATE NOT NULL, cust_no VARCHAR(10) NOT NULL,
  emp_no      VARCHAR(10) NOT NULL, ord_stat_cd VARCHAR(2) NOT NULL,
  src_reg_dtm TIMESTAMP, src_upd_dtm TIMESTAMP,
  src_del_yn  CHAR(1)     NOT NULL DEFAULT 'N',   -- 원천삭제여부
  load_dtm    TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP, batch_id VARCHAR(20) NOT NULL
);
CREATE TABLE lab.ods_ord_dtl (
  ord_no  VARCHAR(14) NOT NULL, ord_seq NUMERIC(4) NOT NULL, item_cd VARCHAR(10) NOT NULL,
  ord_qty NUMERIC(10) NOT NULL, uprc NUMERIC(15) NOT NULL, ord_amt NUMERIC(15) NOT NULL,
  load_dtm TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP, batch_id VARCHAR(20) NOT NULL,
  PRIMARY KEY (ord_no, ord_seq)
);
```

### 적재 프로시저: 한 트랜잭션, 다섯 단계

```sql
CREATE OR REPLACE FUNCTION lab.sp_load_ods_ord(p_batch_id VARCHAR, p_to_dtm TIMESTAMP)
RETURNS TABLE (step VARCHAR, row_cnt BIGINT) LANGUAGE plpgsql AS $$
DECLARE
  v_from TIMESTAMP;
  v_cnt  BIGINT;
BEGIN
  -- 1. 추출 구간: (지난 워터마크 - 겹침 10분, 이번 기준시각]
  SELECT last_wtrmk_dtm - INTERVAL '10 minutes' INTO v_from
    FROM lab.etl_wtrmk WHERE job_nm = 'ODS_ORD' FOR UPDATE;
  DROP TABLE IF EXISTS tmp_chg;
  CREATE TEMP TABLE tmp_chg AS
  SELECT * FROM lab.src_ord
   WHERE COALESCE(upd_dtm, reg_dtm) >  v_from
     AND COALESCE(upd_dtm, reg_dtm) <= p_to_dtm;
  step := '1 추출 헤더'; SELECT COUNT(*) INTO row_cnt FROM tmp_chg; RETURN NEXT;

  -- 2. 헤더 MERGE: 값이 실제로 달라졌을 때만 UPDATE
  MERGE INTO lab.ods_ord t
  USING tmp_chg s ON t.ord_no = s.ord_no
  WHEN MATCHED AND (t.ord_stat_cd, t.cust_no, t.emp_no, t.ord_dt, t.src_upd_dtm, t.src_del_yn)
                   IS DISTINCT FROM (s.ord_stat_cd, s.cust_no, s.emp_no, s.ord_dt, s.upd_dtm, 'N') THEN
    UPDATE SET ord_stat_cd = s.ord_stat_cd, cust_no = s.cust_no, emp_no = s.emp_no, ord_dt = s.ord_dt,
               src_upd_dtm = s.upd_dtm, src_del_yn = 'N',
               load_dtm = CURRENT_TIMESTAMP, batch_id = p_batch_id
  WHEN NOT MATCHED THEN
    INSERT (ord_no, ord_dt, cust_no, emp_no, ord_stat_cd, src_reg_dtm, src_upd_dtm, batch_id)
    VALUES (s.ord_no, s.ord_dt, s.cust_no, s.emp_no, s.ord_stat_cd, s.reg_dtm, s.upd_dtm, p_batch_id);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  step := '2 헤더 MERGE'; row_cnt := v_cnt; RETURN NEXT;

  -- 3. 상세: UPD_DTM 이 없으므로 바뀐 헤더의 상세를 비교해 교체 (같은 값이면 건드리지 않음)
  DELETE FROM lab.ods_ord_dtl t
   USING tmp_chg c
   WHERE t.ord_no = c.ord_no
     AND NOT EXISTS (SELECT 1 FROM lab.src_ord_dtl s
                      WHERE s.ord_no = t.ord_no AND s.ord_seq = t.ord_seq
                        AND (s.item_cd, s.ord_qty, s.uprc, s.ord_amt) = (t.item_cd, t.ord_qty, t.uprc, t.ord_amt));
  INSERT INTO lab.ods_ord_dtl (ord_no, ord_seq, item_cd, ord_qty, uprc, ord_amt, batch_id)
  SELECT s.ord_no, s.ord_seq, s.item_cd, s.ord_qty, s.uprc, s.ord_amt, p_batch_id
    FROM lab.src_ord_dtl s JOIN tmp_chg c ON c.ord_no = s.ord_no
   WHERE NOT EXISTS (SELECT 1 FROM lab.ods_ord_dtl t WHERE t.ord_no = s.ord_no AND t.ord_seq = s.ord_seq);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  step := '3 상세 교체'; row_cnt := v_cnt; RETURN NEXT;

  -- 4. 삭제 감지: 원천 키 목록에 없는 주문은 지우지 않고 표시 (소프트 삭제)
  UPDATE lab.ods_ord t
     SET src_del_yn = 'Y', load_dtm = CURRENT_TIMESTAMP, batch_id = p_batch_id
   WHERE t.src_del_yn = 'N'
     AND NOT EXISTS (SELECT 1 FROM lab.src_ord s WHERE s.ord_no = t.ord_no);
  GET DIAGNOSTICS v_cnt = ROW_COUNT;
  step := '4 삭제 감지'; row_cnt := v_cnt; RETURN NEXT;

  -- 5. 워터마크 전진: 같은 트랜잭션. 실패하면 전부 롤백, W 그대로
  UPDATE lab.etl_wtrmk
     SET last_wtrmk_dtm = p_to_dtm, last_batch_id = p_batch_id, upd_dtm = CURRENT_TIMESTAMP
   WHERE job_nm = 'ODS_ORD';
  RETURN;
END $$;
```

### 1회차(초기)와 2회차(변경 반영)

```sql
-- 1회차: 4월 4일 01:00 기준. 워터마크가 1900년이라 사실상 전체 적재
SELECT * FROM lab.sp_load_ods_ord('B20260404', TIMESTAMP '2026-04-04 01:00');

-- 4월 4일 낮의 원천 변경 (모두 가상)
UPDATE lab.src_ord SET ord_stat_cd = '20', upd_dtm = TIMESTAMP '2026-04-04 10:00' WHERE ord_no = 'SO2026040001';
UPDATE lab.src_ord_dtl SET ord_qty = 25, ord_amt = 75000 WHERE ord_no = 'SO2026040001' AND ord_seq = 1;
INSERT INTO lab.src_ord VALUES ('SO2026040003', DATE '2026-04-04', 'C000301', 'E1003', '10',
                                TIMESTAMP '2026-04-04 11:00', NULL);
INSERT INTO lab.src_ord_dtl VALUES ('SO2026040003', 1, 'P10002', 50, 12000, 600000);
DELETE FROM lab.src_ord_dtl WHERE ord_no = 'SO2026040002';   -- ERP 운영팀이 취소 주문을 물리 삭제
DELETE FROM lab.src_ord     WHERE ord_no = 'SO2026040002';

-- 2회차: 4월 5일 01:00 기준
SELECT * FROM lab.sp_load_ods_ord('B20260405', TIMESTAMP '2026-04-05 01:00');
```

| 단계 | 1회차 | 2회차 | 2회차 의미 |
|---|---|---|---|
| 1 추출 헤더 | 6 | 2 | SO2026040001(확정), SO2026040003(신규) |
| 2 헤더 MERGE | 6 | 2 | UPDATE 1 + INSERT 1 |
| 3 상세 교체 | 8 | 2 | 수량이 바뀐 라인 교체 1 + 신규 라인 1 |
| 4 삭제 감지 | 0 | 1 | SO2026040002 → SRC_DEL_YN = 'Y' |

### 재실행해도 같은가

워터마크를 되돌려 같은 구간을 다시 돌려도 바뀌는 행은 0이어야 합니다.

```sql
CREATE VIEW lab.v_ods_hash AS          -- 업무 값 + 배치ID 전체를 해시 한 값으로
SELECT md5(string_agg(o.ord_no || o.ord_stat_cd || o.src_del_yn || o.batch_id
                      || COALESCE(d.ord_amt::TEXT || d.batch_id, '-'), ',' ORDER BY o.ord_no, d.ord_seq)) AS hash_val
  FROM lab.ods_ord o LEFT JOIN lab.ods_ord_dtl d ON d.ord_no = o.ord_no;
CREATE TABLE lab.chk_before AS SELECT * FROM lab.v_ods_hash;

UPDATE lab.etl_wtrmk SET last_wtrmk_dtm = TIMESTAMP '2026-04-04 01:00' WHERE job_nm = 'ODS_ORD';
SELECT * FROM lab.sp_load_ods_ord('B20260405', TIMESTAMP '2026-04-05 01:00');

SELECT b.hash_val = a.hash_val AS same_result_yn FROM lab.chk_before b, lab.v_ods_hash a;
```

재실행은 추출 2, MERGE 0, 상세 0, 삭제 0이고 `same_result_yn`은 true입니다. "값이 달라졌을 때만" 조건이 없으면 같은 값으로 UPDATE되며 LOAD_DTM·BATCH_ID가 바뀌고, 그 컬럼으로 증분을 도는 하류 작업(Day 23)이 헛돌게 됩니다.

:::note Oracle 차이
Oracle MERGE는 조건을 `WHEN MATCHED THEN UPDATE SET ... WHERE (조건)`으로 붙이고, `IS DISTINCT FROM`이 없어 `DECODE(t.col, s.col, 0, 1) = 1` 같은 NULL 안전 비교를 씁니다. 함수 대신 PL/SQL 프로시저와 `SQL%ROWCOUNT`를 씁니다. 로그 기반 CDC는 별도 도구(예: Oracle GoldenGate)가 필요하고 ERP 운영팀의 권한 승인이 선행 조건입니다.
:::

## Before / After

| 항목 | Before | After |
|---|---|---|
| 변경 감지 | REG_DTM(등록)만 봄 → 상태 변경 누락 | COALESCE(UPD_DTM, REG_DTM) 워터마크 + 10분 겹침 |
| 반영 방식 | INSERT → 재실행 시 중복 | 키 기준 MERGE, 값이 다를 때만 UPDATE |
| 상세 | 헤더와 같은 조건으로 INSERT | UPD_DTM 없음을 인정하고 바뀐 주문의 상세를 비교·교체 |
| 삭제 | 감지 안 함 → 유령 주문 | 키 목록 비교, SRC_DEL_YN 소프트 삭제 (감사 추적 유지) |
| 실패 시 | 어디까지 들어갔는지 모름 | 한 트랜잭션, 실패하면 워터마크 그대로 → 그냥 다시 실행 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 전체 vs 증분 | 작은 마스터(거래처·품목·사원), 변경 감지 수단이 없는 테이블은 전체 + 비교 | 크고 계속 쌓이는 트랜잭션(주문·출고·전표)은 증분 |
| CDC 방식 | 수정일시가 믿을 만하고 물리 삭제가 드물면 워터마크 + 주기적 키 비교 | 삭제가 잦거나 순서·지연이 중요하면 로그 기반 CDC를 ERP 운영팀과 협의 |
| 삭제 반영 | 감사·대사가 필요한 DW는 소프트 삭제(SRC_DEL_YN) | 개인정보 파기 요건이 있으면 물리 삭제 + 삭제 로그 |
| 상세에 수정일시 없음 | 상세 변경 때 헤더도 갱신된다고 ERP 팀이 보증하면 헤더 기준 교체 | 보증이 없으면 최근 기간 상세 해시 비교 + UPD_DTM 추가 요구 |

ERP 운영팀에 꼭 물을 질문은 셋입니다. "수정일시는 모든 프로그램이 채웁니까?", "물리 삭제가 일어납니까?", "상세만 바뀌는 화면이 있습니까?" 답은 매핑정의서(Day 23)에 적습니다.

## 흔한 실수 3가지

1. **워터마크를 실행 시각으로 바로 옮기는 실수.** 추출 시작과 저장 사이에 커밋된 행이 영원히 빠집니다. 기준시각 고정, 겹침 구간, MERGE.
2. **"증분이니까 INSERT"로 짜는 실수.** 재시도 한 번에 중복이나 PK 오류가 납니다. 키 기준 MERGE가 기본값입니다.
3. **삭제를 잊는 실수.** 워터마크는 물리 삭제를 원리상 못 봅니다. 삭제 감지 경로를 따로 두고 원천과 DW 건수를 매일 대사합니다(Day 12).

## 셀프 체크 질문

**Q1. 워터마크 기반 증분 적재에서 데이터가 빠질 수 있는 경우를 두 가지 이상 들고, 각각 어떻게 막겠습니까?**

:::answer 모범 답안 보기
첫째, 늦게 커밋된 트랜잭션은 이미 지나간 구간에 속해 빠집니다. 겹침 구간 + MERGE로 막습니다. 둘째, 수정일시를 채우지 않는 프로그램·일괄 UPDATE는 ERP 운영팀에 확인하고 최근 기간 해시 비교로 보완합니다. 셋째, 물리 삭제는 수정일시가 남지 않으므로 키 비교로 따로 감지합니다.
:::

**Q2. 멱등한 적재 작업이란 무엇이고, 왜 오케스트레이션보다 먼저 확보해야 합니까?**

:::answer 모범 답안 보기
같은 입력(같은 기준시각·구간)으로 여러 번 돌려도 결과가 한 번 돌린 것과 같은 작업입니다. 키 기준 MERGE, 값이 다를 때만 갱신, 워터마크 전진을 같은 트랜잭션에 묶어 확보합니다. 오케스트레이터의 재시도·백필·수동 재실행은 모두 "다시 돌려도 안전하다"를 전제로 합니다. 멱등하지 않으면 재시도가 중복을 만들고 복구 때마다 사람이 데이터를 지워야 합니다.
:::

**Q3. ERP 운영팀이 트리거나 로그 기반 CDC를 허용하지 않는다고 합니다. 삭제를 어떻게 반영하겠습니까?**

:::answer 모범 답안 보기
부하가 작은 키 목록(주문번호만)을 받아 타깃과 비교하고, 없는 키는 SRC_DEL_YN = 'Y'로 표시합니다. 키 목록도 크면 최근 N개월은 매일, 전체는 월 1회 비교합니다. 동시에 업무 규칙을 묻습니다. 주문은 원래 취소(90)로 처리하는데 물리 삭제는 누가 언제 하는지 확인하고, 가능하면 상태 변경으로 운영하도록 요구사항에 올립니다. 삭제 표시 건수가 급증하면 알림을 보냅니다.
:::

## 오늘의 과제

**과제 1.** TB_ORD_DTL에는 수정일시가 없어서, 헤더는 그대로 두고 상세 단가만 고치면 증분 적재가 놓칩니다. 원천(lab.src_ord_dtl)에서 SO2026030004 1번 라인 단가를 3,000원(금액 60,000원)으로 바꾼 뒤, 원천과 ODS 상세를 전체 비교해 차이 나는 주문번호를 찾으세요. 결과 모양은 `ord_no, ord_seq, diff_tp` 이며 SO2026030004 1번이 '원천만'·'ODS만' 두 행으로 나옵니다.

:::answer 해설 보기
EXCEPT를 양방향으로 돌립니다. 같은 키가 양쪽에 다 나오면 값이 바뀐 행, 한쪽에만 나오면 추가·삭제된 행입니다. 최근 기간에 한정해 매일 돌리면 상세 변경 누락의 안전망이 됩니다. 원천 변경은 BEGIN … ROLLBACK으로 되돌립니다.

```sql
BEGIN;
UPDATE lab.src_ord_dtl SET uprc = 3000, ord_amt = 60000 WHERE ord_no = 'SO2026030004' AND ord_seq = 1;

SELECT ord_no, ord_seq, diff_tp
  FROM (SELECT ord_no, ord_seq, item_cd, ord_qty, uprc, ord_amt, '원천만' AS diff_tp FROM lab.src_ord_dtl
        EXCEPT
        SELECT ord_no, ord_seq, item_cd, ord_qty, uprc, ord_amt, '원천만' FROM lab.ods_ord_dtl) a
UNION ALL
SELECT ord_no, ord_seq, diff_tp
  FROM (SELECT ord_no, ord_seq, item_cd, ord_qty, uprc, ord_amt, 'ODS만' AS diff_tp FROM lab.ods_ord_dtl o
         WHERE NOT EXISTS (SELECT 1 FROM lab.ods_ord h WHERE h.ord_no = o.ord_no AND h.src_del_yn = 'Y')
        EXCEPT
        SELECT ord_no, ord_seq, item_cd, ord_qty, uprc, ord_amt, 'ODS만' FROM lab.src_ord_dtl) b
 ORDER BY ord_no, ord_seq, diff_tp;
ROLLBACK;
```

원천 삭제된 주문(SO2026040002)의 상세는 뺐습니다. 빼지 않으면 매일 'ODS만'으로 나와 진짜 차이를 가립니다.
:::

**과제 2.** 적재 후 대사 쿼리를 작성하세요. 주문월별로 원천 주문 건수·상세 금액 합과, ODS의 삭제되지 않은 주문 건수·금액 합을 나란히 보여 주고 차이를 계산합니다. 결과 모양은 `ord_yyyymm, src_cnt, ods_cnt, src_amt, ods_amt, diff_amt` 이며 202603은 4건 2,366,000원, 202604는 2건 675,000원으로 양쪽이 같습니다.

:::answer 해설 보기
건수는 헤더 기준, 금액은 상세 합계 기준으로 따로 집계한 뒤 월로 붙입니다. 헤더와 상세를 조인한 뒤 COUNT(*)를 하면 라인 수가 세어지므로 COUNT(DISTINCT)를 쓰거나 헤더를 따로 셉니다.

```sql
WITH s AS (
  SELECT TO_CHAR(h.ord_dt, 'YYYYMM') AS ord_yyyymm, COUNT(DISTINCT h.ord_no) AS cnt, SUM(d.ord_amt) AS amt
    FROM lab.src_ord h JOIN lab.src_ord_dtl d ON d.ord_no = h.ord_no
   GROUP BY 1
), o AS (
  SELECT TO_CHAR(h.ord_dt, 'YYYYMM') AS ord_yyyymm, COUNT(DISTINCT h.ord_no) AS cnt, SUM(d.ord_amt) AS amt
    FROM lab.ods_ord h JOIN lab.ods_ord_dtl d ON d.ord_no = h.ord_no
   WHERE h.src_del_yn = 'N'
   GROUP BY 1
)
SELECT COALESCE(s.ord_yyyymm, o.ord_yyyymm) AS ord_yyyymm,
       s.cnt AS src_cnt, o.cnt AS ods_cnt, s.amt AS src_amt, o.amt AS ods_amt,
       COALESCE(s.amt, 0) - COALESCE(o.amt, 0) AS diff_amt
  FROM s FULL OUTER JOIN o ON o.ord_yyyymm = s.ord_yyyymm
 ORDER BY 1;
```

202604의 675,000원은 SO2026040001(75,000원)과 신규 SO2026040003(600,000원)의 합이며, 삭제된 SO2026040002는 양쪽에서 빠졌습니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 인터페이스 정의서 | 원천 시스템·테이블, 추출 주기, CDC 방식(워터마크 컬럼, 겹침 구간, 키 비교 주기), 전송 방식, 담당자 |
| 매핑정의서 | 테이블별 적재 유형(전체/증분/교체), MERGE 키, 변경 비교 컬럼, 삭제 처리 규칙(소프트/물리) |
| 프로그램 사양서 | 단계 순서, 트랜잭션 경계, 워터마크 갱신 시점, 재실행 시 동작(멱등성 조건) |
| 데이터 품질 규칙 목록 | 원천 대비 건수·금액 대사, 상세 해시 비교 범위, 삭제 표시 건수 임계치 |
| ERP 운영팀 요청서 | TB_ORD_DTL UPD_DTM 추가, 물리 삭제 정책, CDC 도구 권한 요청 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 19 "ETL Subsystems and Techniques"(변경 데이터 캡처, 추출 하위 시스템).
- PostgreSQL 공식 문서 — MERGE, PL/pgSQL.
- Oracle Database SQL Language Reference — MERGE.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 아키텍처 영역: 데이터 통합(ETL)과 인터페이스.
