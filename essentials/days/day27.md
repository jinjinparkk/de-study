# Day 27. 클라우드 DW/레이크하우스

## 오늘의 한 줄

클라우드 DW의 본질은 두 가지입니다. **컬럼 단위로 저장해 필요한 컬럼만 읽는 것**, 그리고 **저장과 연산을 떼어 따로 늘리고 줄이는 것**. 제품 이름보다 이 두 원리가 설계를 바꾸고, Oracle에서 넘어갈 때는 빈 문자열·날짜·숫자처럼 "같아 보이는데 의미가 다른 것"이 사고를 냅니다.

## 왜 중요한가

그룹 DW를 온프레미스 Oracle에서 클라우드 DW로 옮겼더니 대시보드의 "사업자번호 미등록 거래처 수"가 수십 건에서 몇 건으로 줄었습니다. Oracle에서는 빈 문자열이 자동으로 NULL이었는데, 새 DW에서는 ''와 NULL이 다른 값이라 `IS NULL` 조건이 일부만 잡았기 때문입니다. 같은 날 "3월 주문"이 줄었는데, Oracle DATE에 들어 있던 시각이 이관 중 날짜로 잘리고 일부 조건은 시각 기준으로 바뀌어 경계일 데이터가 어긋났습니다. 클라우드 이관은 **SQL이 돌아가는 것과 숫자가 같은 것은 다르다**는 걸 증명하는 작업입니다.

## 핵심 개념

### 1. 컬럼너(columnar) 저장: 필요한 컬럼만 읽는다

행 저장(row store)은 한 행의 모든 컬럼을 붙여 저장합니다. 주문 한 건을 넣고 꺼내는 OLTP에 맞습니다. 컬럼 저장(column store)은 컬럼별로 값을 모아 저장합니다. "3월 품목별 금액 합계"는 일자·품목·금액 세 컬럼만 읽으면 되고, 같은 컬럼 값은 비슷해서 압축이 잘 됩니다. 대신 한 행 수정·삭제는 여러 컬럼 덩어리를 건드려야 해서 비쌉니다. 그래서 클라우드 DW는 대량 적재·대량 조회에 강하고, 행 단위 잦은 UPDATE에 약합니다. Day 22의 MERGE도 "바뀐 행만, 묶어서" 하는 쪽이 유리합니다.

```text
 행 저장                         컬럼 저장
 [SO..01|3/02|P10001|32000]      ORD_DT  [3/02 3/02 3/10 ...]
 [SO..01|3/02|P10003|50000]      ITEM_CD [P10001 P10003 ...]
 [SO..02|3/02|P10002|60000]      ORD_AMT [32000 50000 ...]
 한 건 넣고 꺼내기에 유리         몇 컬럼 집계·압축에 유리
```

### 2. 스토리지-컴퓨트 분리

전통 DW는 서버 한 대(또는 클러스터)가 저장과 연산을 같이 가집니다. 연산이 부족하면 디스크까지 같이 사야 하고, 야간 적재와 아침 조회가 같은 자원을 두고 다툽니다. 클라우드 DW는 데이터를 객체 저장소 같은 공용 저장 계층에 두고, 연산 자원을 필요할 때 붙였다 뗍니다. 그래서 **적재용 연산과 BI 조회용 연산을 분리**하거나, 월말에만 크게 늘리는 운영이 가능합니다. 대가는 비용 구조가 "쓴 만큼"으로 바뀌어, 비효율 쿼리가 곧 비용이 된다는 점입니다. Day 25의 프루닝·집계가 클라우드에서는 비용 설계가 됩니다.

### 3. 레이크하우스: 파일 위의 테이블

데이터 레이크는 객체 저장소에 파일(Parquet 등)을 쌓는 방식이라 싸고 유연하지만, 트랜잭션·스키마 관리가 약했습니다. 레이크하우스는 그 파일 위에 테이블 형식(Delta Lake, Apache Iceberg 같은 오픈 테이블 포맷)을 얹어 ACID 트랜잭션, 스키마 관리, 시점 조회를 제공합니다. Day 15의 메달리온(Bronze/Silver/Gold)이 주로 이 위에서 쓰이는 용어입니다. 모델링 원칙(grain, 차원, SCD)은 저장소가 바뀌어도 그대로입니다.

### 4. 네 플랫폼의 아키텍처 개념

가격·한도·세부 기능은 계약과 버전에 따라 바뀌므로, 선택 전에 반드시 공식 문서와 PoC로 확인합니다. 아래는 구조 개념만 비교합니다.

| 플랫폼 | 저장 | 연산 | 설계에서 신경 쓸 개념 |
|---|---|---|---|
| Snowflake | 관리형 저장소, 마이크로 파티션 단위 컬럼 저장 | 가상 웨어하우스(필요 시 켜고 끄는 연산 클러스터)를 용도별로 여러 개 | 적재·BI·분석 웨어하우스 분리, 클러스터링 키 |
| Databricks | 객체 저장소 위 Delta Lake 테이블 | Spark 클러스터, SQL 웨어하우스 | 메달리온 레이어, 파일 크기·정렬 관리, Unity Catalog로 거버넌스 |
| BigQuery | 관리형 컬럼 저장 | 서버리스, 슬롯 단위 연산 | 파티션·클러스터링으로 스캔 양 줄이기 (스캔 양이 곧 비용인 과금 방식이 있음) |
| Amazon Redshift | 클러스터 저장 또는 관리형 저장소(RA3 계열) | MPP 클러스터, 서버리스 옵션 | 분산 키·정렬 키 설계 (조인 키에 맞춘 데이터 배치) |

어느 것이든 공통 질문은 같습니다. 그룹사 원천(Oracle)에서 어떻게 넣나, 연산을 어떻게 나누나, 비용을 누가 어떻게 보나, Power BI·Tableau 연결은 어떤가, 그리고 거버넌스(권한·마스킹·리니지, Day 11·13)를 어디서 하나입니다.

### 5. Oracle → 클라우드 이관의 함정

| 항목 | Oracle | 이관 대상에서 흔한 차이 | 대응 |
|---|---|---|---|
| 빈 문자열 | `''` 는 NULL로 저장 | `''` 와 NULL이 다른 값 | 적재 시 `NULLIF(TRIM(col), '')` 로 통일, 규칙을 매핑정의서에 |
| 문자열 결합 | `'A' \|\| NULL = 'A'` | 많은 DBMS에서 결과가 NULL | `COALESCE(col, '')` 로 명시 (`CONCAT` 의 NULL 처리도 DBMS마다 다름: PostgreSQL은 무시, Snowflake·BigQuery는 NULL) |
| DATE | 날짜 + 시각(초)까지 보유 | DATE는 날짜만, 시각은 TIMESTAMP | 원천 DATE에 시각이 실제로 있는지 프로파일링 후 DATE/TIMESTAMP 결정 |
| 숫자 | NUMBER (정밀도 생략 가능) | 대상에 따라 정수 나눗셈(PostgreSQL·Redshift·SQL Server)이 되거나, 정밀도 없는 NUMBER가 소수 0자리로 잡혀 소수가 사라짐(Snowflake) | 금액·수량은 NUMERIC(p,s) 명시, 비율 계산은 형 변환 |
| 시퀀스 | SEQUENCE.NEXTVAL | IDENTITY 또는 시퀀스, 이관 후 시작값 재설정 필요 | 데이터 이관 후 MAX + 1 로 재설정 |
| MERGE·힌트·PL/SQL | Oracle 문법 | 문법·제약 차이 (Day 19·22 참고) | 저장 프로시저는 dbt 모델·SQL 스크립트로 재작성 검토 |
| 정렬·비교 | NLS 설정 따라 | 콜레이션 기본값 차이 | 한글 정렬·대소문자 비교 결과 검증 |

## 예시

### 함정 재현: 빈 문자열, 결합, 정수 나눗셈, 날짜 경계

Oracle에서 내려받은 거래처 추출 파일을 그대로 적재했다고 가정합니다. 원천 화면에서 비워 둔 사업자번호가 파일에는 빈 문자열로 왔습니다(값은 가상).

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

CREATE TABLE lab.mig_cust_raw (           -- 이관 원본 그대로 (Oracle 추출 파일)
  cust_no    VARCHAR(10),
  cust_nm    VARCHAR(100),
  biz_reg_no VARCHAR(12),
  rgn_cd     VARCHAR(3)
);
INSERT INTO lab.mig_cust_raw VALUES
 ('C000101', '청솔내과의원', '101-11-00001', 'SEL'),
 ('C000201', '햇살약국',     '',             'SEL'),
 ('C000202', '늘봄약국',     NULL,           'BSN'),
 ('C000301', '바른팜유통',   '  ',           'GGD');

-- Oracle IS NULL 로는 2건(''·NULL). 공백만 있는 값까지 미등록으로 보려면 TRIM 이 필요
SELECT COUNT(*) FILTER (WHERE biz_reg_no IS NULL)                  AS is_null_cnt,
       COUNT(*) FILTER (WHERE biz_reg_no = '')                     AS empty_cnt,
       COUNT(*) FILTER (WHERE NULLIF(TRIM(biz_reg_no), '') IS NULL) AS unified_cnt
  FROM lab.mig_cust_raw;

-- 문자열 결합: || 는 NULL 이 섞이면 결과 전체가 NULL (PostgreSQL CONCAT 은 NULL 을 무시하지만 DBMS마다 다름)
SELECT cust_no, cust_nm || ' / ' || biz_reg_no AS concat_op,
       CONCAT(cust_nm, ' / ', biz_reg_no)      AS concat_fn
  FROM lab.mig_cust_raw ORDER BY cust_no;

-- 정수 나눗셈: PostgreSQL 은 정수끼리 나누면 소수점이 버려짐
SELECT 7 / 2 AS int_div, 7::NUMERIC / 2 AS num_div,
       ROUND(100.0 * 146000 / 150000, 1) AS achv_rt;
```

첫 쿼리는 IS NULL 1건, 빈 문자열 1건, 통일 후 3건입니다. Oracle 시절 보고서(IS NULL)가 "미등록 2건"이었다면 새 DW에서는 규칙 없이 1건으로 줄어 보이고, 공백만 있는 값까지 미등록으로 보는 규칙(NULLIF(TRIM))을 정하면 3건입니다. 어느 쪽이 맞는지는 업무 정의로 정합니다. 결합 쿼리는 늘봄약국만 `concat_op` 가 NULL입니다. 나눗셈은 3, 3.5, 97.3입니다.

```sql
-- 날짜 경계: 시각이 있는 값을 DATE 범위로 거르면 마지막 날 오후가 빠짐
CREATE TABLE lab.mig_ord_raw (ord_no VARCHAR(14), ord_dtm TIMESTAMP);   -- Oracle DATE(시각 포함)를 TIMESTAMP로
INSERT INTO lab.mig_ord_raw VALUES
 ('SO2026030001', TIMESTAMP '2026-03-02 09:15:00'),
 ('SO2026030004', TIMESTAMP '2026-03-20 14:30:00'),
 ('SO2026039001', TIMESTAMP '2026-03-31 16:40:00');                       -- 가상: 월말 오후 주문

SELECT COUNT(*) FILTER (WHERE ord_dtm BETWEEN DATE '2026-03-01' AND DATE '2026-03-31') AS between_cnt,
       COUNT(*) FILTER (WHERE ord_dtm >= DATE '2026-03-01' AND ord_dtm < DATE '2026-04-01') AS half_open_cnt,
       COUNT(*) FILTER (WHERE ord_dtm::DATE BETWEEN DATE '2026-03-01' AND DATE '2026-03-31') AS cast_cnt
  FROM lab.mig_ord_raw;
```

BETWEEN은 2건, 반열림 범위와 날짜 변환은 3건입니다. `DATE '2026-03-31'`은 3월 31일 0시이므로 그날 오후가 빠집니다. Day 7의 규칙(일시는 반열림)을 이관 SQL에도 그대로 적용합니다. 날짜 변환(`::DATE`)은 결과는 맞지만 컬럼을 가공하므로 프루닝이 사라집니다(Day 25).

### 정제 적재와 시퀀스 재설정

```sql
-- 이관 대상: 빈 문자열 통일, 원천 키 유지, 신규 행용 IDENTITY
CREATE TABLE lab.mig_cust (
  cust_id    BIGINT GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,  -- Oracle 시퀀스 값을 그대로 옮김
  cust_no    VARCHAR(10)  NOT NULL UNIQUE,
  cust_nm    VARCHAR(100) NOT NULL,
  biz_reg_no VARCHAR(12),
  rgn_cd     VARCHAR(3)   NOT NULL
);
INSERT INTO lab.mig_cust (cust_id, cust_no, cust_nm, biz_reg_no, rgn_cd)
SELECT 100 + ROW_NUMBER() OVER (ORDER BY cust_no),          -- 원천 시퀀스 값이라고 가정 (101~104)
       TRIM(cust_no), TRIM(cust_nm), NULLIF(TRIM(biz_reg_no), ''), rgn_cd
  FROM lab.mig_cust_raw;

-- 값을 직접 넣었으므로 IDENTITY 시퀀스는 1에 머물러 있음 → 다음 INSERT는 1번부터 채번되어 원천 번호와 섞이고, 101번에 닿으면 충돌. MAX로 재설정
SELECT setval(pg_get_serial_sequence('lab.mig_cust', 'cust_id'), (SELECT MAX(cust_id) FROM lab.mig_cust));
INSERT INTO lab.mig_cust (cust_no, cust_nm, rgn_cd) VALUES ('C000203', '새봄약국', 'SEL');

SELECT cust_id, cust_no, biz_reg_no FROM lab.mig_cust ORDER BY cust_id;
```

새봄약국은 105번을 받습니다. 재설정을 빼먹으면 신규 등록이 1번부터 다시 채번되어 원천 번호와 섞이고, 101번에 닿는 날 PK 충돌로 실패합니다(원천 번호가 1부터였다면 이관 직후 첫 등록부터 충돌). 이런 문제는 이관 리허설에서 잡지 않으면 오픈 당일 아침에 터집니다.

:::note Oracle 차이
Oracle에서 `SELECT CASE WHEN '' IS NULL THEN 'Y' END FROM DUAL` 은 'Y'이고, `VARCHAR2` 컬럼에 ''를 넣으면 NULL이 저장됩니다. `'A' || NULL` 은 'A'입니다. Oracle 시퀀스는 `CREATE SEQUENCE ... START WITH`, 값은 `seq.NEXTVAL`로 얻고, 재설정은 `ALTER SEQUENCE ... RESTART START WITH n`(지원 버전 확인) 또는 시퀀스 재생성으로 합니다. Oracle DATE 리터럴 `DATE '2026-03-31'`도 0시이므로 BETWEEN 함정은 Oracle 안에서도 같습니다.
:::

### 이관 대사: 건수·합계·해시

```sql
-- 원천(추출 원본)과 대상의 동등성: 정제 규칙을 원천 쪽에 똑같이 적용한 뒤 비교
SELECT 'raw' AS side, COUNT(*) AS cnt,
       md5(string_agg(TRIM(cust_no) || '|' || COALESCE(NULLIF(TRIM(biz_reg_no), ''), '~'), ',' ORDER BY TRIM(cust_no))) AS hash_val
  FROM lab.mig_cust_raw
UNION ALL
SELECT 'target', COUNT(*),
       md5(string_agg(cust_no || '|' || COALESCE(biz_reg_no, '~'), ',' ORDER BY cust_no))
  FROM lab.mig_cust WHERE cust_no <> 'C000203';
```

두 행의 건수(4)와 해시가 같으면 이관과 정제가 정확합니다. 실무에서는 테이블별 건수, 금액 컬럼 합계, 키 + 주요 컬럼 해시를 원천 DB와 대상 DB에서 각각 계산해 비교하고, 해시는 같은 정렬·같은 NULL 표기 규칙으로 만들어야 의미가 있습니다.

## Before / After

| 항목 | Before (그대로 옮기기) | After (이관 설계) |
|---|---|---|
| 빈 문자열 | 원천 값 그대로 → '' 와 NULL 혼재 | 적재 시 NULLIF(TRIM) 통일, 품질 규칙으로 '' 0건 점검 |
| 날짜 | Oracle DATE → DATE 일괄 | 프로파일링: 시각 있는 컬럼은 TIMESTAMP, 일시 조건은 반열림 |
| 숫자 | NUMBER → 정수형·소수 0자리로 추정 | 금액·수량 NUMERIC(p,s) 명시, 비율은 형 변환 |
| 시퀀스 | 재설정 누락 | 이관 체크리스트에 시퀀스·IDENTITY 재설정 |
| 검증 | "SQL이 에러 없이 돈다" | 테이블별 건수·합계·해시 대사, 주요 리포트 숫자 비교 |
| 연산 | 한 자원으로 적재·조회 | 적재용·BI용 연산 분리, 비용 모니터링 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 클라우드 DW vs 레이크하우스 | 정형 데이터 중심, SQL·BI가 주 사용처면 클라우드 DW | 반정형·대용량 파일·ML이 함께면 레이크하우스 |
| 플랫폼 선택 | 그룹 클라우드 표준·계약이 이미 있으면 그 생태계 우선 | 표준이 없으면 대표 쿼리·적재로 PoC 후 결정 (Day 28 ADR) |
| 이관 방식 | 원천·리포트가 적으면 일괄 이관 + 병행 운영 짧게 | 리포트가 많으면 업무 단위 단계 이관, 구·신 숫자 병행 비교 기간 확보 |
| 저장 프로시저 | 로직이 단순하면 SQL·dbt 모델로 재작성 | 복잡한 PL/SQL은 먼저 업무 규칙을 문서화한 뒤 재작성 (그대로 번역하지 않음) |
| 행 단위 갱신 | 갱신이 적으면 MERGE | 갱신이 잦으면 파티션 단위 교체(덮어쓰기)로 설계 |

## 흔한 실수 3가지

1. **"문법만 바꾸면 된다"는 실수.** '' 와 NULL, DATE의 시각, 정수 나눗셈은 에러 없이 숫자만 바꿉니다. 이관 테스트는 SQL 실행 성공이 아니라 대사 결과로 판정합니다.
2. **온프레미스 습관대로 쿼리하는 실수.** `SELECT *`, 파티션 키 가공, 매번 상세 집계는 클라우드에서 그대로 비용이 됩니다. 필요한 컬럼만, 프루닝되게, 반복 집계는 미리.
3. **시퀀스·IDENTITY를 잊는 실수.** 데이터는 옮겼는데 채번기가 1에서 시작합니다. 이관 체크리스트에 넣고 리허설에서 신규 INSERT까지 해 봅니다.

## 셀프 체크 질문

**Q1. 컬럼 저장이 DW에 유리한 이유와 약점은 무엇입니까?**

:::answer 모범 답안 보기
DW 쿼리는 많은 행에서 적은 컬럼을 집계합니다. 컬럼 저장은 필요한 컬럼만 읽고, 같은 컬럼 값이 비슷해 압축이 잘 되어 읽는 양이 크게 줄어듭니다. 약점은 한 행 단위의 잦은 수정·삭제와 한 행 전체 조회입니다. 여러 컬럼 덩어리를 건드려야 하기 때문입니다. 그래서 적재는 묶어서(배치·파티션 단위), 갱신은 바뀐 행만 모아서 하도록 설계합니다.
:::

**Q2. 스토리지-컴퓨트 분리는 운영 설계를 어떻게 바꿉니까?**

:::answer 모범 답안 보기
연산을 용도별로 나눌 수 있게 됩니다. 야간 적재용 연산과 아침 BI 조회용 연산을 분리하면 서로 자원을 다투지 않고, 월말 마감처럼 바쁜 때만 연산을 키웠다가 줄일 수 있습니다. 대신 비용이 사용량 기반이 되어, 비효율 쿼리·불필요한 새로 고침이 바로 비용이 됩니다. 그래서 연산 자원별 비용 모니터링, 자동 중지, 쿼리 표준(프루닝, 필요한 컬럼만)이 운영 설계에 들어갑니다.
:::

**Q3. Oracle에서 클라우드 DW로 옮길 때 데이터 의미가 바뀌는 지점을 세 가지 이상 들고 대응을 말해 보세요.**

:::answer 모범 답안 보기
첫째, Oracle은 빈 문자열을 NULL로 저장하지만 이관 대상은 대개 둘을 구분합니다. 적재 시 NULLIF(TRIM)로 통일하고 '' 0건을 품질 규칙으로 점검합니다. 둘째, Oracle DATE는 시각을 가집니다. 컬럼별로 시각이 실제로 있는지 프로파일링해 DATE/TIMESTAMP를 정하고, 일시 조건은 반열림 범위로 씁니다. 셋째, NUMBER를 정수형이나 소수 0자리로 옮기면 나눗셈·금액 결과가 달라지므로(정수 나눗셈 여부도 DBMS마다 다름) 금액·비율 컬럼의 정밀도를 명시합니다. 넷째, 문자열 결합의 NULL 처리가 DBMS마다 달라(CONCAT 포함) COALESCE로 명시합니다. 다섯째, 시퀀스는 이관 후 재설정합니다. 검증은 테이블별 건수·합계·해시와 주요 리포트 숫자 비교로 합니다.
:::

## 오늘의 과제

**과제 1.** 이관 품질 규칙을 SQL로 작성하세요. lab.mig_cust에 (1) 빈 문자열이거나 공백만 있는 사업자번호 건수, (2) 앞뒤 공백이 남은 거래처명 건수를 1행으로 보여 줍니다. 결과 모양은 `empty_biz_reg_cnt, untrimmed_nm_cnt` 이며 둘 다 0입니다.

:::answer 해설 보기
정제 규칙을 적재 SQL에 넣었더라도 품질 규칙으로 따로 점검합니다. 다른 경로(수기 보정, 다른 적재 작업)로 들어온 값까지 잡기 위해서입니다.

```sql
SELECT COUNT(*) FILTER (WHERE biz_reg_no IS NOT NULL AND TRIM(biz_reg_no) = '') AS empty_biz_reg_cnt,
       COUNT(*) FILTER (WHERE cust_nm <> TRIM(cust_nm))                         AS untrimmed_nm_cnt
  FROM lab.mig_cust;
```

이 규칙을 Day 12의 품질 규칙 목록에 "이관 후 상시 점검"으로 등록합니다.
:::

**과제 2.** 원천 DATE 컬럼에 시각이 실제로 들어 있는지 프로파일링하는 쿼리를 작성하세요. lab.mig_ord_raw의 ORD_DTM에서 자정이 아닌 값의 건수와 비율을 구합니다. 결과 모양은 `tot_cnt, time_cnt, time_rt` 1행이며 3, 3, 100.0입니다.

:::answer 해설 보기
날짜 부분으로 자른 값과 원래 값이 다르면 시각이 있는 것입니다. 이 비율이 0이면 대상에서 DATE로, 0보다 크면 TIMESTAMP로 두고, 업무 의미(주문 "일자"인가 "일시"인가)를 현업과 확인합니다.

```sql
SELECT COUNT(*) AS tot_cnt,
       COUNT(*) FILTER (WHERE ord_dtm <> DATE_TRUNC('day', ord_dtm)) AS time_cnt,
       ROUND(100.0 * COUNT(*) FILTER (WHERE ord_dtm <> DATE_TRUNC('day', ord_dtm)) / COUNT(*), 1) AS time_rt
  FROM lab.mig_ord_raw;
```

Oracle 원천에서는 `ord_dt <> TRUNC(ord_dt)`로 같은 점검을 합니다. 이관 대상 컬럼의 타입은 이 프로파일링 결과를 근거로 매핑정의서에 적습니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 이관 계획서 | 범위·순서(일괄/단계), 병행 운영 기간, 리허설 횟수, 전환·복귀(rollback) 기준 |
| 타입 매핑표 | Oracle 타입 → 대상 타입, 컬럼별 예외(시각 있는 DATE, 정밀도 없는 NUMBER), 근거가 된 프로파일링 결과 |
| 매핑정의서 | 정제 규칙(NULLIF·TRIM), 시퀀스 처리, 문자셋·콜레이션 |
| 이관 검증서 | 테이블별 건수·합계·해시 대사 결과, 주요 리포트 숫자 비교 |
| 아키텍처 정의서 | 저장·연산 구성(적재용/BI용 분리), 비용 모니터링, 거버넌스 위치 (Day 28) |

## 참고할 원전

- Snowflake, Databricks, Google BigQuery, Amazon Redshift 각 공식 문서 — 아키텍처 개요(저장·연산 구조).
- Delta Lake, Apache Iceberg 공식 문서 — 오픈 테이블 포맷.
- Oracle Database SQL Language Reference — Nulls(빈 문자열 처리), Datetime 데이터 타입, CREATE SEQUENCE.
- PostgreSQL 공식 문서 — 문자열 함수(CONCAT), 날짜·시간 타입, IDENTITY 컬럼.
