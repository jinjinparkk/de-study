# Day 2. ERP 업무 흐름과 원천 테이블 구조

## 오늘의 한 줄

ERP 테이블은 업무가 지나가며 남긴 발자국입니다. "어떤 문서가 어떤 문서를 낳는가"라는 흐름을 먼저 그리면, 처음 보는 스키마도 헤더/상세, 상태코드, 문서번호 사슬로 읽힙니다.

## 왜 중요한가

DW 엔지니어가 테이블 목록만 보고 "주문상세가 매출이겠지"라며 `TB_ORD_DTL`을 매출 팩트로 적재했다고 해 보겠습니다. 첫 리뷰에서 경영지원실은 "매출은 전표 기준"이라고 하고, 물류팀은 "출고 안 된 주문이 왜 실적이냐"고 묻습니다. 구매 쪽에서는 입고를 발주와 연결하려는데 입고 테이블에 발주번호가 없다는 사실을 구축 막바지에 발견합니다. 원천 테이블의 **업무상 의미와 연결 고리**를 확인하지 않고 적재부터 하면, 설계를 처음부터 다시 하게 됩니다.

## 핵심 개념

### 1. 업무 흐름은 문서의 사슬입니다

쉽게 말하면 ERP는 "앞 문서를 근거로 다음 문서를 만드는" 시스템입니다. 주문이 있어야 출고를 하고, 출고가 있어야 매출전표를 끊습니다. 이 순서가 테이블 사이의 연결 키로 남습니다. 한빛제약그룹의 네 가지 흐름과 공통 스키마 테이블은 이렇습니다.

| 흐름 | 단계 | 원천 테이블 | 다음 문서로 넘어가는 키 |
|---|---|---|---|
| 영업 (한빛제약) | 주문 → 출고 → 매출전표 | TB_ORD/TB_ORD_DTL → TB_SHIP/TB_SHIP_DTL → TB_SLIP/TB_SLIP_DTL | SHIP.ORD_NO, SHIP_DTL.(ORD_NO, ORD_SEQ), SLIP.SRC_DOC_NO |
| 구매 | 발주 → 입고 | TB_PO/TB_PO_DTL → TB_RCV/TB_RCV_DTL (RCV_TP_CD 01 구매입고) | RCV.VNDR_NO 뿐. 발주번호 없음 |
| 생산 (한빛케미칼) | 작업지시 → 생산실적 → 생산입고 | TB_WO → TB_PROD_RSLT → TB_RCV/TB_RCV_DTL (RCV_TP_CD 02) | PROD_RSLT.WO_NO, 그 다음은 LOT_NO |
| 회계 | 전표 | TB_SLIP/TB_SLIP_DTL | SLIP.SRC_DOC_NO (원천 문서번호) |
| 재고 | 입고(+), 출고(-), 일 마감 | TB_RCV_DTL, TB_SHIP_DTL, TB_INV_DAILY | WH_CD, ITEM_CD, LOT_NO |

정확한 용어로 이런 흐름을 영업은 Order-to-Cash, 구매는 Procure-to-Pay라고 부르기도 합니다. 이름보다 중요한 것은 **각 단계가 어떤 테이블에 어떤 키를 남기는가**입니다. 이 표가 원천 분석의 첫 산출물입니다.

### 2. 헤더/상세 패턴: grain을 읽는 첫 단서

ERP 문서는 대부분 헤더와 상세로 나뉩니다. 헤더는 "언제, 누가, 누구와, 지금 어떤 상태인가"를 한 번만 적고, 상세는 "무엇을 얼마나"를 줄마다 적습니다. 그래서 헤더 1행은 문서 1건, 상세 1행은 문서의 한 줄입니다.

| 테이블 | 한 행의 의미 (grain) | 주의할 점 |
|---|---|---|
| TB_ORD | 주문 1건 | 상태(ORD_STAT_CD)가 여기에만 있음 |
| TB_ORD_DTL | 주문의 품목 1줄 | 금액은 여기에만 있음 |
| TB_SHIP_DTL | 출고된 로트 1줄 | 주문상세 1줄이 **여러 로트로 나뉘어** 여러 행이 될 수 있음 |
| TB_PROD_RSLT | 작업지시별 생산 로트 1건 | 헤더/상세가 아니라 (WO_NO, LOT_NO) 단위 |
| TB_SLIP_DTL | 전표의 계정 1줄 | 한 전표 안에서 차변 합계 = 대변 합계 |
| TB_INV_DAILY | 일자·창고·품목·로트별 마감 수량 | 거래가 아니라 **상태의 사진** (스냅샷) |

DW에서 가장 흔한 사고인 "금액이 부풀었다"는 거의 항상 grain이 다른 두 테이블을 그냥 조인해서 생깁니다. 공통 샘플에서도 SO2026030003의 1번 줄(300 BOX)은 출고상세에서 200 + 100, 두 행으로 나뉩니다.

### 3. 상태코드: 문서의 생애가 한 컬럼에 덮어써집니다

주문은 10 접수 → 20 확정 → 30 출고완료로 진행되고, 출고 전에는 90 취소가 될 수 있습니다. 대부분의 ERP는 상태가 바뀔 때 **새 행을 만들지 않고 같은 행의 상태 컬럼을 UPDATE** 합니다. 그래서 운영계에는 "언제 확정됐는가"가 남지 않을 수 있습니다.

이 사실은 DW 설계에 바로 영향을 줍니다. 첫째, 증분 적재는 "새로 생긴 행"뿐 아니라 "상태가 바뀐 행"도 잡아야 합니다. 그러려면 수정일시(UPD_DTM)가 믿을 만한지 확인해야 합니다. 공통 스키마의 `TB_ORD`에는 UPD_DTM이 있지만 `TB_ORD_DTL`에는 없습니다. 상세 수량이 정정되면 어떻게 감지할지 ERP 팀에 물어야 합니다(Day 22). 둘째, 상태 전이 시점 분석(확정까지 걸린 시간 등)이 필요하면 운영계 로그나 DW의 누적 스냅샷 팩트(Day 17)가 필요합니다.

### 4. 문서번호 사슬: 컬럼 이름보다 실제 값으로 확인합니다

영업 흐름의 사슬은 `ORD_NO → TB_SHIP.ORD_NO → TB_SLIP.SRC_DOC_NO`입니다. 그런데 사슬마다 성격이 다릅니다.

- 주문 → 출고: FK가 걸려 있어 DB가 보장합니다.
- 출고 → 전표: 공통 스키마에서 전표의 SRC_DOC_NO에는 **출고번호가 아니라 주문번호**가 들어 있습니다(SL2026030001 → SO2026030001). FK가 없고 문서 유형 컬럼도 없어서, 어떤 문서번호인지는 접두어(SO, RC)로 짐작할 수밖에 없습니다.
- 발주 → 입고: 연결 컬럼이 아예 없습니다. 구매처·품목·일자로 추정 매칭을 해야 합니다.
- 작업지시 → 생산입고: 직접 키는 없고 **로트번호**로 이어집니다.

FK 제약 목록만 보면 앞의 하나만 보입니다. 나머지는 데이터 값을 보고, ERP 팀에 확인해야 알 수 있습니다. 그래서 원천 분석은 "카탈로그 조회 + 값 프로파일링 + 인터뷰" 세 가지를 같이 합니다.

### 5. 수불과 스냅샷: 재고는 두 방식으로 남습니다

재고는 거래(입고 +, 출고 -)를 누적해서 구할 수도 있고, 매일 마감 시점 수량(TB_INV_DAILY)을 찍어 둔 사진으로 볼 수도 있습니다. 두 값이 맞으려면 **기초재고**(데이터가 시작되기 전 이미 있던 수량)를 알아야 합니다. 공통 샘플처럼 거래 기록이 일부 기간만 있으면 수불 합계와 스냅샷이 다르게 나오며, 이 차이는 오류가 아니라 "기초재고가 어디 있는가"라는 질문입니다.

## 예시

### 처음 보는 스키마 읽기 1단계: 카탈로그에서 관계 뽑기

```sql
-- erp 스키마의 FK 관계 목록: 어떤 테이블이 어떤 테이블을 참조하는가
SELECT conrelid::regclass  AS child_table,
       confrelid::regclass AS parent_table,
       pg_get_constraintdef(oid) AS fk_definition
  FROM pg_constraint
 WHERE contype = 'f'
   AND connamespace = 'erp'::regnamespace
 ORDER BY 1, 2;
```

:::note Oracle 차이
Oracle에서는 `ALL_CONSTRAINTS`(CONSTRAINT_TYPE = 'R')와 `ALL_CONS_COLUMNS`를 조인하고, R_CONSTRAINT_NAME으로 부모 테이블의 PK를 찾습니다. 운영 DB 계정에 딕셔너리 조회 권한이 있는지 먼저 확인하세요.
:::

결과에서 `tb_ship_dtl → tb_ord_dtl`은 보이지만 `tb_slip → tb_ord`, `tb_rcv → tb_po`는 보이지 않습니다. 보이지 않는 연결이 오늘의 핵심입니다.

### 2단계: 상태코드와 값 프로파일링

```sql
-- 주문 상태별 건수와 기간
SELECT ord_stat_cd, COUNT(*) AS ord_cnt, MIN(ord_dt) AS min_dt, MAX(ord_dt) AS max_dt
  FROM erp.tb_ord
 GROUP BY ord_stat_cd
 ORDER BY ord_stat_cd;
```

결과는 10 접수 1건, 20 확정 1건, 30 출고완료 3건, 90 취소 1건입니다. 실무에서는 여기서 정의서에 없는 코드(예: 15, 99)가 나오는지부터 봅니다. 나온다면 그 코드의 뜻을 ERP 팀에 물어야 합니다.

### 3단계: 영업 문서번호 사슬 따라가기

```sql
-- 주문 → 출고 → 매출전표가 어디까지 이어졌나
SELECT o.ord_no, o.ord_stat_cd,
       (SELECT string_agg(s.ship_no, ',' ORDER BY s.ship_no)
          FROM erp.tb_ship s WHERE s.ord_no = o.ord_no)      AS ship_nos,
       (SELECT string_agg(sl.slip_no, ',' ORDER BY sl.slip_no)
          FROM erp.tb_slip sl WHERE sl.src_doc_no = o.ord_no) AS slip_nos
  FROM erp.tb_ord o
 ORDER BY o.ord_no;
```

| ord_no | ord_stat_cd | ship_nos | slip_nos |
|---|---|---|---|
| SO2026030001 | 30 | SH2026030001 | SL2026030001 |
| SO2026030002 | 30 | SH2026030002 | |
| SO2026030003 | 30 | SH2026030003 | |
| SO2026030004 | 20 | | |
| SO2026040001 | 10 | | |
| SO2026040002 | 90 | | |

출고완료인데 전표가 없는 주문이 두 건 보입니다. 공통 샘플은 전표를 한 건만 담고 있어서 생긴 결과지만, 실제 원천 분석에서는 이것이 "전표가 아직 안 끊긴 것인가, 월말에 묶어서 끊는가, 다른 문서번호로 연결되는가"라는 질문이 됩니다. 이 답에 따라 매출 팩트의 원천이 주문인지 출고인지 전표인지가 바뀝니다.

### 4단계: 전표 구조 확인

```sql
-- 전표별 차변·대변 합계와 균형 여부, 원천 주문 금액과 비교
SELECT sl.slip_no, sl.src_doc_no,
       SUM(sd.dr_amt) AS dr_sum,
       SUM(sd.cr_amt) AS cr_sum,
       SUM(sd.dr_amt) = SUM(sd.cr_amt) AS balanced,
       SUM(CASE WHEN sd.acct_cd = '41100' THEN sd.cr_amt ELSE 0 END) AS sales_cr,
       (SELECT SUM(d.ord_amt) FROM erp.tb_ord_dtl d WHERE d.ord_no = sl.src_doc_no) AS src_ord_amt
  FROM erp.tb_slip sl
  JOIN erp.tb_slip_dtl sd ON sd.slip_no = sl.slip_no
 GROUP BY sl.slip_no, sl.src_doc_no;
```

SL2026030001은 차변 90,200원(외상매출금), 대변 82,000원(제품매출) + 8,200원(부가세예수금)으로 균형이 맞고, 제품매출 82,000원은 원천 주문금액과 같습니다. DW에서 "매출"을 전표 기준으로 정의한다면 이 전표 상세의 41100 계정 대변이 원천입니다. 반대로 주문 기준이라면 부가세가 빠진 공급가액이라는 점도 함께 적어 둬야 합니다.

### 5단계: 생산 흐름은 로트로 이어집니다

```sql
-- 작업지시 → 생산실적 → 생산입고
SELECT w.wo_no, w.item_cd, w.wo_qty,
       p.prod_dt, p.lot_no, p.good_qty, p.defect_qty,
       r.rcv_no, r.rcv_dt, rd.rcv_qty
  FROM erp.tb_wo w
  JOIN erp.tb_prod_rslt p   ON p.wo_no = w.wo_no
  LEFT JOIN erp.tb_rcv_dtl rd ON rd.lot_no = p.lot_no AND rd.item_cd = w.item_cd
  LEFT JOIN erp.tb_rcv r      ON r.rcv_no = rd.rcv_no AND r.rcv_tp_cd = '02';
```

WO2026010001은 P10001 2,000 BOX를 지시했고, 1월 5일 로트 L260105로 양품 2,000, 불량 12가 나왔고, 1월 8일 RC2026010001로 2,000이 입고됐습니다. 입고 테이블에는 작업지시번호가 없으므로 **로트번호가 유일한 다리**입니다. 로트 하나가 여러 작업지시에서 나올 수 있는지, 생산입고가 분할될 수 있는지를 확인하지 않으면 이 조인은 언제든 행이 불어날 수 있습니다.

### 6단계: 구매 흐름은 키 없이 추정해야 합니다

```sql
-- 발주와 입고를 구매처·품목·일자로 추정 매칭
SELECT po.po_no, po.po_dt, po.co_cd, pd.item_cd, pd.po_qty,
       r.rcv_no, r.rcv_dt, r.wh_cd, rd.rcv_qty
  FROM erp.tb_po po
  JOIN erp.tb_po_dtl pd ON pd.po_no = po.po_no
  LEFT JOIN erp.tb_rcv r
         ON r.vndr_no = po.vndr_no AND r.rcv_tp_cd = '01' AND r.rcv_dt >= po.po_dt
  LEFT JOIN erp.tb_rcv_dtl rd
         ON rd.rcv_no = r.rcv_no AND rd.item_cd = pd.item_cd;
```

샘플에서는 PO2026010001(R20001 500 KG)이 RC2026020001(500 KG)과 짝이 맞습니다. 하지만 같은 구매처에 같은 원료를 두 번 발주하면 이 조인은 2 × 2 = 4행을 만듭니다. 추정 매칭을 DW에 넣기 전에 ERP에 발주번호를 들고 있는 다른 테이블(입고 예정, 검수 등)이 있는지 반드시 물어야 합니다. 발주 회사는 4000 한빛케미칼인데 입고 창고 W01은 2000 한빛로지스 소속이라는 점도 확인 대상입니다. 계열사 간 물류 위탁 구조라면 DW에서 "누구의 재고인가"를 따로 정의해야 합니다.

### 7단계: 수불과 스냅샷 대조

```sql
-- 3월 31일까지 로트별 입고·출고 합계와 일 마감 재고 비교 (W01)
WITH mv AS (
  SELECT rd.item_cd, rd.lot_no, rd.rcv_qty AS in_qty, 0 AS out_qty
    FROM erp.tb_rcv r JOIN erp.tb_rcv_dtl rd ON rd.rcv_no = r.rcv_no
   WHERE r.wh_cd = 'W01' AND r.rcv_dt <= DATE '2026-03-31'
  UNION ALL
  SELECT sd.item_cd, sd.lot_no, 0, sd.ship_qty
    FROM erp.tb_ship s JOIN erp.tb_ship_dtl sd ON sd.ship_no = s.ship_no
   WHERE s.wh_cd = 'W01' AND s.ship_dt <= DATE '2026-03-31'
)
SELECT i.item_cd, i.lot_no,
       COALESCE(SUM(mv.in_qty), 0)  AS in_qty,
       COALESCE(SUM(mv.out_qty), 0) AS out_qty,
       i.inv_qty                    AS snapshot_qty,
       i.inv_qty - (COALESCE(SUM(mv.in_qty), 0) - COALESCE(SUM(mv.out_qty), 0)) AS implied_opening_qty
  FROM erp.tb_inv_daily i
  LEFT JOIN mv ON mv.item_cd = i.item_cd AND mv.lot_no = i.lot_no
 WHERE i.inv_dt = DATE '2026-03-31' AND i.wh_cd = 'W01'
 GROUP BY i.item_cd, i.lot_no, i.inv_qty
 ORDER BY i.item_cd, i.lot_no;
```

| item_cd | lot_no | in_qty | out_qty | snapshot_qty | implied_opening_qty |
|---|---|---|---|---|---|
| P10001 | L250901 | 0 | 210 | 0 | 210 |
| P10001 | L260105 | 2000 | 100 | 1900 | 0 |
| P10002 | L251110 | 0 | 105 | 395 | 500 |
| P10003 | L250620 | 0 | 20 | 480 | 500 |
| R20001 | R260201 | 500 | 0 | 500 | 0 |

거래가 모두 샘플 안에 있는 로트(L260105, R260201)는 정확히 맞고, 나머지는 기초재고만큼 차이가 납니다. DW에서 재고를 수불로 재계산할지, 스냅샷을 그대로 받을지 정하기 전에 "기초재고와 월 마감 데이터는 어디에 있는가"를 확인해야 하는 이유입니다.

## Before / After

**Before: 테이블 이름으로 원천을 고른 설계**

| 결정 | 근거 | 생긴 문제 |
|---|---|---|
| 매출 팩트 원천 = TB_ORD_DTL | "주문상세에 금액이 있으니까" | 취소·미출고 포함, 회계 매출과 불일치 |
| 출고 팩트 = TB_SHIP_DTL과 TB_ORD_DTL 조인 후 금액 합산 | "단가는 주문상세에 있으니까" | 로트 분할 행만큼 주문금액이 중복 합산 |
| 구매 실적 = 발주와 입고를 구매처로 조인 | "키가 그것뿐이라서" | 같은 구매처 반복 발주 시 행 증식 |
| 증분 적재 = REG_DTM 기준 | "등록일시가 있으니까" | 상태 변경(확정→취소)이 DW에 반영 안 됨 |

**After: 흐름부터 그리고, 사슬마다 근거를 적은 원천 분석서**

| 흐름 단계 | 원천 | 연결 방식 | 확인 상태 |
|---|---|---|---|
| 주문 → 출고 | TB_SHIP_DTL.(ORD_NO, ORD_SEQ) | FK (DB 보장) | 확인 완료 |
| 출고 → 매출전표 | TB_SLIP.SRC_DOC_NO = 주문번호 | 값 규칙, FK 없음 | ERP 팀 확인 필요: 출고별·월별 전표 발행 규칙 |
| 발주 → 입고 | 없음 (구매처·품목·일자 추정) | 추정 | ERP 팀 확인 필요: 발주번호 보유 테이블 |
| 작업지시 → 생산입고 | LOT_NO | 값 규칙 | 확인 필요: 로트와 작업지시 1:1 여부 |
| 재고 | TB_INV_DAILY 스냅샷 | 일 마감 | 확인 필요: 기초재고, 마감 시각 |
| 증분 기준 | TB_ORD.UPD_DTM | 수정일시 | 확인 필요: TB_ORD_DTL 변경 감지 방법 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 매출 팩트의 원천 | 경영 보고·회계 대사가 목적이면 전표 기준 | 영업 활동 관리(수주 추이)가 목적이면 주문 기준, 물류 성과면 출고 기준. 셋 다 필요하면 팩트를 나누고 용어도 나눔 |
| FK가 없는 연결 | 값 규칙이 문서화돼 있고 프로파일링으로 예외가 없으면 DW에서 조인 키로 사용 | 추정 매칭이 필요하면 DW 팩트에 넣기 전에 ERP 쪽 키 추가를 요청하거나, 매칭 결과를 "추정"으로 표시 |
| 상태가 덮어써지는 테이블 | 최종 상태만 분석하면 주기 적재 + 상태 컬럼 갱신 | 상태 전이 시점이 필요하면 CDC나 변경 로그 확보를 먼저 협의 |
| 재고 원천 | 마감 스냅샷이 신뢰되면 스냅샷 적재 | 스냅샷이 없거나 마감 규칙이 불명확하면 수불 재계산 + 기초재고 확보 |
| 처음 보는 스키마 | 카탈로그 조회 → 값 프로파일링 → 인터뷰 순서로 | 문서가 최신이라는 확인이 없으면 문서보다 실제 데이터를 믿고 차이를 기록 |

ERP 운영팀에 가져갈 질문 목록도 산출물입니다. 시니어는 아래 질문을 첫 미팅 전에 준비합니다.

| 질문 | 왜 묻는가 |
|---|---|
| 상태코드 전체 목록과 허용되는 전이(10→90 가능? 30→90 가능?) | 취소·반품 처리와 팩트 정의 |
| 삭제는 물리 삭제인가, 상태 변경인가 | 증분 적재에서 삭제 감지 방법 |
| 어떤 테이블에 UPD_DTM이 있고, 모든 변경 경로에서 갱신되는가 | 증분 기준 컬럼의 신뢰도 |
| SRC_DOC_NO에 들어가는 문서 유형과 구분 방법 | 전표와 원천 문서 연결 |
| 발주와 입고를 잇는 키가 다른 테이블에 있는가 | 구매 실적 grain |
| 반품·수량 정정은 마이너스 행인가, 별도 문서인가 | 합계 계산 방식 |
| 기초재고·월 마감은 어디에 있고 마감 시각은 언제인가 | 재고 대사 |
| 테이블에 회사코드가 없는데 단일 회사 데이터만 들어오는가 | 그룹 통합 시 회사 구분 |
| 배치 가능 시간대와 운영 DB 조회 제한 | 적재 일정 |

## 흔한 실수 3가지

1. **FK 목록을 연결 관계의 전부로 믿는 실수.** ERP는 성능이나 개발 편의 때문에 FK를 걸지 않은 연결이 많습니다. 전표의 SRC_DOC_NO처럼 값으로만 이어진 사슬은 카탈로그에 나오지 않습니다.
2. **grain이 다른 헤더·상세·로트 행을 조인한 뒤 합산하는 실수.** 주문상세 1줄이 출고상세 여러 줄로 나뉘는 구조를 확인하지 않으면 금액이 부풉니다. 테이블마다 "한 행의 의미"를 먼저 적어 두세요.
3. **"상태가 바뀐다"는 사실을 적재 설계에 반영하지 않는 실수.** 등록일시만으로 증분 적재하면 확정 후 취소된 주문이 DW에 계속 확정으로 남습니다. 상태 컬럼이 있는 테이블은 변경 감지 방법부터 확인합니다.

## 셀프 체크 질문

**Q1. 처음 보는 ERP 스키마를 받았습니다. 첫 이틀 동안 무엇을 어떤 순서로 하겠습니까?**

:::answer 모범 답안 보기
먼저 현업 인터뷰로 업무 흐름(주문→출고→전표, 발주→입고 등)을 그립니다. 다음으로 카탈로그에서 PK·FK와 테이블별 건수를 뽑아 흐름의 각 단계에 테이블을 대응시킵니다. 그다음 값 프로파일링을 합니다. 상태코드 분포, 문서번호 접두어, 연결 컬럼의 매칭률(출고의 주문번호가 주문에 다 있는가, 전표의 SRC_DOC_NO가 어떤 문서와 맞는가)을 봅니다. 마지막으로 FK가 없는 연결, 정의서에 없는 코드, 수정일시가 없는 테이블을 질문 목록으로 만들어 ERP 운영팀과 확인합니다. 결과물은 "흐름 단계 - 원천 테이블 - 연결 방식 - 확인 상태" 표입니다.
:::

**Q2. 공통 스키마에서 생산입고를 작업지시와 연결하는 방법과 그 위험을 설명해 보세요.**

:::answer 모범 답안 보기
입고 테이블에는 작업지시번호가 없으므로 생산실적의 LOT_NO와 입고상세의 LOT_NO, 품목코드로 연결합니다. 위험은 로트와 작업지시가 1:1이라는 가정이 깨질 때입니다. 한 로트를 여러 번에 나눠 입고하거나, 여러 작업지시가 같은 로트번호를 쓰면 조인 결과가 불어납니다. 그래서 ERP 팀에 로트 채번 규칙과 분할 입고 여부를 확인하고, 프로파일링으로 로트별 작업지시 수와 입고 건수를 세어 1:1인지 검증한 뒤에 DW 조인 키로 씁니다.
:::

**Q3. 정 과장은 주문 기준, 경영지원실은 전표 기준 매출을 원합니다. 원천 설계는 어떻게 하겠습니까?**

:::answer 모범 답안 보기
둘 중 하나를 고르게 하지 않고, 서로 다른 업무 사건이므로 원천과 팩트를 나눕니다. 수주 실적은 TB_ORD/TB_ORD_DTL(취소 제외, 기준일 = 주문일자), 회계 매출은 TB_SLIP/TB_SLIP_DTL의 제품매출 계정(기준일 = 전표일자)을 원천으로 삼습니다. 표준용어사전에는 "수주금액"과 "매출액"을 다른 용어로 올리고 부가세 포함 여부까지 적습니다. 그리고 둘을 잇는 SRC_DOC_NO 규칙을 확인해서 "수주했지만 아직 매출로 잡히지 않은 금액"을 대사할 수 있게 합니다. 경영진 대시보드의 대표 지표가 무엇인지는 지표 오너인 경영지원실이 확정하도록 의사결정 요청을 올립니다.
:::

## 오늘의 과제

**과제 1.** 출고완료(30) 상태인데 매출전표가 없는 주문을 찾으세요. 결과 모양은 `ord_no, ord_dt, cust_nm, ord_amt`이며, 공통 샘플 기준 2행이 나와야 합니다.

:::answer 해설 보기
전표는 SRC_DOC_NO로 주문번호를 들고 있으므로 NOT EXISTS로 찾습니다. 주문금액은 상세에서 합산하되, 헤더와 상세의 grain이 다르므로 상세를 먼저 집계하거나 GROUP BY를 헤더 컬럼으로 묶습니다.

```sql
SELECT o.ord_no, o.ord_dt, c.cust_nm, SUM(d.ord_amt) AS ord_amt
  FROM erp.tb_ord o
  JOIN erp.tb_cust c    ON c.cust_no = o.cust_no
  JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
 WHERE o.ord_stat_cd = '30'
   AND NOT EXISTS (SELECT 1 FROM erp.tb_slip sl WHERE sl.src_doc_no = o.ord_no)
 GROUP BY o.ord_no, o.ord_dt, c.cust_nm
 ORDER BY o.ord_no;
```

결과는 SO2026030002 청솔내과의원 60,000원, SO2026030003 바른팜유통 2,160,000원입니다. 실무라면 이 목록을 들고 "월말 일괄 발행인지, 누락인지"를 ERP 팀에 확인합니다.
:::

**과제 2.** 리콜 상황을 가정해 로트 L260105가 언제 만들어지고, 언제 입고되고, 어느 거래처로 얼마나 출고됐는지 시간순으로 보여 주세요. 결과 모양은 `event_dt, event_tp, doc_no, qty, cust_nm`입니다(생산·입고는 cust_nm이 비어 있음).

:::answer 해설 보기
서로 다른 흐름의 테이블을 같은 모양으로 맞춰 UNION ALL 하는 "이벤트 타임라인"입니다. 로트번호가 생산·입고·출고를 꿰는 공통 키라는 점을 확인하는 과제입니다.

```sql
SELECT p.prod_dt AS event_dt, 'PROD' AS event_tp, p.wo_no AS doc_no, p.good_qty AS qty, NULL AS cust_nm
  FROM erp.tb_prod_rslt p
 WHERE p.lot_no = 'L260105'
UNION ALL
SELECT r.rcv_dt, 'RCV', r.rcv_no, rd.rcv_qty, NULL
  FROM erp.tb_rcv r JOIN erp.tb_rcv_dtl rd ON rd.rcv_no = r.rcv_no
 WHERE rd.lot_no = 'L260105'
UNION ALL
SELECT s.ship_dt, 'SHIP', s.ship_no, sd.ship_qty, c.cust_nm
  FROM erp.tb_ship s
  JOIN erp.tb_ship_dtl sd ON sd.ship_no = s.ship_no
  JOIN erp.tb_ord o       ON o.ord_no = s.ord_no
  JOIN erp.tb_cust c      ON c.cust_no = o.cust_no
 WHERE sd.lot_no = 'L260105'
 ORDER BY event_dt;
```

결과는 2026-01-05 PROD WO2026010001 2,000 → 2026-01-08 RCV RC2026010001 2,000 → 2026-03-11 SHIP SH2026030003 100 바른팜유통입니다. 제약 업계에서 로트 추적이 중요한 이유가 이 한 장에 보입니다. DW에서도 로트 차원을 버리지 말아야 하는 근거가 됩니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 원천 시스템 분석서 | 흐름별 단계, 원천 테이블, 한 행의 의미(grain), 연결 키와 연결 방식(FK·값 규칙·추정), 확인 상태. |
| 요구사항정의서 | "매출"의 기준 문서(주문·출고·전표)와 기준일자, 부가세 포함 여부. |
| 인터뷰 질문지 / 회의록 | ERP 운영팀 질문 목록과 답변, 답변자와 일자. 답이 바뀌면 이력으로 남깁니다. |
| 매핑정의서 | 원천 테이블·컬럼 → DW 컬럼, 조인 조건, 필터(취소 제외 등), 증분 기준 컬럼. |
| 데이터 프로파일링 결과서 | 상태코드 분포, 연결 컬럼 매칭률, 정의서에 없는 코드값, 수불·스냅샷 차이. |
| 이슈·리스크 관리대장 | "발주-입고 연결 키 없음", "TB_ORD_DTL 수정일시 없음" 같은 원천 제약과 대응 방안, 담당자. |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 4 "Inventory", Chapter 5 "Procurement", Chapter 6 "Order Management", Chapter 7 "Accounting": 업무 프로세스별로 원천을 읽고 팩트를 정하는 방식.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 데이터 요건 분석 영역: 현행 시스템 분석과 요건 수집.
- PostgreSQL 공식 문서 — System Catalogs의 `pg_constraint`, The Information Schema.
