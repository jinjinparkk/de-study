# Day 13. 데이터 거버넌스와 MDM

## 오늘의 한 줄

데이터 거버넌스는 "이 데이터는 누가 정의하고, 누가 고치고, 누가 책임지는가"를 정해 두는 일이고, MDM(마스터 데이터 관리)은 그 결정을 거래처·품목·로트 같은 **모든 업무가 함께 쓰는 기준 데이터**에 적용하는 일입니다. 기술보다 역할과 규칙이 먼저입니다.

## 왜 중요한가

바른팜유통은 한빛제약 C000301, 한빛푸드 F-0091 "(주)바른팜유통", 한빛로지스 L-0077 "바른팜 유통"으로 따로 등록돼 있어, 그룹 거래처별 매출 순위에서 세 줄로 나뉘어 실제보다 낮게 나옵니다. 로트 마스터도 같습니다. 유효기한이 잘못 등록된 로트 하나가 있으면 FEFO 출고가 엉뚱한 로트를 먼저 내보내고, 회수(리콜)가 필요할 때 어느 약국으로 갔는지 추적이 끊깁니다.

## 핵심 개념

### 1. 거버넌스의 역할: 결정권과 책임을 나눕니다

| 역할 | 하는 일 | 한빛제약그룹에서 |
|---|---|---|
| 데이터 오너 | 정의·품질 기준·접근 권한을 결정하고 책임진다 | 그룹 거래처: 그룹 경영지원실, 영업 지표: 한빛제약 영업기획팀, 로트: 한빛케미칼 품질보증(QA) |
| 데이터 스튜어드 | 매일의 품질을 관리한다. 중복 검토, 코드 등록, 규칙 위반 조치 | 계열사별 마스터 담당자 (한빛로지스 한 대리 등) |
| 데이터 관리자 (커스터디언) | 저장·백업·권한을 기술적으로 운영한다 | 한빛정보기술 ERP 운영팀 |
| 데이터 아키텍트 | 구조·표준·통합 방식을 설계한다 | 나 (그룹 DW PL) |
| 데이터 거버넌스 협의체 | 계열사 간 충돌을 조정하고 표준을 승인한다 | 경영지원실 주관, 계열사 오너 참여 |

핵심은 **아키텍트가 오너가 아니라는 것**입니다. 공식 상호, 임박 재고 기준은 아키텍트가 정하지 않습니다. 누가 정해야 하는지 묻고, 그 결정을 구조와 점검 규칙으로 옮깁니다. Day 10의 표준 심의, Day 12의 품질 규칙 등급이 모두 오너 승인을 거쳐야 하는 이유입니다.

### 2. 마스터 데이터와 참조 데이터

마스터 데이터는 거래가 참조하는 업무 핵심 대상(거래처, 품목, 사원, 창고), 참조 데이터는 분류 값 목록(코드, 단위, 지역)입니다. 로트는 생산 때마다 생기지만 생긴 뒤에는 출고·재고·품질·회수가 모두 참조하고 유효기한이라는 품질 속성을 가지므로, 제약 그룹에서는 **품질보증이 오너인 마스터 데이터**로 다룹니다.

### 3. MDM 방식: 어디에 골든 레코드를 두나

| 방식 | 골든 레코드 위치 | 원천 시스템 | 어울리는 때 |
|---|---|---|---|
| 레지스트리 | 원천을 가리키는 교차참조만 | 그대로 | "같은 대상" 연결만 필요할 때 |
| 통합 (Consolidation) | DW·MDM 허브에 골든 레코드를 만듦 | 그대로 | 분석·보고용 통합이 목표일 때 |
| 공존 (Coexistence) | 허브와 원천 모두, 허브가 원천에 되돌려 보냄 | 허브 값으로 갱신 | 원천 품질도 개선해야 할 때 |
| 중앙집중 | 허브에서만 생성·수정 | 허브에서 받아 씀 | 그룹 공통 마스터를 한 곳에서 운영할 때 |

그룹 DW 1차 범위는 **통합 방식**으로 시작하는 것이 현실적입니다. 계열사 ERP를 바꾸지 않고 DW에서 매칭·골든 레코드·교차참조를 만들고, 공존·중앙집중으로의 전환은 협의체 결정으로 남깁니다.

### 4. 매칭과 생존 규칙(Survivorship)

매칭은 "같은 대상인가"의 판단, 생존 규칙은 묶인 레코드의 속성 중 **어느 값을 골든 레코드에 남길지**의 규칙입니다.

- **매칭 키**: 거래처는 사업자등록번호가 가장 강한 키이고, 비교 전 하이픈·공백을 지우는 **정규화**가 필요합니다. 번호가 없으면 정규화한 상호로 후보만 만들어 스튜어드 검토로 보냅니다.
- **생존 규칙 예**: 상호는 출처 우선순위(한빛제약 ERP > 한빛푸드 > 한빛로지스), 주소는 가장 최근 수정값, 사업자등록번호는 표준 형식으로.
- **교차참조(XREF)**: 그룹거래처번호 ↔ (회사코드, 원천 거래처번호). DW 팩트는 원천 번호로 들어와도 교차참조를 통해 그룹 거래처로 집계됩니다.

Day 4에서 본 것처럼 같은 사업자 아래 지점을 별도 거래처로 관리하는 경우가 있습니다. 그래서 "사업자번호가 같으면 무조건 하나"가 아니라 "그룹 분석에서는 하나로 본다"는 오너의 결정이 먼저 있어야 합니다.

### 5. 로트·유효기한 관리: 마스터 거버넌스의 실전

로트 마스터(TB_LOT)에 대해 오너가 정해야 할 규칙은 이런 것들입니다.

- **유효기한 산식**: 완제품은 제조일자 + 품목 유효기간(SHELF_LIFE_MM) − 1일(공통 샘플이 따르는 규칙). 원료는 품목 단위 유효기간이 없으므로 입고 시 공급처 기준 기한을 등록.
- **출고 원칙**: **FEFO**(First Expired, First Out, 유효기한이 먼저 끝나는 로트부터). 제조일 순(FIFO)과 대개 같지만 유효기간이 다른 로트가 섞이면 달라집니다.
- **임박 기준**: 몇 개월 남으면 "임박"인가, 거래처별 최소 잔여기간이 있는가(오너가 정함. 이 과정은 가상 기준 18개월).
- **추적성**: 원료 로트 → 제품 로트 → 출고 거래처를 정·역방향 모두 따라가야 회수 범위를 정합니다.

## 예시

### 계열사 거래처 통합: 매칭 → 교차참조 → 골든 레코드

```sql
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE lab.tb_cust_src (                 -- 계열사별 원천 거래처 (DW 수집본)
  co_cd        VARCHAR(4)   NOT NULL,
  src_cust_no  VARCHAR(20)  NOT NULL,
  cust_nm      VARCHAR(100) NOT NULL,
  biz_reg_no   VARCHAR(20),
  addr         VARCHAR(200),
  upd_dt       DATE         NOT NULL,
  PRIMARY KEY (co_cd, src_cust_no)
);
INSERT INTO lab.tb_cust_src VALUES
 ('1000', 'C000101', '청솔내과의원',   '101-11-00001', '서울 (가상)',               DATE '2025-01-02'),
 ('1000', 'C000201', '햇살약국',       '201-12-00003', '서울 (가상)',               DATE '2025-01-02'),
 ('1000', 'C000102', '미래종합병원',   '124-81-00002', '경기 (가상)',               DATE '2025-01-02'),
 ('1000', 'C000301', '바른팜유통',     '135-86-00005', '경기 성남시 (가상)',        DATE '2025-03-01'),
 ('3000', 'F-0091',  '(주)바른팜유통', '1358600005',   '경기 성남시 분당구 (가상)', DATE '2026-02-10'),
 ('2000', 'L-0077',  '바른팜 유통',    '135-86-00005', NULL,                        DATE '2025-11-20'),
 ('2000', 'L-0080',  '미래종합병원',   '124-81-00002', '경기 (가상)',               DATE '2025-06-01'),
 ('3000', 'F-0102',  '햇살 약국',      NULL,           '서울 (가상)',               DATE '2026-01-15');

CREATE TABLE lab.tb_co_prio (co_cd VARCHAR(4) PRIMARY KEY, nm_prio NUMERIC(2) NOT NULL);  -- 상호 출처 우선순위
INSERT INTO lab.tb_co_prio VALUES ('1000', 1), ('3000', 2), ('2000', 3);

-- 1) 정규화 + 사업자번호 매칭 → 교차참조
CREATE TABLE lab.tb_cust_xref AS
WITH n AS (
  SELECT s.*,
         NULLIF(regexp_replace(COALESCE(biz_reg_no, ''), '[^0-9]', '', 'g'), '') AS biz_key,
         regexp_replace(replace(cust_nm, '(주)', ''), '\s', '', 'g')            AS nm_key
    FROM lab.tb_cust_src s
)
SELECT 'G' || lpad(DENSE_RANK() OVER (ORDER BY biz_key)::text, 6, '0') AS grp_cust_no,
       co_cd, src_cust_no, biz_key, nm_key, 'BIZ' AS match_tp_cd
  FROM n
 WHERE biz_key IS NOT NULL;

SELECT grp_cust_no, co_cd, src_cust_no, biz_key FROM lab.tb_cust_xref ORDER BY 1, 2;

-- 2) 사업자번호가 없는 레코드: 상호가 같으면 "후보"로만 (스튜어드 검토 대기열)
SELECT s.co_cd, s.src_cust_no, s.cust_nm, x.grp_cust_no AS cand_grp_cust_no
  FROM lab.tb_cust_src s
  JOIN lab.tb_cust_xref x ON x.nm_key = regexp_replace(replace(s.cust_nm, '(주)', ''), '\s', '', 'g')
 WHERE s.biz_reg_no IS NULL;

-- 3) 생존 규칙으로 골든 레코드
SELECT x.grp_cust_no,
       (array_agg(s.cust_nm ORDER BY p.nm_prio))[1]                                AS cust_nm,
       substr(MAX(x.biz_key), 1, 3) || '-' || substr(MAX(x.biz_key), 4, 2) || '-'
         || substr(MAX(x.biz_key), 6)                                               AS biz_reg_no,
       (array_agg(s.addr ORDER BY s.upd_dt DESC) FILTER (WHERE s.addr IS NOT NULL))[1] AS addr,
       COUNT(*) AS src_cnt
  FROM lab.tb_cust_xref x
  JOIN lab.tb_cust_src s ON s.co_cd = x.co_cd AND s.src_cust_no = x.src_cust_no
  JOIN lab.tb_co_prio  p ON p.co_cd = s.co_cd
 GROUP BY x.grp_cust_no
 ORDER BY x.grp_cust_no;
```

| 그룹거래처번호 | 상호 (우선순위) | 사업자등록번호 (표준 형식) | 주소 (최신값) | 원천 수 |
|---|---|---|---|---|
| G000001 | 청솔내과의원 | 101-11-00001 | 서울 (가상) | 1 |
| G000002 | 미래종합병원 | 124-81-00002 | 경기 (가상) | 2 |
| G000003 | 바른팜유통 | 135-86-00005 | 경기 성남시 분당구 (가상) | 3 |
| G000004 | 햇살약국 | 201-12-00003 | 서울 (가상) | 1 |

바른팜유통 세 레코드는 정규화 덕분에 하이픈 없는 한빛푸드 번호까지 G000003 하나로 묶였고, 상호는 한빛제약 값이, 주소는 가장 최근(2026-02-10) 한빛푸드 값이 살아남았습니다. **속성마다 생존 규칙이 다를 수 있다**는 것이 핵심입니다. 한빛푸드의 "햇살 약국"(F-0102)은 사업자번호가 없어 자동으로 묶이지 않고 G000004 후보로만 올라갔습니다. 다른 약국일 수도 있으므로 스튜어드가 확정합니다.

그룹번호를 DENSE_RANK로 만든 것은 실습용입니다. 실무에서는 번호가 다음 배치에서 바뀌면 안 되므로(Day 4의 불변성) 교차참조에 **누적 부여**하고 새 사업자번호에만 채번합니다.

### 로트 마스터 규칙 점검: 유효기한 산식

```sql
SELECT l.lot_no, l.item_cd, i.item_tp_cd, l.mfg_dt, i.shelf_life_mm, l.exp_dt,
       (l.mfg_dt + make_interval(months => i.shelf_life_mm::int) - INTERVAL '1 day')::date AS calc_exp_dt,
       CASE WHEN i.shelf_life_mm IS NULL THEN '산식 대상 아님(원료)'
            WHEN l.exp_dt = (l.mfg_dt + make_interval(months => i.shelf_life_mm::int) - INTERVAL '1 day')::date THEN '일치'
            ELSE '불일치' END AS chk
  FROM erp.tb_lot l
  JOIN erp.tb_item i ON i.item_cd = l.item_cd
 ORDER BY l.lot_no;
```

완제품 로트 4개는 모두 산식과 일치하고, 원료 R260201은 대상이 아닙니다. Day 12의 품질 규칙으로 등록하면 유효기한 오입력을 그날 잡습니다.

:::note Oracle 차이
월 더하기는 `ADD_MONTHS(MFG_DT, SHELF_LIFE_MM) - 1`입니다. Oracle의 ADD_MONTHS는 시작일이 그 달의 말일이면 결과도 말일로 맞추므로, 월말 제조 로트에서는 PostgreSQL의 interval 덧셈과 결과가 다를 수 있습니다. 산식을 표준으로 정할 때 월말 규칙까지 명시합니다.
:::

### 유효기한 임박 재고

3월 31일 마감 재고를 잔여 유효기간으로 봅니다. 임박 기준(잔여 18개월 미만)은 가상의 오너 결정입니다.

```sql
SELECT v.wh_cd, v.lot_no, v.item_cd, v.inv_qty, l.exp_dt,
       l.exp_dt - DATE '2026-03-31' AS remain_days,
       EXTRACT(YEAR FROM age(l.exp_dt, DATE '2026-03-31')) * 12
         + EXTRACT(MONTH FROM age(l.exp_dt, DATE '2026-03-31')) AS remain_mm,
       round((l.exp_dt - DATE '2026-03-31')::numeric / (l.exp_dt - l.mfg_dt) * 100) AS remain_pct,
       CASE WHEN l.exp_dt < (DATE '2026-03-31' + INTERVAL '18 months')::date THEN '임박' ELSE '정상' END AS exp_stat
  FROM erp.tb_inv_daily v
  JOIN erp.tb_lot l ON l.lot_no = v.lot_no
 WHERE v.inv_dt = DATE '2026-03-31' AND v.inv_qty > 0
 ORDER BY l.exp_dt;
```

한빛시럽 L250620(480 EA)이 잔여 14개월, 전체 유효기간의 61%로 "임박"입니다. 잔여 개월수와 잔여 비율 중 무엇을 기준으로 할지도 오너가 정합니다. 24개월짜리 시럽과 36개월짜리 정제를 같은 "18개월"로 보면 시럽이 늘 먼저 임박이 됩니다.

### FEFO 출고 로트 배정

한빛펜정의 가상 로트 L251201(2025-12-01 제조)을 W01에 300 BOX 넣고 400 BOX 주문에 로트를 배정합니다. 트랜잭션 안에서 넣고 되돌립니다.

```sql
BEGIN;
INSERT INTO erp.tb_lot VALUES ('L251201', 'P10001', DATE '2025-12-01', DATE '2028-11-30');
INSERT INTO erp.tb_inv_daily VALUES (DATE '2026-03-31', 'W01', 'P10001', 'L251201', 300);

WITH req AS (SELECT 'W01'::varchar AS wh_cd, 'P10001'::varchar AS item_cd, 400 AS req_qty),
avail AS (
  SELECT v.lot_no, l.exp_dt, v.inv_qty,
         SUM(v.inv_qty) OVER (ORDER BY l.exp_dt, v.lot_no) - v.inv_qty AS cum_before
    FROM erp.tb_inv_daily v
    JOIN erp.tb_lot l ON l.lot_no = v.lot_no
    JOIN req r ON r.wh_cd = v.wh_cd AND r.item_cd = v.item_cd
   WHERE v.inv_dt = DATE '2026-03-31' AND v.inv_qty > 0
     AND l.exp_dt >= DATE '2026-04-03'                 -- 출고일 기준 유효기한 경과 로트 제외
)
SELECT a.lot_no, a.exp_dt, a.inv_qty,
       LEAST(a.inv_qty, r.req_qty - a.cum_before) AS alloc_qty
  FROM avail a CROSS JOIN req r
 WHERE a.cum_before < r.req_qty
 ORDER BY a.exp_dt;
ROLLBACK;
```

| 로트 | 유효기한 | 재고 | 배정 |
|---|---|---|---|
| L251201 | 2028-11-30 | 300 | 300 |
| L260105 | 2029-01-04 | 1,900 | 100 |

L250901(2028-08-31)이 가장 먼저 끝나지만 재고가 0이라 후보에서 빠지고, 유효기한 순으로 L251201 전량 300 BOX와 L260105 100 BOX가 배정됩니다. 공통 샘플의 출고 SH2026030003(L250901 200 → L260105 100)도 같은 원칙으로 나간 것입니다. 실제 WMS는 여기에 로트 품질 상태(시험 중·적합·출하 보류)와 거래처별 최소 잔여기간 조건을 더합니다. 공통 스키마 TB_LOT에는 **품질 상태 컬럼이 없으므로**, QA가 로트상태코드(LOT_STAT_CD) 추가를 요구할 대목입니다.

### 로트 추적: 정방향과 역방향

공통 스키마에는 어떤 원료 로트를 생산에 썼는지(투입실적)가 없어 `lab`에 만듭니다. 투입량은 BOM(원료A 0.0150 KG, 호일 0.0020 ROLL × 2,000 BOX)과 맞췄고, 원료 로트 R251215·M251130은 시스템 오픈 전에 입고된 가상의 로트입니다.

```sql
CREATE TABLE lab.tb_prod_input (                -- 생산투입실적 (원료 로트 → 제품 로트)
  wo_no          VARCHAR(14)   NOT NULL REFERENCES erp.tb_wo (wo_no),
  prod_lot_no    VARCHAR(20)   NOT NULL REFERENCES erp.tb_lot (lot_no),
  input_item_cd  VARCHAR(10)   NOT NULL REFERENCES erp.tb_item (item_cd),
  input_lot_no   VARCHAR(20)   NOT NULL,        -- 원료 로트 (오픈 전 로트는 TB_LOT에 없음)
  input_qty      NUMERIC(12,4) NOT NULL CHECK (input_qty > 0),
  PRIMARY KEY (wo_no, prod_lot_no, input_lot_no)
);
INSERT INTO lab.tb_prod_input VALUES
 ('WO2026010001', 'L260105', 'R20001', 'R251215', 30),
 ('WO2026010001', 'L260105', 'M30001', 'M251130', 4);

-- 정방향: 원료 로트 R251215 → 제품 로트 → 출고 거래처 (+ 남은 재고)
WITH RECURSIVE fwd AS (
  SELECT input_lot_no AS src_lot_no, prod_lot_no AS lot_no, 1 AS lvl
    FROM lab.tb_prod_input WHERE input_lot_no = 'R251215'
  UNION ALL
  SELECT f.src_lot_no, p.prod_lot_no, f.lvl + 1
    FROM fwd f JOIN lab.tb_prod_input p ON p.input_lot_no = f.lot_no
   WHERE f.lvl < 5
)
SELECT f.src_lot_no, f.lot_no AS prod_lot_no, s.ship_dt, s.ship_no, o.cust_no, c.cust_nm, d.ship_qty
  FROM fwd f
  JOIN erp.tb_ship_dtl d ON d.lot_no = f.lot_no
  JOIN erp.tb_ship s     ON s.ship_no = d.ship_no
  JOIN erp.tb_ord o      ON o.ord_no = s.ord_no
  JOIN erp.tb_cust c     ON c.cust_no = o.cust_no
UNION ALL
SELECT 'R251215', v.lot_no, v.inv_dt, '(재고 ' || v.wh_cd || ')', NULL, NULL, v.inv_qty
  FROM erp.tb_inv_daily v
 WHERE v.lot_no IN (SELECT prod_lot_no FROM lab.tb_prod_input WHERE input_lot_no = 'R251215')
   AND v.inv_dt = DATE '2026-03-31';
```

원료 로트 R251215는 제품 로트 L260105가 되었고, 그중 100 BOX가 3월 11일 바른팜유통으로 나갔고 1,900 BOX가 W01에 남아 있습니다. 회수가 필요하다면 연락할 거래처는 한 곳, 묶어 둘 재고는 1,900 BOX입니다. 생산 2,000 = 출고 100 + 재고 1,900으로 수불도 맞습니다. 재귀로 쓴 것은 원료 → 반제품(S40002) → 완제품처럼 단계가 늘어도(Day 6) 같은 쿼리로 가기 위해서입니다.

```sql
-- 역방향: 바른팜유통(C000301)이 받은 한빛펜정은 어느 로트, 어느 원료에서 왔나
SELECT s.ship_dt, d.lot_no AS prod_lot_no, d.ship_qty,
       r.wo_no, r.prod_dt, i.input_item_cd, i.input_lot_no, rd.rcv_no AS input_rcv_no,
       CASE WHEN r.wo_no IS NULL THEN '생산실적 없음 (이관 전 로트)'
            WHEN rd.rcv_no IS NULL THEN '원료 입고 기록 없음 (이관 전)'
            ELSE '추적 완료' END AS trace_stat
  FROM erp.tb_ord o
  JOIN erp.tb_ship s          ON s.ord_no = o.ord_no
  JOIN erp.tb_ship_dtl d      ON d.ship_no = s.ship_no
  LEFT JOIN erp.tb_prod_rslt r ON r.lot_no = d.lot_no
  LEFT JOIN lab.tb_prod_input i ON i.prod_lot_no = d.lot_no
  LEFT JOIN erp.tb_rcv_dtl rd  ON rd.lot_no = i.input_lot_no
 WHERE o.cust_no = 'C000301' AND d.item_cd = 'P10001'
 ORDER BY d.lot_no, i.input_item_cd;
```

L260105는 작업지시 WO2026010001과 원료 로트 둘까지 이어지지만, 원료 입고 기록이 없어 구매처까지는 가지 못합니다. L250901은 생산실적 자체가 없어 거기서 끊깁니다. 둘 다 **시스템 오픈 이전 데이터의 이관 범위** 문제입니다. 추적성은 쿼리가 아니라 "로트가 생기는 모든 지점(입고·생산·투입·출고)에서 로트번호를 빠짐없이 남긴다"는 거버넌스 규칙으로 지켜집니다. 이관 계획에 기초재고뿐 아니라 **기초 로트 계보**를 넣을지는 QA와 정할 일입니다.

## Before / After

| 항목 | Before | After |
|---|---|---|
| 거래처 | 계열사별 등록, 그룹 매출은 엑셀 수작업 합산 | 통합 방식 MDM. 정규화 매칭, 교차참조, 속성별 생존 규칙, 그룹번호 누적 부여 |
| 중복 판단 | 사람마다 다름, 기록 없음 | 자동(사업자번호) + 후보(상호) + 스튜어드 확정 기록 |
| 로트 | 유효기한 손 입력, 점검 없음, 품질 상태 없음 | QA 오너, 유효기한 산식 품질 규칙, 로트상태코드 추가, 임박 기준 승인 |
| 추적 | 원료 투입 기록 없음, 회수 범위는 기억 | 투입실적으로 원료 → 제품 → 거래처 정·역방향 재귀 추적 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| MDM 방식 | 목표가 그룹 분석이고 원천을 바꿀 수 없으면 통합 방식 (DW에서) | 원천 품질 자체가 문제이고 협의체가 있으면 공존·중앙집중 |
| 자동 매칭 | 강한 키(사업자번호)가 정규화 후 일치하면 자동 | 이름·주소만 비슷하면 후보로만, 스튜어드 확정 |
| 생존 규칙 | 출처 신뢰도가 분명한 속성(상호)은 출처 우선순위 | 자주 바뀌는 속성(주소·연락처)은 최신값 |
| 추적 데이터 | 회수 대상이 될 수 있는 품목(의약품)은 투입 로트까지 필수 | 추적 의무가 약한 소모품은 품목 단위까지 |

MDM 실패의 흔한 원인은 알고리즘이 아니라 **오너 부재**입니다. 중복 확정자가 없으면 검토 대기열은 쌓이기만 합니다.

## 흔한 실수 3가지

1. **아키텍트가 업무 기준을 정해 버리는 실수.** 임박 기준, 공식 상호, 중복 판단은 오너 몫입니다.
2. **골든 레코드 번호를 매번 새로 매기는 실수.** 배치마다 그룹번호가 바뀌면 DW 팩트와 BI 필터가 깨집니다. 교차참조는 누적하고 번호는 한 번만 부여합니다.
3. **로트 추적을 "출고상세에 로트번호가 있으니 된다"고 보는 실수.** 원료 투입과 생산입고까지 로트가 이어져야 원료 문제에서 거래처까지 갈 수 있습니다.

## 셀프 체크 질문

**Q1. 데이터 오너와 데이터 스튜어드의 차이를 그룹 거래처 마스터로 설명해 보세요.**

:::answer 모범 답안 보기
오너는 결정하고 책임집니다. 경영지원실이 "사업자번호가 같으면 그룹 분석에서 하나", "상호는 한빛제약 ERP 값 우선" 같은 기준을 승인합니다. 스튜어드는 그 기준대로 매일 일합니다. 계열사 마스터 담당자가 매칭 후보를 확정하고 품질 위반을 조치합니다. 아키텍트는 기준을 매칭 키·생존 규칙·교차참조·품질 규칙으로 구현하지만 기준 자체를 정하지 않습니다.
:::

**Q2. 계열사별 거래처를 통합하는 골든 레코드를 어떻게 만들겠습니까?**

:::answer 모범 답안 보기
먼저 오너와 "같은 거래처"의 정의(사업자 단위인지, 지점 단위인지)를 정합니다. 사업자번호를 정규화해 일치하면 자동 매칭, 번호가 없고 상호·주소만 비슷하면 후보로 올려 스튜어드가 확정합니다. 묶인 레코드는 속성별 생존 규칙(상호는 출처 우선순위, 주소는 최신값)으로 골든 레코드를 만들고, 그룹번호 ↔ (회사, 원천번호) 교차참조를 누적 관리해 번호가 바뀌지 않게 합니다. DW 팩트는 교차참조로 그룹 거래처 차원에 연결합니다.
:::

**Q3. 원료 로트에 품질 문제가 발견됐습니다. 데이터로 무엇을, 어떤 순서로 확인하겠습니까?**

:::answer 모범 답안 보기
정방향부터 합니다. 원료 로트가 투입된 제품 로트(반제품을 거치면 재귀로), 그 로트의 출고 거래처와 수량, 창고에 남은 재고를 뽑아 회수·출하 보류 대상을 정합니다. 생산량 = 출고 + 재고 + 기타 수불로 누락 경로가 없는지 확인하고, 역방향으로 원료 로트의 입고(구매처)를 확인합니다. 이관 전 로트처럼 추적이 끊기는 지점은 범위의 불확실성으로 명시해 QA에 보고합니다.
:::

## 오늘의 과제

**과제 1.** 거래처 통합 결과에서 "그룹 거래처별 원천 목록"을 보여 주세요. 결과 모양은 `grp_cust_no, src_list`(예: `1000:C000301, 2000:L-0077, 3000:F-0091`) 4행입니다. 영업기획팀에 "이 그룹 거래처는 어떤 원천들이 합쳐졌나"를 보여 주는 화면입니다.

:::answer 해설 보기
```sql
SELECT grp_cust_no,
       string_agg(co_cd || ':' || src_cust_no, ', ' ORDER BY co_cd) AS src_list
  FROM lab.tb_cust_xref
 GROUP BY grp_cust_no
 ORDER BY grp_cust_no;
```

G000002는 둘, G000003은 셋입니다. 스튜어드가 F-0102를 G000004로 확정하면 교차참조에 MATCH_TP_CD를 'MANUAL'로 한 행을 넣고, 확정자·확정일을 함께 남깁니다. 수작업 확정도 감사 추적 대상(Day 12)입니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 데이터 거버넌스 체계도 (R&R) | 마스터별 오너·스튜어드·관리자, 협의체 구성, 결정 절차. |
| 마스터 데이터 통합 정의서 | 통합 방식, 매칭 키와 정규화 규칙, 자동/후보 기준, 속성별 생존 규칙, 그룹번호 채번 규칙. |
| 교차참조 테이블정의서 | 그룹번호, 회사코드, 원천번호, 매칭 유형, 확정자·확정일. |
| 로트 관리 기준서 (QA 승인) | 유효기한 산식(월말 규칙 포함), FEFO 원칙, 임박 기준, 로트상태코드, 추적 범위. |

## 참고할 원전

- DAMA International, "DAMA-DMBOK: Data Management Body of Knowledge", 2nd ed. (Technics Publications, 2017) — Data Governance 장, Reference and Master Data 장.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 관리 체계: 데이터 관리 조직과 역할.
- PIC/S, "Good Practices for Data Management and Integrity in Regulated GMP/GDP Environments" — GMP/GDP 환경의 데이터 관리 책임.
