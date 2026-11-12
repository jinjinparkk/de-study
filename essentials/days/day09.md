# Day 9. 코드 설계

## 오늘의 한 줄

코드는 업무의 분류 체계를 두세 글자로 줄여 놓은 약속입니다. 코드를 어디에 담을지(공통코드 vs 개별 코드 테이블)보다 중요한 것은 **코드값에 로직을 걸지 않고, 한번 쓴 값의 뜻을 바꾸지 않는 것**입니다.

## 왜 중요한가

주문상태코드에 '25 출고지시'를 새로 넣는 날, `WHERE ORD_STAT_CD < '30'`으로 "미출고 주문"을 뽑던 배치는 우연히 25를 포함하지만, `IN ('10','20')`으로 짜인 다른 화면은 25를 빠뜨립니다. 같은 "미출고 주문"이 화면마다 다른 숫자가 되고, 정 과장은 대시보드를 믿지 않게 됩니다. 코드 하나 추가가 수십 개 프로그램의 영향도 분석이 되는 이유입니다.

## 핵심 개념

### 1. 공통코드 테이블 vs 개별 코드 테이블

공통코드 테이블은 모든 코드를 (코드그룹, 코드값) 두 컬럼으로 한 테이블에 담는 방식입니다. 개별 코드 테이블은 코드 종류마다 테이블을 따로 만듭니다(TB_ORD_STAT, TB_RGN 등).

| 기준 | 공통코드 (TB_CMM_CD) | 개별 코드 테이블 (TB_ORD_STAT) |
|---|---|---|
| 새 코드 종류 추가 | 행 INSERT로 끝 (DDL 없음) | 테이블 생성 필요 |
| FK로 무결성 보장 | 어려움. 자식에 코드그룹 컬럼이 없어 FK를 못 검 | 가능. ORD_STAT_CD → TB_ORD_STAT FK |
| 코드별 고유 속성 | 범용 컬럼(ATTR1~5)에 넣게 되어 의미가 숨음 | 컬럼으로 명시 (종료여부, 단계순서) |
| 관리 화면 | 하나로 전부 관리 | 테이블마다 필요 |
| 조회 | 항상 (그룹, 값) 두 조건으로 조인 | 값 하나로 조인 |

대부분의 SI 프로젝트는 **둘을 섞습니다.** 이름과 정렬 순서만 있는 단순 분류(거래처유형, 단가유형, 입고유형)는 공통코드에, 코드 자체가 업무 속성을 갖거나 무결성이 중요한 것(주문상태의 종료 여부, 지역의 상위 지역, 계정과목)은 개별 테이블에 둡니다.

### 2. 코드 체계 설계 원칙

- **코드값은 문자 타입.** '01'의 앞자리 0을 지키고, 나중에 'A1' 같은 값이 와도 타입을 바꿀 필요가 없게 합니다(Day 8).
- **의미를 많이 담지 않습니다.** FG/RM/PM처럼 짧은 약어는 기억하기 쉬워 좋지만, "앞자리 1은 서울, 2는 경기" 같은 자리별 의미는 조직이 바뀌면 거짓말이 됩니다(Day 4의 스마트 키와 같은 문제).
- **상태코드의 간격(10, 20, 30, 90)은 정렬과 끼워넣기를 위한 것**이지 비교 연산을 위한 것이 아닙니다. 순서가 필요하면 별도 순서 컬럼(SORT_SEQ, STEP_SEQ)을 둡니다.
- **한번 쓴 코드값은 재사용하지 않습니다.** 폐기는 USE_YN = 'N'. 과거 데이터에 남은 '03'의 뜻이 바뀌면 과거 집계가 조용히 틀립니다.
- **"99 기타"를 쉽게 만들지 않습니다.** 기타가 커지면 분류 체계가 실패한 것입니다. 기타 비중을 품질 지표로 봅니다.

### 3. 코드에 로직을 걸지 말고, 속성에 걸기

`ORD_STAT_CD IN ('10','20')`는 "미출고"라는 업무 개념을 코드값 목록으로 하드코딩한 것입니다. 상태가 늘면 모든 하드코딩을 찾아 고쳐야 합니다. 대신 코드 테이블에 "출고완료여부", "매출인식여부" 같은 **속성 컬럼**을 두고 로직은 속성으로 겁니다. 새 상태 25가 생기면 코드 테이블에 한 행을 넣으며 속성값을 정하는 것으로 끝납니다. 개별 코드 테이블이 유리한 가장 큰 이유가 이것입니다.

### 4. 코드 변경의 세 종류와 영향도

| 변경 | 예 | 영향 |
|---|---|---|
| 코드명 변경 | '03 도매상' → '03 의약품도매상' | 화면 표시만. DW 차원 속성은 Type 1 덮어쓰기로 충분 |
| 코드값 추가 | ORD_STAT_CD 25 출고지시, ITEM_TP_CD SF 반제품 (Day 6) | 하드코딩 조건, CASE 문, BI 필터, DW 매핑정의서 |
| 코드 의미 변경·분할 | '01 병원'을 의원/병원/종합병원으로 쪼갬 | 과거 데이터 재분류 필요. 원칙은 새 코드 체계를 만들고 과거는 매핑 |

Day 6에서 품목유형에 SF(반제품)가 추가됐습니다. `ITEM_TP_CD <> 'FG'`를 "원자재"로 쓰던 구매 화면이 있었다면 반제품까지 원자재로 셌을 것입니다. 거래처유형 '01 병원'을 쪼개지 않고 서브타입의 HOSP_TP_CD(01 의원, 02 병원, 03 종합병원)로 하위 분류를 둔 것도, 기존 코드의 의미를 바꾸지 않기 위한 선택이었습니다.

### 5. 계열사마다 다른 코드: 표준코드와 매핑

한빛푸드 ERP는 거래처유형을 'A 대리점, B 할인점'으로 쓰고, 한빛제약은 '01 병원, 02 약국, 03 도매상'을 씁니다. 그룹 DW는 한쪽을 강요하지 않고 **그룹 표준코드**를 정한 뒤 계열사 원천 코드 → 표준코드 **매핑 테이블**을 둡니다. 매핑이 없는 원천 코드가 들어오면 적재를 멈추지 않고 미매핑 목록으로 알립니다(Day 23).

## 예시

### 공통코드 테이블 설계와 등록

| 한글 논리명 (ENGLISH_PHYSICAL) | 타입 | 비고 |
|---|---|---|
| 코드그룹코드 (CD_GRP_CD) | VARCHAR(30) | PK. 그 코드를 쓰는 컬럼의 물리명 그대로 (CUST_TP_CD) |
| 코드 (CD) | VARCHAR(10) | PK |
| 코드명 (CD_NM) | VARCHAR(50) | |
| 정렬순번 (SORT_SEQ) | NUMERIC(4) | 화면·보고서 정렬 |
| 사용여부 (USE_YN) | CHAR(1) | 폐기 코드는 N (삭제 금지) |
| 적용시작일자·적용종료일자 (APLY_STRT_DT, APLY_END_DT) | DATE | Day 7 규칙. 언제부터 쓰는 코드인가 |

코드그룹코드를 **컬럼 물리명과 같게** 짓는 것이 작지만 강력한 규칙입니다. "이 컬럼의 코드 목록은?"이 이름만으로 찾아지고, 다음 절의 자동 점검이 가능해집니다. CMM(공통), GRP(그룹), SORT(정렬)는 표준 약어표에 없으므로 Day 10의 표준단어 신청 대상입니다.

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

CREATE TABLE lab.tb_cmm_cd_grp (               -- 공통코드그룹
  cd_grp_cd   VARCHAR(30) PRIMARY KEY,
  cd_grp_nm   VARCHAR(50) NOT NULL,
  use_yn      CHAR(1)     NOT NULL DEFAULT 'Y' CHECK (use_yn IN ('Y', 'N'))
);
CREATE TABLE lab.tb_cmm_cd (                   -- 공통코드
  cd_grp_cd    VARCHAR(30) NOT NULL REFERENCES lab.tb_cmm_cd_grp (cd_grp_cd),
  cd           VARCHAR(10) NOT NULL,
  cd_nm        VARCHAR(50) NOT NULL,
  sort_seq     NUMERIC(4)  NOT NULL,
  use_yn       CHAR(1)     NOT NULL DEFAULT 'Y' CHECK (use_yn IN ('Y', 'N')),
  aply_strt_dt DATE        NOT NULL DEFAULT DATE '2025-01-01',
  aply_end_dt  DATE        NOT NULL DEFAULT DATE '9999-12-31',
  PRIMARY KEY (cd_grp_cd, cd)
);

INSERT INTO lab.tb_cmm_cd_grp (cd_grp_cd, cd_grp_nm) VALUES
 ('CUST_TP_CD', '거래처유형'), ('ITEM_TP_CD', '품목유형'), ('UPRC_TP_CD', '단가유형'),
 ('RCV_TP_CD', '입고유형'), ('ORD_DTL_TP_CD', '주문상세유형'), ('UNIT_CD', '단위');

INSERT INTO lab.tb_cmm_cd (cd_grp_cd, cd, cd_nm, sort_seq) VALUES
 ('CUST_TP_CD', '01', '병원', 1), ('CUST_TP_CD', '02', '약국', 2), ('CUST_TP_CD', '03', '도매상', 3),
 ('ITEM_TP_CD', 'FG', '완제품', 1), ('ITEM_TP_CD', 'SF', '반제품', 2),
 ('ITEM_TP_CD', 'RM', '원료', 3), ('ITEM_TP_CD', 'PM', '포장재', 4),
 ('UPRC_TP_CD', '01', '기준가', 1), ('UPRC_TP_CD', '02', '보험상한가', 2),
 ('RCV_TP_CD', '01', '구매입고', 1), ('RCV_TP_CD', '02', '생산입고', 2),
 ('ORD_DTL_TP_CD', '01', '일반', 1), ('ORD_DTL_TP_CD', '02', '증정', 2),
 ('UNIT_CD', 'BOX', '박스', 1), ('UNIT_CD', 'EA', '개', 2), ('UNIT_CD', 'KG', '킬로그램', 3);
```

주문상태(ORD_STAT_CD)와 지역(RGN_CD)은 일부러 공통코드에 넣지 않았습니다. 주문상태는 업무 속성이 있어 개별 테이블로 만들고(아래), 지역은 상위 지역을 갖는 계층 코드라 별도 테이블이 어울립니다.

### 운영 데이터 vs 코드 목록 점검

코드그룹코드 = 컬럼명 규칙 덕분에, 운영계 데이터에 쓰인 코드값이 등록돼 있는지 한 쿼리로 볼 수 있습니다. 운영계에 FK가 없는 공통코드의 무결성은 이런 점검으로 지킵니다.

```sql
WITH used AS (
  SELECT 'CUST_TP_CD' AS cd_grp_cd, cust_tp_cd AS cd, COUNT(*) AS row_cnt FROM erp.tb_cust GROUP BY cust_tp_cd
  UNION ALL SELECT 'ITEM_TP_CD', item_tp_cd, COUNT(*) FROM erp.tb_item GROUP BY item_tp_cd
  UNION ALL SELECT 'UNIT_CD', unit_cd, COUNT(*) FROM erp.tb_item GROUP BY unit_cd
  UNION ALL SELECT 'UPRC_TP_CD', uprc_tp_cd, COUNT(*) FROM erp.tb_item_uprc_hist GROUP BY uprc_tp_cd
  UNION ALL SELECT 'RCV_TP_CD', rcv_tp_cd, COUNT(*) FROM erp.tb_rcv GROUP BY rcv_tp_cd
)
SELECT u.cd_grp_cd, u.cd, u.row_cnt,
       CASE WHEN c.cd IS NULL THEN '미등록' WHEN c.use_yn = 'N' THEN '폐기코드 사용' END AS issue
  FROM used u
  LEFT JOIN lab.tb_cmm_cd c ON c.cd_grp_cd = u.cd_grp_cd AND c.cd = u.cd
 WHERE c.cd IS NULL OR c.use_yn = 'N';
```

결과는 `UNIT_CD | ROLL | 1` 한 행입니다. 포장재 M30001의 단위 ROLL을 코드로 등록하지 않았습니다. 이런 누락은 운영 화면에서는 아무 문제가 없다가, DW에서 코드명을 붙이는 순간 단위명이 빈 칸으로 나타납니다. 점검 쿼리를 매일 돌리면 등록 누락을 그날 알 수 있습니다.

```sql
INSERT INTO lab.tb_cmm_cd (cd_grp_cd, cd, cd_nm, sort_seq) VALUES ('UNIT_CD', 'ROLL', '롤', 4);
```

### 공통코드 조인의 함정: 그룹 조건을 빠뜨리면

공통코드는 '01'이 여러 그룹에 있습니다(거래처유형·단가유형·입고유형·주문상세유형). 조인에서 그룹 조건을 빠뜨리면 행이 불어납니다.

```sql
-- 잘못: 그룹 조건 없이 코드값만으로 조인
SELECT COUNT(*) AS wrong_cnt
  FROM erp.tb_cust t
  JOIN lab.tb_cmm_cd c ON c.cd = t.cust_tp_cd;

-- 바름: (그룹, 코드) 두 조건
SELECT t.cust_no, t.cust_nm, t.cust_tp_cd, c.cd_nm AS cust_tp_nm
  FROM erp.tb_cust t
  LEFT JOIN lab.tb_cmm_cd c ON c.cd_grp_cd = 'CUST_TP_CD' AND c.cd = t.cust_tp_cd
 ORDER BY t.cust_no;
```

거래처는 5개인데 잘못된 조인은 17행을 돌려줍니다. '01'·'02'는 네 그룹에 다 있어 병원·약국 4곳이 각각 4배가 되고, '03'은 거래처유형에만 있어 도매상만 1행으로 남기 때문입니다. 일부만 부풀어서 더 찾기 어렵습니다. Day 16에서 다룰 fan-out이 코드 조인 하나로도 생깁니다. 그래서 공통코드를 쓰는 조직은 "코드명 붙이기"를 뷰나 함수 하나로 통일해 그룹 조건 누락을 원천 차단하기도 합니다.

### 주문상태: 개별 코드 테이블 + 속성에 로직 걸기

```sql
CREATE TABLE lab.tb_ord_stat (                 -- 주문상태 (개별 코드 테이블)
  ord_stat_cd  VARCHAR(2)  PRIMARY KEY,
  ord_stat_nm  VARCHAR(30) NOT NULL,
  step_seq     NUMERIC(2)  NOT NULL,           -- 진행 순서 (코드값 비교 대신)
  ship_end_yn  CHAR(1)     NOT NULL CHECK (ship_end_yn IN ('Y', 'N')),  -- 출고 대상에서 끝났나
  sales_yn     CHAR(1)     NOT NULL CHECK (sales_yn IN ('Y', 'N')),     -- 매출 집계 대상인가
  use_yn       CHAR(1)     NOT NULL DEFAULT 'Y'
);
INSERT INTO lab.tb_ord_stat (ord_stat_cd, ord_stat_nm, step_seq, ship_end_yn, sales_yn) VALUES
 ('10', '접수', 1, 'N', 'N'), ('20', '확정', 2, 'N', 'Y'),
 ('30', '출고완료', 4, 'Y', 'Y'), ('90', '취소', 9, 'Y', 'N');

CREATE TABLE lab.tb_ord (LIKE erp.tb_ord INCLUDING ALL);
INSERT INTO lab.tb_ord SELECT * FROM erp.tb_ord;
ALTER TABLE lab.tb_ord
  ADD CONSTRAINT fk_ord_01 FOREIGN KEY (ord_stat_cd) REFERENCES lab.tb_ord_stat (ord_stat_cd);
```

```sql 의도된 오류 — 등록되지 않은 주문상태
INSERT INTO lab.tb_ord (ord_no, ord_dt, cust_no, emp_no, ord_stat_cd)
VALUES ('SO2026040003', DATE '2026-04-05', 'C000201', 'E1002', '99');
```

개별 테이블은 FK로 잘못된 상태를 막습니다. 이제 영향도 분석을 해 봅니다. 기존 프로그램 두 개(뷰로 흉내 냄)가 코드값을 하드코딩하고 있습니다.

```sql
CREATE VIEW lab.vw_ord_unshipped_old AS        -- 미출고 주문 (값 목록 하드코딩)
SELECT ord_no, ord_dt, cust_no FROM lab.tb_ord WHERE ord_stat_cd IN ('10', '20');
CREATE VIEW lab.vw_ord_sales_old AS            -- 매출 집계 대상 (범위 비교 하드코딩)
SELECT ord_no, ord_dt, cust_no FROM lab.tb_ord WHERE ord_stat_cd >= '20' AND ord_stat_cd < '90';
CREATE VIEW lab.vw_ord_unshipped AS            -- 같은 뜻, 속성에 로직
SELECT o.ord_no, o.ord_dt, o.cust_no
  FROM lab.tb_ord o JOIN lab.tb_ord_stat s ON s.ord_stat_cd = o.ord_stat_cd
 WHERE s.ship_end_yn = 'N';

-- 영향도 1단계: ORD_STAT_CD 를 쓰는 뷰 찾기
SELECT viewname FROM pg_views
 WHERE schemaname = 'lab' AND definition ILIKE '%ord_stat_cd%'
 ORDER BY viewname;
```

```sql
-- 상태 추가: 25 출고지시 (확정 다음, 출고완료 전). 시험 후 되돌림
BEGIN;
INSERT INTO lab.tb_ord_stat (ord_stat_cd, ord_stat_nm, step_seq, ship_end_yn, sales_yn)
VALUES ('25', '출고지시', 3, 'N', 'Y');
UPDATE lab.tb_ord SET ord_stat_cd = '25' WHERE ord_no = 'SO2026030004';
SELECT 'old' AS ver, COUNT(*) FROM lab.vw_ord_unshipped_old
UNION ALL
SELECT 'new', COUNT(*) FROM lab.vw_ord_unshipped;
ROLLBACK;
```

카탈로그 검색은 세 뷰를 모두 찾아 줍니다(속성 기반 뷰도 조인 조건에 ORD_STAT_CD가 있으므로). 하지만 **고쳐야 하는 것은 두 개**입니다. SO2026030004를 출고지시로 바꾸면 하드코딩 뷰는 미출고 1건(SO2026040001만), 속성 기반 뷰는 2건(SO2026040001, SO2026030004)을 셉니다. 출고지시는 아직 출고 전이므로 2건이 맞습니다. 매출 집계 뷰는 범위 비교 덕분에 우연히 25를 포함하지만, 다음에 '95 반품'이 생기면 또 틀립니다. 카탈로그 검색은 DB 안의 뷰·프로시저만 찾습니다. 배치 스크립트, BI 계산식, 엑셀 매크로는 Day 11의 리니지·메타데이터 없이는 찾을 수 없습니다.

## Before / After

**Before: 코드는 각자, 로직은 값으로**

| 증상 | 원인 |
|---|---|
| '미출고 주문' 숫자가 화면마다 다름 | 상태 목록을 프로그램마다 하드코딩 |
| 단위명이 빈 칸으로 나오는 품목 | 코드 등록 누락, 점검 없음 |
| 병원·약국만 4배로 나오는 보고서 | 공통코드 조인에서 그룹 조건 누락 |
| 작년 '03' 집계가 올해 다르게 나옴 | 폐기 코드값을 다른 뜻으로 재사용 |

**After: 담는 곳을 기준으로 나누고, 로직은 속성에**

| 항목 | 규칙 |
|---|---|
| 단순 분류 | 공통코드 (CD_GRP_CD = 컬럼 물리명), 사용 데이터 vs 코드 목록 매일 점검 |
| 업무 속성이 있는 코드 | 개별 코드 테이블 + FK (TB_ORD_STAT: STEP_SEQ, SHIP_END_YN, SALES_YN) |
| 로직 | 코드값 목록·범위 비교 금지, 속성 컬럼으로 |
| 변경 | 값 재사용 금지, 폐기는 USE_YN, 의미 분할은 새 코드 + 매핑 |
| 계열사 코드 | 그룹 표준코드 + 원천 코드 매핑 테이블 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 담을 곳 | 코드명·정렬만 있고 자주 늘어나면 공통코드 | 업무 속성·계층·FK 무결성이 필요하면 개별 테이블 |
| 코드값 형태 | 값이 적고 오래 안정적이면 니모닉(FG, RM) | 값이 많거나 늘어날 여지가 크면 의미 없는 일련값(01, 02…) |
| 상태 추가 요청 | 기존 상태로 표현 불가하고 업무 처리가 달라지면 새 상태 | 화면 표시만 다르면 상태가 아니라 하위 속성이나 플래그 |
| 의미를 쪼개야 할 때 | 과거 데이터를 재분류할 근거가 있으면 새 코드 + 과거 매핑 | 근거가 없으면 상위 코드 유지 + 하위 분류 코드 추가 (HOSP_TP_CD처럼) |
| 계열사 간 코드 불일치 | 그룹 지표에 쓰이면 표준코드 + 매핑 테이블 | 계열사 내부 지표면 원천 코드 그대로 두고 차원 속성으로만 보존 |

코드 변경 요청이 오면 시니어는 "추가인가, 이름 변경인가, 의미 변경인가"부터 묻습니다. 셋은 영향 범위가 전혀 다르기 때문입니다.

## 흔한 실수 3가지

1. **코드값 범위 비교로 업무 로직을 짜는 실수.** `< '30'`, `BETWEEN '10' AND '20'`은 코드 간격이 의미를 갖는다는 숨은 가정입니다. 새 값이 그 사이에 들어오는 순간 깨집니다. 순서는 STEP_SEQ, 판정은 속성 컬럼으로 합니다.
2. **범용 속성 컬럼(ATTR1~ATTR5)에 의미를 숨기는 실수.** 공통코드에 "ATTR1 = 매출인식여부" 같은 약속을 두면, 그 약속은 사람 머릿속과 위키에만 남습니다. 속성이 필요해지면 개별 테이블로 승격하는 신호로 봅니다.
3. **폐기 코드를 지우거나 재사용하는 실수.** 코드를 DELETE하면 과거 데이터의 코드명이 사라지고, 재사용하면 과거 집계의 뜻이 바뀝니다. 폐기는 USE_YN = 'N'과 적용종료일자로 합니다.

## 셀프 체크 질문

**Q1. 공통코드 테이블과 개별 코드 테이블 중 무엇을 쓰시겠습니까?**

:::answer 모범 답안 보기
둘 중 하나가 아니라 기준을 정해 섞겠습니다. 코드명과 정렬 순서만 있고 종류가 자주 늘어나는 단순 분류(거래처유형, 단가유형, 입고유형)는 공통코드에 두어 관리 화면 하나로 운영합니다. 대신 FK를 걸 수 없으므로 코드그룹코드를 컬럼 물리명과 같게 짓고, 운영 데이터의 코드값이 등록돼 있는지 매일 점검합니다. 코드 자체가 업무 속성을 갖거나(주문상태의 출고종료·매출인식 여부), 계층이 있거나(지역), 무결성이 중요하면 개별 테이블과 FK를 씁니다. 공통코드의 범용 속성 컬럼에 의미를 넣고 싶어지는 순간이 개별 테이블로 바꿀 신호입니다.
:::

**Q2. 주문상태 '25 출고지시'를 추가해 달라는 요청을 받았습니다. 무엇을 확인하겠습니까?**

:::answer 모범 답안 보기
먼저 정말 새 상태인지 묻습니다. 업무 처리(출고 가능 여부, 매출 인식)가 달라지면 상태이고, 표시만 다르면 플래그로 충분합니다. 상태가 맞다면 영향도를 봅니다. DB 안에서는 카탈로그(뷰·프로시저 정의)에서 ORD_STAT_CD를 쓰는 객체를 찾고, 밖에서는 배치 소스·BI 계산식·DW 매핑정의서를 리니지 메타데이터로 찾습니다. 특히 값 목록(IN)·범위 비교(<, BETWEEN)로 짠 곳은 결과가 조용히 바뀌므로 하나씩 확인합니다. 개별 코드 테이블에 "출고종료여부", "매출대상여부" 같은 속성이 있다면 새 행을 넣고 속성만 정하면 되므로, 이번 기회에 하드코딩을 속성 기반으로 바꾸는 것도 함께 제안합니다.
:::

**Q3. 한빛푸드의 거래처유형 코드가 한빛제약과 다릅니다. 그룹 DW에서는 어떻게 하시겠습니까?**

:::answer 모범 답안 보기
어느 한 계열사 코드를 그룹 기준으로 강요하지 않고, 그룹 경영지원실(마스터 오너)과 그룹 표준 거래처유형을 정합니다. 그다음 (회사코드, 원천 코드그룹, 원천 코드) → 표준코드 매핑 테이블을 두고 DW 적재 때 변환합니다. 원천 코드도 차원에 함께 남겨 계열사 내부 분석이 가능하게 하고, 매핑이 없는 새 원천 코드가 들어오면 적재를 멈추지 않고 미매핑으로 표시한 뒤 담당 스튜어드에게 알립니다. 매핑 자체도 바뀔 수 있으므로 적용 기간을 둡니다.
:::

## 오늘의 과제

**과제 1.** 주문 목록을 코드명과 함께 보여 주는 쿼리를 작성하세요. 결과 모양은 `ord_no, cust_nm, cust_tp_nm, ord_stat_nm` 6행입니다. 거래처유형명은 공통코드에서, 주문상태명은 개별 코드 테이블에서 가져옵니다.

:::answer 해설 보기
공통코드는 그룹 조건을 조인 조건에 함께 넣고, 코드 등록 누락이 있어도 주문이 사라지지 않도록 LEFT JOIN을 씁니다.

```sql
SELECT o.ord_no, t.cust_nm, c.cd_nm AS cust_tp_nm, s.ord_stat_nm
  FROM lab.tb_ord o
  JOIN erp.tb_cust t ON t.cust_no = o.cust_no
  LEFT JOIN lab.tb_cmm_cd c ON c.cd_grp_cd = 'CUST_TP_CD' AND c.cd = t.cust_tp_cd
  LEFT JOIN lab.tb_ord_stat s ON s.ord_stat_cd = o.ord_stat_cd
 ORDER BY o.ord_no;
```

6행이 나오면 정답입니다. INNER JOIN으로 쓰면 코드가 빠진 주문이 목록에서 사라지는데, 이는 코드 문제를 매출 누락으로 바꾸는 셈입니다.
:::

**과제 2.** 매출 집계 대상 주문 수를 하드코딩 뷰(`vw_ord_sales_old`)와 같은 결과가 나오도록 속성 기반으로 다시 쓰세요. 결과 모양은 `ver, ord_cnt` 2행이고 두 값이 같아야 합니다.

:::answer 해설 보기
SALES_YN = 'Y'인 상태(20 확정, 30 출고완료)만 셉니다. 이제 '95 반품'이 생겨도 SALES_YN만 정하면 되고 쿼리는 그대로입니다.

```sql
SELECT 'old' AS ver, COUNT(*) AS ord_cnt FROM lab.vw_ord_sales_old
UNION ALL
SELECT 'new', COUNT(*)
  FROM lab.tb_ord o JOIN lab.tb_ord_stat s ON s.ord_stat_cd = o.ord_stat_cd
 WHERE s.sales_yn = 'Y';
```

두 값 모두 4건(SO2026030001~0004)입니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 코드정의서 (표준코드 목록) | 코드그룹, 코드값, 코드명, 정렬순번, 사용여부, 적용기간, 코드 오너. 업무 속성이 있는 코드는 속성의 뜻. |
| 테이블정의서 | 코드 컬럼마다 참조 코드그룹(공통코드) 또는 FK 대상 테이블(개별 코드). |
| 코드 매핑정의서 (DW) | 회사코드 + 원천 코드 → 그룹 표준코드, 미매핑 처리 규칙, 적용기간. |
| 변경요청서·영향도 분석서 | 변경 종류(명칭·추가·의미), 영향 객체 목록(뷰·배치·BI·매핑), 과거 데이터 처리 방안. |
| 품질 점검 목록 | 미등록 코드 사용, 폐기 코드 사용, 기타 코드 비중 점검 쿼리. |

## 참고할 원전

- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드"(DAP·DAsP 공통 교재) — 데이터 표준화 과목: 표준 코드.
- DAMA International, "DAMA-DMBOK: Data Management Body of Knowledge", 2nd ed. (Technics Publications, 2017) — Reference and Master Data 장 (참조 데이터와 코드값 관리).
