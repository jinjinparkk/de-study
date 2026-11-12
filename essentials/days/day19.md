# Day 19. SCD (Slowly Changing Dimension)

## 오늘의 한 줄

SCD는 "차원 속성이 바뀌었을 때 **과거 팩트를 어느 값으로 보이게 할 것인가**"를 속성마다 정하는 규칙입니다. 덮어쓰면(Type 1) 과거가 현재 값으로 다시 쓰이고, 새 행을 만들면(Type 2) 과거가 당시 값으로 남습니다. 어느 쪽이 맞는지는 기술이 아니라 **실적 귀속 같은 업무 규칙**이 정합니다.

## 왜 중요한가

청솔내과의원의 담당이 3월 16일 김도윤에서 이서연으로 바뀌었습니다. 거래처 차원을 Type 1로 덮어쓰면, 4월에 3월 실적을 다시 뽑는 순간 김도윤이 3월 2일에 받은 60,000원 주문이 이서연 실적으로 옮겨 갑니다. 김도윤의 3월 달성률은 이미 보고된 숫자와 달라지고, 인센티브 정산 자료와 대시보드가 어긋납니다. 반대로 "지금 담당자 기준으로 거래처 이력을 보고 싶다"는 요청에 Type 2만 있으면 답하기 번거롭습니다. 속성마다 SCD 유형을 정하지 않으면 이 논쟁이 대시보드가 열린 뒤에 터집니다.

## 핵심 개념

### 1. 다섯 가지 유형을 한 문장씩

| 유형 | 바뀌면 | 과거 팩트에 보이는 값 | 한빛 예시 속성 |
|---|---|---|---|
| Type 0 | 바꾸지 않음 (원래 값 보존) | 최초 값 | 로트 제조일자, 거래처 최초거래일 |
| Type 1 | 덮어쓰기 | 현재 값 | 거래처명 오타 정정, 사업자등록번호 정정 |
| Type 2 | 새 행 추가 (유효기간, 현재여부) | 당시 값 | 담당영업사원, 거래처유형 변경 |
| Type 3 | "이전 값" 컬럼 추가 | 현재 값 + 직전 값 한 개 | 조직개편 전·후 지역 (한 번의 큰 변경 비교) |
| Type 6 | Type 2 행 + 모든 행에 "현재 값" 컬럼(Type 1) | 당시 값과 현재 값 둘 다 | 담당영업사원 (당시 담당 + 현재 담당) |

Type 6이라는 이름은 1 + 2 + 3 = 6에서 왔습니다. 이 밖에 자주 바뀌는 속성을 따로 떼는 미니 차원(Type 4) 같은 기법도 있지만, 실무 판단의 대부분은 위 다섯 가지 안에서 이뤄집니다.

### 2. Type 2의 구조: 버전마다 새 SK

쉽게 말하면 거래처 하나가 담당 변경 때마다 **새 버전 행**을 갖고, 버전마다 서로게이트 키(CUST_SK)가 다릅니다. 팩트는 사건 일자에 유효했던 버전의 SK를 들고 있으므로, 팩트를 차원과 조인하기만 하면 자동으로 당시 값이 나옵니다.

공통 DW의 DIM_CUST가 이미 이 구조입니다. 유효시작일자(EFF_STRT_DT), 유효종료일자(EFF_END_DT, 포함, 현재 = 9999-12-31), 현재여부(CURR_YN)를 두고 Day 7의 선분이력 규칙을 그대로 따릅니다. 업무 키(CUST_NO)는 버전마다 반복되므로 "거래처 수"는 `COUNT(DISTINCT CUST_NO)` 또는 `CURR_YN = 'Y'`로 셉니다.

### 3. 유효기간은 업무 일자인가, 적재 일자인가

Type 2 새 버전의 시작일을 무엇으로 할지가 실무의 핵심 결정입니다. 원천에 업무 유효일(TB_CUST_EMP_HIST.APLY_STRT_DT)이 있으면 그것을 씁니다. 원천이 현재 값만 주면 변경을 감지한 **적재일**을 쓸 수밖에 없고, 그러면 3월 16일 변경을 3월 18일에 적재한 경우 이틀간의 주문이 이전 담당으로 붙습니다. 이 오차를 허용할지, ERP 팀에 이력 테이블을 요구할지가 아키텍트의 판단입니다.

### 4. 팩트의 사원 FK와 차원의 담당 속성은 다른 질문이다

주문 헤더(TB_ORD.EMP_NO)에는 "주문을 받은 사원"이, 거래처 차원에는 "그 시점 거래처 담당"이 있습니다. 대개 같지만 대리 수주, 공동 담당이 있으면 달라집니다. 그래서 공통 DW는 둘 다 둡니다. FCT_ORD_LINE.EMP_SK는 "누가 받았나", DIM_CUST.EMP_NO는 "누구 거래처였나"입니다. 영업기획이 정해야 할 것은 "실적은 어느 쪽으로 귀속하는가"입니다.

## 예시

### 실적 귀속 세 가지 답

청솔내과의원(C000101)의 3월 주문은 두 건입니다. SO2026030002(3월 2일, 60,000원, 김도윤 수주), SO2026030004(3월 20일, 64,000원, 이서연 수주).

```sql
-- 공통 DW 거래처 차원: 청솔내과의원의 두 버전
SELECT cust_sk, cust_no, emp_no, emp_nm, eff_strt_dt, eff_end_dt, curr_yn
  FROM dw.dim_cust WHERE cust_no = 'C000101' ORDER BY eff_strt_dt;

-- 같은 두 주문을 세 기준으로 귀속
SELECT f.ord_no, d.full_dt AS ord_dt, f.ord_amt,
       e.emp_nm  AS rcv_emp_nm,          -- 팩트 사원: 주문을 받은 사원
       c.emp_nm  AS t2_emp_nm,           -- Type 2: 주문일자 당시 거래처 담당
       cc.emp_nm AS t1_emp_nm            -- Type 1처럼: 현재 거래처 담당
  FROM dw.fct_ord_line f
  JOIN dw.dim_date d  ON d.date_sk = f.ord_dt_sk
  JOIN dw.dim_emp  e  ON e.emp_sk  = f.emp_sk
  JOIN dw.dim_cust c  ON c.cust_sk = f.cust_sk
  JOIN dw.dim_cust cc ON cc.cust_no = c.cust_no AND cc.curr_yn = 'Y'
 WHERE c.cust_no = 'C000101'
 ORDER BY f.ord_no;
```

| ord_no | ord_dt | ord_amt | 받은 사원 | Type 2 (당시 담당) | Type 1 (현재 담당) |
|---|---|---|---|---|---|
| SO2026030002 | 2026-03-02 | 60,000 | 김도윤 | 김도윤 | 이서연 |
| SO2026030004 | 2026-03-20 | 64,000 | 이서연 | 이서연 | 이서연 |

Type 1로 보면 김도윤의 3월 청솔내과의원 실적은 0원이 됩니다. 영업 인센티브처럼 "그때 누가 했나"가 중요한 지표는 Type 2(또는 팩트의 받은 사원), "지금 내 거래처의 과거 추이"를 보는 영업 관리 화면은 현재 담당 기준이 맞습니다. 두 요구가 다 있으면 Type 6입니다.

### Type 2 적재: MERGE 한 문장

5월 1일 배치에서 원천이 다음을 줬다고 가정합니다(모두 가상). 늘봄약국(C000202) 담당이 5월 1일부터 최하은 → 박지훈, 신규 거래처 새봄약국(C000203) 등록, 미래종합병원 거래처명 정정(Type 1).

```sql
CREATE SCHEMA IF NOT EXISTS lab;

-- 실습용 차원 복사본 (서로게이트 키 시퀀스를 현재 최댓값 뒤로)
CREATE TABLE lab.dim_cust (LIKE dw.dim_cust INCLUDING ALL);
INSERT INTO lab.dim_cust SELECT * FROM dw.dim_cust;
SELECT setval(pg_get_serial_sequence('lab.dim_cust', 'cust_sk'), (SELECT MAX(cust_sk) FROM lab.dim_cust));

-- 스테이징: 원천 거래처 + 현재 담당 (업무 유효시작일 포함)
CREATE TABLE lab.stg_cust AS
SELECT c.cust_no, c.cust_nm, c.cust_tp_cd, c.rgn_cd, h.emp_no, h.aply_strt_dt AS emp_aply_strt_dt
  FROM erp.tb_cust c
  JOIN erp.tb_cust_emp_hist h ON h.cust_no = c.cust_no AND h.aply_end_dt = DATE '9999-12-31';

UPDATE lab.stg_cust SET emp_no = 'E1003', emp_aply_strt_dt = DATE '2026-05-01' WHERE cust_no = 'C000202';
UPDATE lab.stg_cust SET cust_nm = '미래종합병원(본원)' WHERE cust_no = 'C000102';
INSERT INTO lab.stg_cust VALUES ('C000203', '새봄약국', '02', 'SEL', 'E1002', DATE '2026-05-01');
```

적재는 두 단계입니다. Type 1 속성은 **모든 버전**을 덮어쓰고, Type 2 속성은 MERGE로 "현재 행 닫기 + 새 버전 넣기"를 한 문장에 처리합니다.

```sql
-- 1단계: Type 1 속성(거래처명·유형·지역) 덮어쓰기 — 과거 버전까지 전부
UPDATE lab.dim_cust t
   SET cust_nm = s.cust_nm, load_dtm = CURRENT_TIMESTAMP, batch_id = 'B20260502'
  FROM lab.stg_cust s
 WHERE t.cust_no = s.cust_no AND t.cust_nm <> s.cust_nm;

-- 2단계: Type 2 속성(담당영업사원) MERGE
--   변경된 거래처는 소스에 두 번 넣음: (가) 업무 키로 매칭 → 현재 행 닫기
--                                      (나) 키를 NULL로 → 매칭 안 됨 → 새 버전 INSERT
MERGE INTO lab.dim_cust t
USING (
  SELECT s.cust_no AS merge_key, s.* FROM lab.stg_cust s
  UNION ALL
  SELECT NULL, s.*
    FROM lab.stg_cust s
    JOIN lab.dim_cust d ON d.cust_no = s.cust_no AND d.curr_yn = 'Y'
   WHERE d.emp_no <> s.emp_no
) src
ON t.cust_no = src.merge_key AND t.curr_yn = 'Y'
WHEN MATCHED AND t.emp_no <> src.emp_no THEN
  UPDATE SET eff_end_dt = src.emp_aply_strt_dt - 1, curr_yn = 'N',
             load_dtm = CURRENT_TIMESTAMP, batch_id = 'B20260502'
WHEN NOT MATCHED THEN
  INSERT (cust_no, cust_nm, cust_tp_cd, cust_tp_nm, rgn_cd, rgn_nm, emp_no, emp_nm,
          eff_strt_dt, eff_end_dt, curr_yn, batch_id)
  VALUES (src.cust_no, src.cust_nm, src.cust_tp_cd,
          CASE src.cust_tp_cd WHEN '01' THEN '병원' WHEN '02' THEN '약국' WHEN '03' THEN '도매상' ELSE '기타' END,
          src.rgn_cd,
          CASE src.rgn_cd WHEN 'SEL' THEN '서울' WHEN 'GGD' THEN '경기' WHEN 'BSN' THEN '부산' ELSE '기타' END,
          src.emp_no, (SELECT emp_nm FROM erp.tb_emp WHERE emp_no = src.emp_no),
          src.emp_aply_strt_dt, DATE '9999-12-31', 'Y', 'B20260502');

SELECT cust_sk, cust_no, cust_nm, emp_no, emp_nm, eff_strt_dt, eff_end_dt, curr_yn, batch_id
  FROM lab.dim_cust
 WHERE cust_no IN ('C000101', 'C000102', 'C000202', 'C000203')
 ORDER BY cust_no, eff_strt_dt;
```

| cust_no | cust_nm | emp_nm | eff_strt_dt | eff_end_dt | curr_yn |
|---|---|---|---|---|---|
| C000101 | 청솔내과의원 | 김도윤 | 2025-01-01 | 2026-03-15 | N |
| C000101 | 청솔내과의원 | 이서연 | 2026-03-16 | 9999-12-31 | Y |
| C000102 | 미래종합병원(본원) | 박지훈 | 2025-01-01 | 9999-12-31 | Y |
| C000202 | 늘봄약국 | 최하은 | 2025-01-01 | 2026-04-30 | N |
| C000202 | 늘봄약국 | 박지훈 | 2026-05-01 | 9999-12-31 | Y |
| C000203 | 새봄약국 | 이서연 | 2026-05-01 | 9999-12-31 | Y |

늘봄약국은 옛 버전이 4월 30일로 닫히고 새 SK의 버전이 생겼습니다. 4월 3일 주문(SO2026040001)은 계속 옛 SK를 가리키므로 최하은 실적으로 남습니다. 같은 MERGE를 한 번 더 돌려도 바뀌는 행이 없어야 합니다(멱등성).

```sql
-- 멱등성 점검: 같은 배치를 다시 돌리면 변경 대상(담당이 다른 현재 행)이 0건
SELECT COUNT(*) AS pending_chg_cnt
  FROM lab.stg_cust s
  JOIN lab.dim_cust d ON d.cust_no = s.cust_no AND d.curr_yn = 'Y'
 WHERE d.emp_no <> s.emp_no;

-- 선분 규칙 점검 (Day 7): 거래처마다 현재 행 1개, 다음 시작 = 이전 종료 + 1
SELECT cust_no, eff_strt_dt, eff_end_dt, next_strt_dt
  FROM (SELECT d.*, LEAD(eff_strt_dt) OVER (PARTITION BY cust_no ORDER BY eff_strt_dt) AS next_strt_dt
          FROM lab.dim_cust d) x
 WHERE next_strt_dt IS NOT NULL AND next_strt_dt <> eff_end_dt + 1;
```

두 쿼리 모두 0건입니다.

:::note Oracle 차이
Oracle MERGE는 `WHEN MATCHED THEN UPDATE ... WHERE 조건`과 `WHEN NOT MATCHED THEN INSERT ... WHERE 조건`을 각각 **하나씩만** 쓸 수 있고, 조건은 `WHEN ... AND`가 아니라 각 절 뒤의 WHERE로 붙입니다. 또 ON 절에 쓴 컬럼은 UPDATE할 수 없어서(ORA-38104) 위처럼 ON에 `CURR_YN`을 쓰고 그 컬럼을 갱신하는 문장은 Oracle에서 실패합니다. Oracle에서는 소스에서 대상의 ROWID를 미리 찾아 ON을 ROWID로 하거나, "UPDATE로 닫기 → INSERT로 새 버전"의 두 문장을 한 트랜잭션으로 씁니다. PostgreSQL은 15부터 MERGE를 지원하고, 여러 개의 `WHEN MATCHED AND ...` 절을 쓸 수 있습니다.
:::

### Type 6: 당시 담당과 현재 담당을 한 행에

```sql
-- 현재 담당 컬럼을 추가하고 모든 버전에 현재 값을 덮어씀 (Type 1 부분)
ALTER TABLE lab.dim_cust ADD COLUMN curr_emp_no VARCHAR(10), ADD COLUMN curr_emp_nm VARCHAR(50);
UPDATE lab.dim_cust t
   SET curr_emp_no = c.emp_no, curr_emp_nm = c.emp_nm
  FROM lab.dim_cust c
 WHERE c.cust_no = t.cust_no AND c.curr_yn = 'Y';

-- 청솔내과의원 3월 주문: 한 조인으로 두 기준을 모두
SELECT f.ord_no, f.ord_amt, c.emp_nm AS hist_emp_nm, c.curr_emp_nm
  FROM dw.fct_ord_line f
  JOIN lab.dim_cust c ON c.cust_sk = f.cust_sk
 WHERE c.cust_no = 'C000101'
 ORDER BY f.ord_no;
```

lab.dim_cust의 SK는 dw.dim_cust에서 복사했으므로 공통 팩트와 그대로 조인됩니다. 담당이 다시 바뀌면 새 버전 추가(Type 2)와 함께 그 거래처의 모든 행의 CURR_EMP_*를 갱신(Type 1)해야 하므로, 적재 로직이 하나 더 늘어나는 것이 Type 6의 비용입니다.

## Before / After

**Before: 거래처 테이블을 그대로 복사, 매일 덮어쓰기**

| 문제 | 결과 |
|---|---|
| 담당 변경을 덮어씀 | 지난달 실적이 새 담당에게 이동, 보고된 숫자와 불일치 |
| 오타 정정과 담당 변경을 같은 방식으로 처리 | 둘 다 덮어쓰거나, 둘 다 새 버전을 만들어 버전이 불필요하게 늘어남 |
| 변경 시점이 적재일 | 업무 변경일과 며칠 어긋남 |

**After: 속성별 SCD 유형 명시**

| 속성 | 유형 | 근거 |
|---|---|---|
| 거래처명, 사업자등록번호 | Type 1 | 정정은 과거에도 정정된 값이 맞음 |
| 담당영업사원 | Type 2 (+ 현재 담당 컬럼 = Type 6) | 실적 귀속은 당시 담당, 영업 관리 화면은 현재 담당 |
| 거래처유형 | Type 2 | 약국 → 도매상 전환 시 과거 실적은 약국으로 남아야 함 |
| 최초거래일자 | Type 0 | 바뀌면 안 되는 값 |
| 유효기간 시작일 | 원천 이력의 업무 유효일 (없으면 적재일, 오차를 매핑정의서에 명시) | |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| Type 1 vs 2 | 값이 바뀌어도 과거를 새 값으로 보는 게 맞으면(정정) Type 1 | 과거 팩트가 당시 값으로 보여야 하면(조직·담당·분류 변경) Type 2 |
| Type 2 vs 팩트 FK | "누가 했나"가 사건마다 기록되면 팩트에 사원 FK로 (Type 2 불필요) | 사건에 기록이 없고 마스터 관계로만 정해지면 차원 Type 2 |
| Type 2 vs Type 6 | 사용자가 당시 기준만 보면 Type 2 | "현재 담당 기준 과거 추이"도 자주 보면 Type 6, 또는 현재 행만 거르는 뷰 |
| Type 3 | 조직개편처럼 한 번의 큰 변경 전후를 나란히 비교할 때 | 변경이 반복되면 Type 3은 직전 하나만 남으므로 부적합 |
| 변경이 아주 잦은 속성 | 신용등급처럼 매월 바뀌면 차원 행 폭증 → 미니 차원 분리나 팩트(스냅샷)로 | 드물게 바뀌면 Type 2 그대로 |
| 유효 시작일 | 원천 업무 유효일 사용 | 원천에 없으면 적재일 사용 + ERP 팀에 이력 요구를 요구사항으로 올림 |

결정의 출발점은 항상 현업 질문입니다. 정 과장에게 "담당이 바뀌면 지난달 실적은 누구 것입니까?"(Day 3)를 묻고, 답을 속성별 SCD 유형 표로 남깁니다.

## 흔한 실수 3가지

1. **모든 속성을 Type 2로 만드는 실수.** 오타 정정까지 새 버전을 만들면 버전이 늘고, 같은 거래처가 이름만 다른 두 행으로 보고서에 갈라져 나옵니다. 정정 성격의 속성은 Type 1로 분리합니다.
2. **팩트를 업무 키로 차원에 조인하는 실수.** `f.cust_no = d.cust_no`로 조인하면 Type 2 버전 수만큼 팩트가 복제됩니다(fan-out). 팩트는 SK로 조인하고, 업무 키 조인이 꼭 필요하면 `curr_yn = 'Y'` 또는 사건 일자 BETWEEN 조건을 붙입니다.
3. **새 버전만 넣고 이전 버전을 닫지 않는 실수.** 현재 행이 두 개가 되어 현재 기준 보고서가 두 배가 됩니다. 닫기와 넣기를 MERGE 한 문장이나 한 트랜잭션으로 처리하고, 현재 행 1개 점검을 매 배치 돌립니다.

## 셀프 체크 질문

**Q1. 청솔내과의원 담당이 3월 16일 바뀌었습니다. 3월 실적을 누구에게 귀속할지 어떻게 결정하고 DW에 어떻게 반영하겠습니까?**

:::answer 모범 답안 보기
먼저 영업기획(정 과장)에게 업무 규칙을 확인합니다. 보통 실적·인센티브는 "그 주문이 일어난 시점의 담당"이 기준이므로 3월 2일 주문 60,000원은 김도윤, 3월 20일 주문 64,000원은 이서연입니다. DW에는 거래처 차원의 담당영업사원을 Type 2로 두고 유효기간을 원천 이력(TB_CUST_EMP_HIST)의 업무 유효일로 잡아, 팩트가 주문일자에 유효했던 버전의 SK를 갖게 합니다. 주문을 받은 사원(TB_ORD.EMP_NO)도 팩트 FK로 따로 둡니다. "현재 담당 기준 과거 추이" 요구도 있으면 현재 담당 컬럼을 추가해 Type 6으로 만듭니다. 결정은 속성별 SCD 표와 매핑정의서에 남깁니다.
:::

**Q2. Type 2 MERGE에서 같은 거래처를 소스에 두 번 넣는 이유는 무엇입니까?**

:::answer 모범 답안 보기
담당이 바뀐 거래처는 한 배치에서 두 가지 일이 필요하기 때문입니다. 현재 행을 닫는 UPDATE와 새 버전을 넣는 INSERT입니다. MERGE는 소스 한 행에 대해 MATCHED 또는 NOT MATCHED 중 하나만 실행하므로, 변경 건을 업무 키로 한 번(매칭 → 닫기), 키를 NULL로 한 번(매칭 실패 → 새 버전 INSERT) 넣어 한 문장에 두 동작을 하게 만듭니다. 장점은 원자성과 멱등성입니다. 다시 돌리면 현재 행의 담당이 이미 같아서 NULL 키 행이 생기지 않습니다. Oracle은 ON 절 컬럼을 UPDATE할 수 없는 제약이 있어 ROWID 기반 ON이나 UPDATE + INSERT 두 문장으로 바꿉니다.
:::

**Q3. 원천이 거래처 현재 값만 주고 변경 이력을 주지 않습니다. Type 2를 어떻게 구현하고, 어떤 위험을 알리겠습니까?**

:::answer 모범 답안 보기
매 배치마다 스테이징의 현재 값과 차원의 현재 행을 비교해 변경을 감지하고(속성 해시 비교가 편함), 새 버전의 시작일을 적재일(또는 원천 수정일시가 있으면 그 일자)로 둡니다. 위험은 두 가지입니다. 실제 업무 변경일과 적재일 사이의 주문이 이전 버전에 붙는 시차 오류, 그리고 배치 사이에 두 번 바뀌면 중간 값이 사라지는 누락입니다. 이 오차를 매핑정의서에 명시하고, 실적 귀속처럼 정확도가 중요한 속성이면 ERP 팀에 이력 테이블(거래처담당이력)이나 변경로그를 요구사항으로 올립니다.
:::

## 오늘의 과제

**과제 1.** 원천 정합성 점검입니다. 주문 헤더의 영업사원(TB_ORD.EMP_NO)이 주문일자 기준 거래처 담당(TB_CUST_EMP_HIST)과 다른 주문을 찾으세요. 결과 모양은 `ord_no, ord_dt, cust_no, ord_emp_no, hist_emp_no` 이며 공통 샘플에서는 0행입니다.

:::answer 해설 보기
두 값이 다르면 "받은 사원"과 "담당"이 다른 주문이고, 실적 귀속 규칙이 결과를 바꾸는 건입니다. 0행이면 현재 샘플에서는 두 기준의 결과가 같다는 뜻이지만, 규칙은 그래도 정해 둬야 합니다. 담당 이력이 없는 주문도 잡히도록 LEFT JOIN을 씁니다.

```sql
SELECT o.ord_no, o.ord_dt, o.cust_no, o.emp_no AS ord_emp_no, h.emp_no AS hist_emp_no
  FROM erp.tb_ord o
  LEFT JOIN erp.tb_cust_emp_hist h
         ON h.cust_no = o.cust_no
        AND o.ord_dt BETWEEN h.aply_strt_dt AND h.aply_end_dt
 WHERE h.emp_no IS NULL OR h.emp_no <> o.emp_no
 ORDER BY o.ord_no;
```
:::

**과제 2.** 영업사원별 3월 실적(취소 제외)을 "당시 담당 기준(Type 2)"과 "현재 담당 기준(Type 1)"으로 나란히 보여 주세요. 결과 모양은 `emp_nm, hist_amt, curr_amt` 이며 김도윤은 60,000 / 0, 이서연은 146,000 / 206,000입니다.

:::answer 해설 보기
당시 기준은 팩트의 CUST_SK가 가리키는 버전의 담당, 현재 기준은 같은 거래처의 현재 행 담당입니다. 두 기준을 각각 집계한 뒤 사원으로 붙입니다.

```sql
WITH f AS (
  SELECT f.ord_amt, c.emp_nm AS hist_emp_nm, cc.emp_nm AS curr_emp_nm
    FROM dw.fct_ord_line f
    JOIN dw.dim_date d  ON d.date_sk = f.ord_dt_sk
    JOIN dw.dim_cust c  ON c.cust_sk = f.cust_sk
    JOIN dw.dim_cust cc ON cc.cust_no = c.cust_no AND cc.curr_yn = 'Y'
   WHERE d.yyyymm = '202603' AND f.ord_stat_cd <> '90'
), h AS (SELECT hist_emp_nm AS emp_nm, SUM(ord_amt) AS amt FROM f GROUP BY hist_emp_nm),
   c AS (SELECT curr_emp_nm AS emp_nm, SUM(ord_amt) AS amt FROM f GROUP BY curr_emp_nm)
SELECT COALESCE(h.emp_nm, c.emp_nm) AS emp_nm,
       COALESCE(h.amt, 0) AS hist_amt, COALESCE(c.amt, 0) AS curr_amt
  FROM h FULL OUTER JOIN c ON c.emp_nm = h.emp_nm
 ORDER BY emp_nm;
```

김도윤 60,000 / 0, 박지훈 2,160,000 / 2,160,000, 이서연 146,000 / 206,000입니다. 합계는 두 기준 모두 2,366,000원으로 같고 사람 사이에서만 이동합니다. 이 표를 정 과장에게 보여 주면 귀속 규칙 결정이 빨라집니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 차원 정의서 | 속성별 SCD 유형(0/1/2/3/6)과 근거, 유효기간 컬럼 규칙, 현재여부 |
| 요구사항정의서 | 실적 귀속 기준(당시 담당 / 받은 사원 / 현재 담당), 결정자와 결정일 |
| 매핑정의서 | 변경 감지 방법(속성 비교·해시), 유효 시작일의 원천(업무 유효일 또는 적재일), Type 1 속성의 전 버전 갱신 |
| 프로그램 사양서 | MERGE 로직, 멱등성 조건, Oracle 구현 방식(ROWID 또는 두 문장) |
| 데이터 품질 규칙 목록 | 현재 행 1개, 선분 겹침·빈틈 0건, 팩트 SK가 사건 일자의 유효 버전인지 점검 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 5 "Procurement"(천천히 변하는 차원 기법 Type 0~7).
- Kimball Group 웹사이트의 Dimensional Modeling Techniques 항목 — Slowly Changing Dimension 유형별 설명.
- PostgreSQL 공식 문서 — MERGE (PostgreSQL 15 이상).
- Oracle Database SQL Language Reference — MERGE.
