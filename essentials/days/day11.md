# Day 11. 메타데이터와 리니지

## 오늘의 한 줄

메타데이터는 "이 데이터가 무엇이고(비즈니스), 어떻게 생겼고(기술), 지금 어떤 상태인가(운영)"를 적은 데이터이고, 리니지는 그 데이터가 **어디서 와서 어디로 가는지**의 지도입니다. 둘이 있어야 "이 컬럼을 바꾸면 무엇이 깨지는가"에 답할 수 있습니다.

## 왜 중요한가

ERP 운영팀이 "주문상세 단가(TB_ORD_DTL.UPRC)를 소수 둘째 자리까지 받도록 NUMERIC(15,2)로 바꾸겠다"고 통보합니다. DW 적재 매핑, 주문라인 팩트, 월 매출 마트, Power BI 측정값 중 어디가 영향을 받는지 아무도 목록을 갖고 있지 않으면, 변경 다음 날 아침 정 과장의 대시보드에서 매출이 원 단위 반올림 차이로 전표와 맞지 않는 것을 보고서야 알게 됩니다. 메타데이터와 리니지는 사고가 난 뒤가 아니라 **변경 전에** 답하기 위한 장치입니다.

## 핵심 개념

### 1. 메타데이터의 세 종류

| 종류 | 질문 | 예 (TB_ORD_DTL.ORD_AMT) | 누가 채우나 |
|---|---|---|---|
| 비즈니스 | 무슨 뜻인가, 누구 책임인가 | "주문수량 × 단가, 원 단위, 부가세 제외", 오너 영업기획팀 | 현업·스튜어드 (사람이 써야 함) |
| 기술 | 어떻게 생겼나 | NUMERIC(15), NOT NULL, PK (ORD_NO, ORD_SEQ) | DB 카탈로그에서 자동 수집 |
| 운영 | 지금 어떤 상태인가 | 마지막 적재 2026-04-04 06:10, 8건, 성공 | 배치·오케스트레이터가 자동 기록 |

기술·운영 메타데이터는 자동으로 모입니다. 어려운 것은 **비즈니스 메타데이터**입니다. "주문금액에 부가세가 포함되는가"는 DB 어디에도 없고 사람만 압니다. Day 10의 표준용어사전이 비즈니스 메타데이터의 뼈대가 되는 이유입니다. 용어 정의를 한 번 써 두면 그 용어를 쓰는 모든 컬럼이 정의를 물려받습니다.

### 2. 데이터 카탈로그: 찾고, 이해하고, 믿게 하는 곳

카탈로그는 세 종류의 메타데이터를 한 화면에 모아 "거래처별 매출은 어느 테이블을 보나요?(검색) 언제 적재됐나요?(운영) 오너는 누구인가요?(거버넌스, Day 13)"에 답하는 도구입니다.

시작은 거창하지 않아도 됩니다. 테이블·컬럼 **COMMENT**를 DB에 넣는 것만으로 기술 메타데이터 옆에 비즈니스 설명이 붙고, 대부분의 카탈로그 도구와 BI 도구가 이를 읽어 갑니다. 전용 도구(오픈소스·상용 카탈로그)는 수집 대상이 여러 DB·BI·파이프라인으로 늘어날 때 검토합니다.

### 3. 리니지: 테이블 단위와 컬럼 단위

테이블 단위 리니지는 "TB_ORD_DTL → STG_ORD_DTL → FCT_ORD_LINE"처럼 테이블 사이 화살표입니다. dbt를 써 보셨다면 docs의 모델 그래프가 이 수준입니다. 영향도 분석에는 부족합니다. FCT_ORD_LINE이 TB_ORD_DTL에서 온다는 것은 알아도, **UPRC를 바꿨을 때 FCT_ORD_LINE의 어느 컬럼이 영향받는지**는 모릅니다.

컬럼 단위 리니지는 (원천 테이블.컬럼) → (대상 테이블.컬럼) + **변환 규칙**을 남깁니다. 변환 규칙이 핵심입니다. "그대로 복사"와 "SUM 집계", "단가 × 수량 계산"은 원천 타입이 바뀔 때 받는 영향이 다릅니다.

리니지를 모으는 방법은 세 가지입니다. SQL·ETL 코드를 파싱해 자동 추출하거나, 매핑정의서를 구조화된 표로 관리해 그대로 리니지로 쓰거나, 파이프라인이 실행될 때 리니지 이벤트를 내보내게 합니다(OpenLineage 같은 공개 표준이 있습니다). SI 프로젝트에서 가장 현실적인 출발점은 **매핑정의서를 엑셀이 아니라 테이블로** 관리하는 것입니다.

### 4. 영향도 분석: 하류와 상류

- **하류(정방향) 영향도**: "이 컬럼을 바꾸면 무엇이 깨지나?"
- **상류(역방향) 추적**: "이 대시보드 숫자는 어디서 왔나?"

DB 안의 의존 관계(뷰, 제약, 프로시저)는 카탈로그로 정확히 찾을 수 있습니다. DB 밖(ETL 스크립트, 다른 DB의 적재 대상, BI 계산식, 엑셀)은 리니지 저장소가 없으면 찾을 방법이 사람의 기억뿐입니다. 영향도 분석은 **두 가지를 합쳐야** 완성됩니다.

## 예시

### 비즈니스 메타데이터를 DB에 붙이기

운영계를 건드리지 않도록 주문상세를 `lab`에 복사하고, 그 위에 Week 1에서 쓴 것 같은 점검·집계 뷰 두 개를 만듭니다.

```sql
CREATE SCHEMA IF NOT EXISTS lab;
CREATE TABLE lab.tb_ord_dtl (LIKE erp.tb_ord_dtl INCLUDING ALL);
INSERT INTO lab.tb_ord_dtl SELECT * FROM erp.tb_ord_dtl;

COMMENT ON TABLE  lab.tb_ord_dtl         IS '주문상세. 오너: 한빛제약 영업기획팀';
COMMENT ON COLUMN lab.tb_ord_dtl.uprc    IS '단가. 주문 시점 적용 단가(원). 기준가와 다를 수 있음(할인)';
COMMENT ON COLUMN lab.tb_ord_dtl.ord_amt IS '주문금액 = 주문수량 × 단가. 원 단위, 부가세 제외';

CREATE VIEW lab.vw_ord_amt_chk AS               -- 금액 정합성 점검 (Day 5)
SELECT ord_no, ord_seq, ord_qty * uprc AS calc_amt, ord_amt, ord_qty * uprc - ord_amt AS diff_amt
  FROM lab.tb_ord_dtl;
CREATE VIEW lab.vw_item_sales AS                -- 품목별 주문금액
SELECT item_cd, SUM(ord_amt) AS ord_amt, MAX(uprc) AS max_uprc
  FROM lab.tb_ord_dtl
 GROUP BY item_cd;

-- 카탈로그 화면처럼: 기술 메타데이터 + 비즈니스 설명
SELECT c.column_name, c.data_type, c.numeric_precision, c.numeric_scale, c.is_nullable,
       col_description('lab.tb_ord_dtl'::regclass, c.ordinal_position::int) AS col_desc
  FROM information_schema.columns c
 WHERE c.table_schema = 'lab' AND c.table_name = 'tb_ord_dtl'
 ORDER BY c.ordinal_position;
```

:::note Oracle 차이
`COMMENT ON TABLE/COLUMN` 문법은 Oracle도 같습니다. 조회는 `ALL_TAB_COMMENTS`, `ALL_COL_COMMENTS`, 컬럼 정보는 `ALL_TAB_COLUMNS`를 씁니다.
:::

6개 컬럼 중 둘에만 설명이 있습니다. 설명이 빈 컬럼 비율이 곧 메타데이터 품질 지표입니다. 표준용어사전(Day 10)이 있다면 컬럼명으로 용어 정의를 찾아 COMMENT를 자동으로 채울 수 있습니다.

### 영향도 분석 1단계: DB 안에서 찾기

UPRC를 NUMERIC(15,2)로 바꾸면 어디에 영향이 있는지 카탈로그로 찾습니다.

```sql
-- (1) 같은 이름의 컬럼: 같은 의미일 가능성이 높은 곳 (운영계·실습 스키마)
SELECT table_schema, table_name, column_name, numeric_precision, numeric_scale
  FROM information_schema.columns
 WHERE column_name = 'uprc' AND table_schema IN ('erp', 'lab')
 ORDER BY 1, 2;

-- (2) 이 컬럼을 직접 쓰는 뷰
SELECT view_schema, view_name, table_name, column_name
  FROM information_schema.view_column_usage
 WHERE table_schema = 'lab' AND table_name = 'tb_ord_dtl' AND column_name = 'uprc'
 ORDER BY view_name;

-- (3) 그 테이블을 FK로 참조하는 테이블 (키 컬럼 변경일 때 중요)
SELECT c.conrelid::regclass AS child_tbl, c.conname
  FROM pg_constraint c
 WHERE c.contype = 'f' AND c.confrelid = 'erp.tb_ord_dtl'::regclass;
```

(1)은 운영계에 UPRC가 세 곳(TB_ORD_DTL, TB_PO_DTL, TB_ITEM_UPRC_HIST) 있다고 알려 줍니다. 모두 단가N15 도메인(Day 10)이므로 **주문상세만 바꾸면 도메인이 깨집니다.** 단가 도메인을 바꿀지, 주문상세만 예외로 할지가 사실은 먼저 내려야 할 결정입니다. (2)는 두 뷰를 모두 찾습니다. (3)은 출고상세(TB_SHIP_DTL)가 주문상세를 참조한다고 알려 줍니다. UPRC는 키가 아니라 이번엔 영향이 없지만, 키 컬럼 길이를 바꾸는 요청이라면 자식 테이블까지 같이 바꿔야 합니다.

PostgreSQL은 뷰가 쓰는 컬럼의 타입 변경을 거부합니다. 의존 관계를 DB가 알고 있다는 뜻입니다.

```sql 의도된 오류 — 뷰가 쓰는 컬럼은 타입을 바꿀 수 없음
ALTER TABLE lab.tb_ord_dtl ALTER COLUMN uprc TYPE NUMERIC(15,2);
```

:::note Oracle 차이
Oracle은 타입 변경을 허용하고 의존 뷰를 INVALID 상태로 바꿉니다(다음 사용 때 재컴파일). 오류가 나지 않으니 오히려 영향을 놓치기 쉽습니다. 의존 객체는 `ALL_DEPENDENCIES`로 찾되, 이 뷰는 객체 단위라 어느 컬럼을 쓰는지까지는 알려 주지 않습니다.
:::

### 영향도 분석 2단계: DB 밖은 리니지 저장소로

DW 적재, 마트, BI는 다른 DB·도구에 있어 카탈로그로는 보이지 않습니다. 매핑정의서를 컬럼 리니지 테이블로 관리합니다. 대상 테이블 이름은 Week 3에서 만들 DW 테이블(주문라인 팩트 FCT_ORD_LINE)과 Week 4의 마트·BI를 가정한 것이며, 여기서는 이름(문자열)만 씁니다.

```sql
CREATE TABLE lab.tb_col_lineage (               -- 컬럼 리니지 (매핑정의서를 구조화)
  lineage_seq  INTEGER      GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  src_obj_nm   VARCHAR(100) NOT NULL,           -- 원천 테이블(또는 BI 데이터셋)
  src_col_nm   VARCHAR(100) NOT NULL,
  tgt_obj_nm   VARCHAR(100) NOT NULL,
  tgt_col_nm   VARCHAR(100) NOT NULL,
  xform_tp_cd  VARCHAR(10)  NOT NULL,           -- COPY 그대로, CALC 계산, AGG 집계
  xform_rule   VARCHAR(300) NOT NULL,
  UNIQUE (src_obj_nm, src_col_nm, tgt_obj_nm, tgt_col_nm)
);
INSERT INTO lab.tb_col_lineage (src_obj_nm, src_col_nm, tgt_obj_nm, tgt_col_nm, xform_tp_cd, xform_rule) VALUES
 ('erp.tb_ord_dtl', 'uprc',    'stg.stg_ord_dtl', 'uprc',    'COPY', '그대로'),
 ('erp.tb_ord_dtl', 'ord_amt', 'stg.stg_ord_dtl', 'ord_amt', 'COPY', '그대로'),
 ('stg.stg_ord_dtl', 'uprc',    'dw.fct_ord_line', 'uprc',    'COPY', '그대로'),
 ('stg.stg_ord_dtl', 'ord_amt', 'dw.fct_ord_line', 'ord_amt', 'COPY', '그대로'),
 ('stg.stg_ord_dtl', 'uprc',    'dw.fct_ord_line', 'disc_amt', 'CALC', '(기준가 - 단가) × 수량'),
 ('dw.fct_ord_line', 'ord_amt', 'dm.dm_sales_mon', 'sales_amt', 'AGG', '월·거래처·품목별 SUM, 취소 제외'),
 ('dw.fct_ord_line', 'disc_amt', 'dm.dm_sales_mon', 'disc_amt', 'AGG', '월·거래처·품목별 SUM'),
 ('dm.dm_sales_mon', 'sales_amt', 'pbi.영업실적', '[매출금액]', 'AGG', 'SUM(sales_amt)'),
 ('dm.dm_sales_mon', 'disc_amt',  'pbi.영업실적', '[할인율]',   'CALC', 'DIVIDE(SUM(disc_amt), SUM(sales_amt) + SUM(disc_amt))');

-- 하류 영향도: erp.tb_ord_dtl.uprc 에서 출발해 끝까지
WITH RECURSIVE down AS (
  SELECT 1 AS lvl, src_obj_nm, src_col_nm, tgt_obj_nm, tgt_col_nm, xform_tp_cd, xform_rule
    FROM lab.tb_col_lineage
   WHERE src_obj_nm = 'erp.tb_ord_dtl' AND src_col_nm = 'uprc'
  UNION ALL
  SELECT d.lvl + 1, l.src_obj_nm, l.src_col_nm, l.tgt_obj_nm, l.tgt_col_nm, l.xform_tp_cd, l.xform_rule
    FROM down d
    JOIN lab.tb_col_lineage l ON l.src_obj_nm = d.tgt_obj_nm AND l.src_col_nm = d.tgt_col_nm
   WHERE d.lvl < 10
)
SELECT lvl, tgt_obj_nm || '.' || tgt_col_nm AS impacted, xform_tp_cd, xform_rule
  FROM down
 ORDER BY lvl, impacted;
```

| lvl | impacted | xform_tp_cd | 확인할 것 |
|---|---|---|---|
| 1 | stg.stg_ord_dtl.uprc | COPY | 스테이징 타입도 NUMERIC(15,2)로 |
| 2 | dw.fct_ord_line.disc_amt | CALC | 할인금액 계산 결과에 소수가 생김. 반올림 규칙 결정 |
| 2 | dw.fct_ord_line.uprc | COPY | 팩트 타입 변경 |
| 3 | dm.dm_sales_mon.disc_amt | AGG | 집계 결과가 원 단위 전표와 대사될 때 차이 |
| 4 | pbi.영업실적.[할인율] | CALC | 표시 형식, 과거 값과의 비교 |

이 목록은 DB 카탈로그로는 1단계부터 보이지 않습니다(다른 DB·도구이므로). 반대로 [매출금액]은 목록에 없습니다. 매출금액은 ORD_AMT에서 오고, ORD_AMT는 원천에서 이미 계산돼 들어오므로 UPRC 타입 변경의 **직접** 영향은 없습니다. 다만 원천에서 ORD_AMT 계산 규칙(반올림)이 함께 바뀌는지는 ERP 운영팀에 물어야 합니다. 리니지는 "어디를 볼지"를 알려 주지, 판단까지 대신해 주지는 않습니다.

상류 추적은 방향만 바꾸면 됩니다.

```sql
-- 상류 추적: Power BI [매출금액]은 어디서 왔나
WITH RECURSIVE up AS (
  SELECT 1 AS lvl, src_obj_nm, src_col_nm, tgt_obj_nm, tgt_col_nm
    FROM lab.tb_col_lineage
   WHERE tgt_obj_nm = 'pbi.영업실적' AND tgt_col_nm = '[매출금액]'
  UNION ALL
  SELECT u.lvl + 1, l.src_obj_nm, l.src_col_nm, l.tgt_obj_nm, l.tgt_col_nm
    FROM up u
    JOIN lab.tb_col_lineage l ON l.tgt_obj_nm = u.src_obj_nm AND l.tgt_col_nm = u.src_col_nm
   WHERE u.lvl < 10
)
SELECT lvl, src_obj_nm || '.' || src_col_nm AS source FROM up ORDER BY lvl;
```

마트 → 팩트 → 스테이징 → erp.tb_ord_dtl.ord_amt의 4단계가 나옵니다. "대시보드 매출이 이상하다"는 문의를 받으면 이 경로를 따라 단계별 합계를 비교하는 것이 Day 12의 대사(Reconciliation)입니다.

### 운영 메타데이터: 적재 이력

```sql
CREATE TABLE lab.tb_load_log (                  -- 적재 이력 (운영 메타데이터)
  batch_id     VARCHAR(30)  NOT NULL,
  tgt_obj_nm   VARCHAR(100) NOT NULL,
  strt_dtm     TIMESTAMP    NOT NULL,
  end_dtm      TIMESTAMP,
  src_cnt      NUMERIC(12),
  tgt_cnt      NUMERIC(12),
  stat_cd      VARCHAR(2)   NOT NULL,           -- 10 실행중, 20 성공, 90 실패
  PRIMARY KEY (batch_id, tgt_obj_nm)
);
INSERT INTO lab.tb_load_log VALUES
 ('B20260403', 'dw.fct_ord_line', TIMESTAMP '2026-04-03 06:00', TIMESTAMP '2026-04-03 06:08', 8, 8, '20'),
 ('B20260404', 'stg.stg_ord_dtl', TIMESTAMP '2026-04-04 06:00', TIMESTAMP '2026-04-04 06:02', 8, 8, '20'),
 ('B20260404', 'dw.fct_ord_line', TIMESTAMP '2026-04-04 06:02', NULL, NULL, NULL, '90');

-- 대상별 마지막 성공 적재 (카탈로그의 "최신성" 표시)
SELECT tgt_obj_nm, MAX(end_dtm) FILTER (WHERE stat_cd = '20') AS last_success_dtm,
       BOOL_OR(stat_cd = '90' AND strt_dtm >= TIMESTAMP '2026-04-04') AS failed_today
  FROM lab.tb_load_log
 GROUP BY tgt_obj_nm
 ORDER BY tgt_obj_nm;
```

4월 4일 팩트 적재가 실패해서 FCT_ORD_LINE의 마지막 성공은 4월 3일입니다. 리니지와 합치면 "오늘 대시보드의 [매출금액]은 하루 전 데이터"라고 사용자에게 알려 줄 수 있습니다. 운영 메타데이터가 리니지를 만나 **신뢰도 정보**가 되는 순간입니다.

## Before / After

**Before: 메타데이터가 사람과 엑셀에 흩어진 상태**

| 질문 | 답하는 방법 |
|---|---|
| ORD_AMT에 부가세 포함? | 영업기획팀 정 과장에게 메신저 |
| UPRC 바꾸면 어디 영향? | 개발자 기억 + 소스 전체 텍스트 검색 |
| 대시보드 숫자 출처? | 매핑정의서 엑셀 최신본이 어느 것인지부터 찾기 |
| 오늘 데이터 최신인가? | 배치 담당자에게 확인 |

**After: 세 메타데이터를 연결**

| 질문 | 답하는 곳 |
|---|---|
| 뜻·오너 | 표준용어사전 → 컬럼 COMMENT → 카탈로그 |
| DB 안 영향 | information_schema·pg_catalog 질의 (뷰·FK·같은 이름 컬럼) |
| DB 밖 영향·출처 | 컬럼 리니지 테이블 (매핑정의서 = 리니지 원천), 재귀 질의 |
| 최신성 | 적재 이력 + 리니지 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 리니지 수준 | 원천 변경이 잦고 하류가 깊으면 컬럼 단위 | 소규모 마트 몇 개면 테이블 단위 + 매핑정의서로 시작 |
| 리니지 수집 | 변환이 SQL로 일관되면 파싱·자동 수집 | 도구·언어가 섞였으면 매핑정의서를 표로 관리하고 배포 때 갱신 강제 |
| 카탈로그 도입 | 사용자가 많고 데이터를 "찾는" 문의가 잦으면 전용 도구 | 초기에는 COMMENT + 용어사전 + 간단한 조회 화면 |
| 비즈니스 메타 작성 | 핵심 지표·마스터는 오너가 직접 정의하고 승인 | 나머지는 표준용어 정의 상속으로 채우고 빈칸을 지표로 관리 |

리니지에서 가장 비싼 것은 수집이 아니라 **최신 유지**입니다. 매핑정의서를 고치지 않고 적재 SQL만 바꾸는 순간 리니지는 거짓말이 됩니다. 그래서 "배포 체크리스트에 리니지 갱신 포함", "리니지 테이블과 실제 적재 SQL을 정기 대조" 같은 절차를 설계 단계에서 함께 정합니다.

## 흔한 실수 3가지

1. **테이블 단위 리니지로 영향도 분석이 된다고 믿는 실수.** 테이블 화살표만으로는 어느 컬럼, 어떤 계산이 영향받는지 모릅니다. 최소한 핵심 지표에 쓰이는 컬럼은 컬럼 단위와 변환 규칙까지 남깁니다.
2. **기술 메타데이터만 모으고 카탈로그라고 부르는 실수.** 타입·길이 목록은 DB가 이미 알고 있습니다. 사용자가 원하는 것은 "무슨 뜻이고 믿어도 되는가"입니다. 비즈니스 정의와 오너, 최신성이 없으면 카탈로그는 쓰이지 않습니다.
3. **DB 카탈로그 검색만으로 영향도 분석을 끝내는 실수.** 뷰와 FK는 찾지만 ETL 스크립트, 다른 DB, BI 계산식은 찾지 못합니다. 영향도 분석서에 "DB 내부 / 리니지 저장소 / 담당자 확인"을 나눠 적습니다.

## 셀프 체크 질문

**Q1. 비즈니스·기술·운영 메타데이터를 그룹 DW 예시로 구분하고, 가장 확보하기 어려운 것을 말해 보세요.**

:::answer 모범 답안 보기
비즈니스 메타데이터는 뜻과 책임입니다. 주문금액은 "수량 × 단가, 원 단위, 부가세 제외"이고 오너는 영업기획팀이라는 것. 기술 메타데이터는 형식입니다. NUMERIC(15), NOT NULL, PK. 운영 메타데이터는 상태입니다. 마지막 적재 일시, 건수, 실패 여부. 기술과 운영은 DB 카탈로그와 배치 로그에서 자동으로 모이지만 비즈니스 메타데이터는 사람이 써야 하므로 가장 어렵습니다. 그래서 표준용어사전의 정의를 컬럼에 상속시키고, 핵심 지표만 오너가 직접 정의·승인하게 하며, 설명이 빈 컬럼 비율을 품질 지표로 관리합니다.
:::

**Q2. ERP 운영팀이 TB_ORD_DTL.UPRC를 NUMERIC(15,2)로 바꾼다고 합니다. 영향도 분석을 어떻게 하시겠습니까?**

:::answer 모범 답안 보기
세 갈래로 봅니다. 첫째, DB 안: information_schema와 pg_catalog로 이 컬럼을 쓰는 뷰·프로시저, 같은 이름의 컬럼(TB_PO_DTL.UPRC, TB_ITEM_UPRC_HIST.UPRC)을 찾습니다. 같은 단가 도메인을 쓰는 컬럼이 셋이므로 주문상세만 바꿀지 단가 도메인 전체를 바꿀지부터 정합니다. 둘째, DB 밖: 컬럼 리니지로 스테이징 → 팩트 → 마트 → BI 측정값까지 하류를 따라가며, 변환 유형별로 영향을 나눕니다. COPY는 타입만 맞추면 되지만 CALC·AGG는 반올림 규칙과 원 단위 전표 대사에 영향이 있습니다. 셋째, 원천 쪽 질문: ORD_AMT 계산 규칙도 바뀌는지, 과거 데이터는 그대로인지 확인합니다. 결과는 영향 객체 목록, 조치, 테스트 방법(변경 전후 합계 대사)을 담은 영향도 분석서로 남깁니다.
:::

**Q3. 리니지를 처음 도입하는 프로젝트입니다. 무엇부터 하시겠습니까?**

:::answer 모범 답안 보기
자동 수집 도구부터 고르지 않고, 이미 만들어야 하는 매핑정의서를 컬럼 단위 표(원천 컬럼, 대상 컬럼, 변환 유형, 규칙)로 구조화하는 것부터 하겠습니다. 매핑정의서는 어차피 산출물이므로 추가 작업이 적고, 그대로 리니지 저장소가 됩니다. 범위는 1차 범위의 핵심 지표(매출금액, 출고수량, 재고수량)에 쓰이는 컬럼부터입니다. 그다음 배포 체크리스트에 매핑정의서 갱신을 넣어 최신성을 지키고, 변환이 SQL로 일관되게 쌓이면 파싱 기반 자동 수집이나 실행 시점 리니지 이벤트로 확장합니다.
:::

## 오늘의 과제

**과제 1.** `erp` 스키마에서 **다른 테이블이 FK로 가장 많이 참조하는 테이블** 순위를 카탈로그로 뽑으세요. 결과 모양은 `parent_tbl, child_cnt, children`입니다. 이 순위가 마스터 변경 영향도의 크기라는 점을 설명해 보세요.

:::answer 해설 보기
pg_constraint의 FK(contype = 'f')를 부모(confrelid) 기준으로 셉니다.

```sql
SELECT c.confrelid::regclass AS parent_tbl,
       COUNT(DISTINCT c.conrelid) AS child_cnt,
       string_agg(DISTINCT c.conrelid::regclass::text, ', ') AS children
  FROM pg_constraint c
  JOIN pg_namespace n ON n.oid = c.connamespace
 WHERE c.contype = 'f' AND n.nspname = 'erp'
 GROUP BY c.confrelid
 ORDER BY child_cnt DESC, c.confrelid::regclass::text;
```

품목(TB_ITEM)이 9개 테이블에서 참조되어 1위이고, 회사·로트가 4개로 뒤를 잇습니다. 품목코드 체계나 길이를 바꾸면 주문·출고·입고·재고·로트·BOM·발주·작업지시가 함께 바뀌어야 한다는 뜻입니다. 마스터의 키 설계(Day 4)가 무거운 이유이자, Day 13 MDM에서 품목 통합을 조심스럽게 다뤄야 하는 이유입니다.
:::

**과제 2.** 위 리니지 테이블에서 "Power BI 측정값마다 최종 원천(erp 컬럼) 목록"을 뽑으세요. 결과 모양은 `measure, erp_source` 입니다.

:::answer 해설 보기
BI 측정값에서 출발하는 상류 재귀를 측정값별로 돌리고, 원천 이름이 `erp.`로 시작하는 행만 남깁니다.

```sql
WITH RECURSIVE up AS (
  SELECT tgt_col_nm AS measure, src_obj_nm, src_col_nm, 1 AS lvl
    FROM lab.tb_col_lineage
   WHERE tgt_obj_nm = 'pbi.영업실적'
  UNION ALL
  SELECT u.measure, l.src_obj_nm, l.src_col_nm, u.lvl + 1
    FROM up u
    JOIN lab.tb_col_lineage l ON l.tgt_obj_nm = u.src_obj_nm AND l.tgt_col_nm = u.src_col_nm
   WHERE u.lvl < 10
)
SELECT DISTINCT measure, src_obj_nm || '.' || src_col_nm AS erp_source
  FROM up
 WHERE src_obj_nm LIKE 'erp.%'
 ORDER BY measure, erp_source;
```

[매출금액]은 ORD_AMT, [할인율]은 UPRC 하나만 나옵니다. 그런데 할인율 계산식에는 SUM(sales_amt)도 쓰이고(→ ORD_AMT), 할인금액 계산에는 기준가(TB_ITEM_UPRC_HIST.UPRC)도 쓰입니다. 변환 규칙 문장에는 적어 놓고 **리니지 행 두 개를 빠뜨린** 것입니다. 규칙 문장과 리니지 행이 일치하는지 대조하는 것도 리니지 검토의 일입니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 매핑정의서 | 원천 테이블·컬럼, 대상 테이블·컬럼, 변환 유형(COPY·CALC·AGG), 변환 규칙. 컬럼 리니지의 원천. |
| 영향도 분석서 | 변경 대상, DB 내부 영향(카탈로그 결과), DB 외부 영향(리니지 결과), 조치, 테스트 방법. |
| 테이블정의서 | 테이블·컬럼 설명(COMMENT로 반영), 오너. |
| 메타데이터 관리 지침 | 메타데이터 항목, 수집 방법(자동·수동), 갱신 책임, 배포 시 리니지 갱신 절차. |

## 참고할 원전

- PostgreSQL 공식 문서 — "The Information Schema", "System Catalogs" (pg_constraint, pg_depend), "COMMENT".
- Oracle Database 공식 문서 — "Database Reference" (ALL_TAB_COLUMNS, ALL_COL_COMMENTS, ALL_DEPENDENCIES).
- DAMA International, "DAMA-DMBOK: Data Management Body of Knowledge", 2nd ed. (Technics Publications, 2017) — Metadata Management 장.
- OpenLineage 프로젝트 문서 (openlineage.io) — 실행 시점 리니지 이벤트 표준.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 관리 체계: 메타데이터 관리.
