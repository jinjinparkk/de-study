# Day 21. 업무별 케이스 실습

## 오늘의 한 줄

업무가 달라도 차원 모델링의 순서는 같습니다. 프로세스 → grain → 차원 → 팩트, 그리고 **원천을 대사해 보는 것**입니다. 오늘은 주문관리·재고·구매·회계(총계정원장) 네 케이스를 같은 순서로 설계하고, 그 결과를 그룹 버스 매트릭스 한 장으로 묶습니다.

## 왜 중요한가

Week 3에서 배운 기법은 하나씩 보면 쉽지만, 실제 프로젝트에서는 "재고는 스냅샷인가 트랜잭션인가", "구매는 발주와 입고를 한 팩트로 둘까", "전표는 헤더인가 상세인가"를 한 번에 결정해야 합니다. 또 설계가 끝나기 전에 원천 데이터를 대사해 보지 않으면, 기초재고가 없다거나 입고에 발주번호가 없다는 사실을 테스트 단계에서야 알게 됩니다. 케이스마다 **설계 결정 + 대사 쿼리 한 개**를 세트로 만드는 습관이 오늘의 목표입니다.

## 핵심 개념

### 1. 주문관리: 파이프라인은 팩트 여러 개로

주문 → 출고 → 매출 → 수금은 한 흐름이지만 grain이 모두 다릅니다(주문상세, 출고상세·로트, 전표, 수금 건). 그래서 단계별 트랜잭션 팩트를 따로 두고, 진행 상태는 누적 스냅샷(Day 17)으로 모읍니다. 공통 DW의 FCT_ORD_LINE, FCT_SHIP_LINE이 여기에 해당하며 Day 16~20에서 충분히 다뤘습니다.

### 2. 재고: 스냅샷과 수불 트랜잭션을 함께

재고는 두 개의 팩트가 짝을 이룹니다. "그 시점에 얼마나 있나"는 주기 스냅샷(FCT_INV_DAILY), "왜 바뀌었나"는 입고(+)·출고(-)를 한 grain으로 모은 **재고 수불 트랜잭션 팩트**입니다. 두 팩트는 "기초 + 수불 합계 = 기말"로 서로를 검증합니다. 이 식이 맞지 않으면 원천 누락이나 기초재고 이관 누락입니다.

### 3. 구매: 발주와 입고는 다른 사건

발주(약속)와 입고(실물 도착)는 일자·수량·건수가 다릅니다. 분할 입고, 발주 없는 긴급 입고가 있으므로 한 팩트로 합치지 않고 발주상세 팩트와 입고상세 팩트를 따로 둔 뒤, 발주 대비 입고율은 drill-across나 누적 스냅샷으로 봅니다. 이때 **입고가 어느 발주상세에서 왔는지** 원천에 연결 키가 있어야 합니다.

### 4. 회계(총계정원장): grain은 전표상세, 잔액은 스냅샷

총계정원장 팩트의 grain은 전표상세(전표 × 순번 × 계정) 한 줄입니다. 차변·대변 금액은 가산이고, 재무상태표 계정(외상매출금, 부가세예수금 등)의 잔액은 반가산입니다(Day 17의 재고와 같은 수위). 손익 계정(제품매출 등)은 기간 발생액이라 월끼리 더해 회계연도 누계를 만듭니다. 그래서 전표상세 트랜잭션 팩트와 월말 계정잔액 스냅샷을 짝으로 둡니다. 전표마다 차변 합 = 대변 합이라는 회계 항등식이 가장 강력한 적재 검증입니다.

### 5. 그룹 버스 매트릭스: 계열사를 한 장에

케이스별 설계가 끝나면 모든 팩트를 행으로, 공통 차원을 열로 놓습니다. 같은 열에 체크가 여러 계열사에서 나오면 그 차원은 그룹 MDM(Day 13) 대상이고, 한 계열사에만 있는 차원(한빛건설 현장)은 그 계열사 범위로 둡니다.

## 예시

### 케이스 1. 주문관리: 설계 요약

| 팩트 | 유형 | grain | 차원 | 측정값 |
|---|---|---|---|---|
| FCT_ORD_LINE | 트랜잭션 | 주문상세 | 주문일, 거래처(SCD2), 품목, 사원 | 주문수량, 주문금액, 단가(비가산) |
| FCT_SHIP_LINE | 트랜잭션 | 출고상세(로트) | 출고일, 주문일, 거래처, 품목, 창고, 로트 | 출고수량, 출고금액 |
| 주문상세 진행 | 누적 스냅샷 | 주문상세 | 주문일, 출고일, 매출일, 수금일 | 단계별 수량, 소요일 |

결정 포인트는 Day 19의 실적 귀속(당시 담당)과 Day 20의 헤더 할인 배분입니다. 둘 다 영업기획의 결정이 필요한 항목이므로 요구사항정의서의 "결정 필요" 목록에 올립니다.

### 케이스 2. 재고: 수불 트랜잭션 팩트와 대사

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

-- 재고수불팩트: 일자 × 창고 × 품목 × 로트 × 수불유형, 수량은 부호 있음 (입고 +, 출고 -)
CREATE TABLE lab.fct_inv_txn AS
SELECT TO_CHAR(r.rcv_dt, 'YYYYMMDD')::INT AS txn_dt_sk, w.wh_sk, i.item_sk, l.lot_sk,
       CASE r.rcv_tp_cd WHEN '01' THEN 'RCV_PO' ELSE 'RCV_PROD' END AS txn_tp_cd,
       r.rcv_no AS src_doc_no, d.rcv_qty AS txn_qty
  FROM erp.tb_rcv r
  JOIN erp.tb_rcv_dtl d ON d.rcv_no = r.rcv_no
  JOIN dw.dim_wh w      ON w.wh_cd = r.wh_cd
  JOIN dw.dim_item i    ON i.item_cd = d.item_cd
  JOIN dw.dim_lot l     ON l.lot_no = d.lot_no
UNION ALL
SELECT f.ship_dt_sk, f.wh_sk, f.item_sk, f.lot_sk, 'SHIP', f.ship_no, -f.ship_qty
  FROM dw.fct_ship_line f;

-- 수불 대사: 3월 31일 스냅샷 vs 수불 누계 (차이 = 기초재고가 원천에 없음)
SELECT l.lot_no, i.item_cd, s.inv_qty AS snap_qty, COALESCE(t.net_qty, 0) AS txn_net_qty,
       s.inv_qty - COALESCE(t.net_qty, 0) AS diff_qty
  FROM dw.fct_inv_daily s
  JOIN dw.dim_lot l  ON l.lot_sk = s.lot_sk
  JOIN dw.dim_item i ON i.item_sk = s.item_sk
  LEFT JOIN (SELECT wh_sk, lot_sk, SUM(txn_qty) AS net_qty
               FROM lab.fct_inv_txn WHERE txn_dt_sk <= 20260331
              GROUP BY wh_sk, lot_sk) t
         ON t.wh_sk = s.wh_sk AND t.lot_sk = s.lot_sk
 WHERE s.inv_dt_sk = 20260331
 ORDER BY l.lot_no;
```

| lot_no | item_cd | 스냅샷 | 수불 누계 | 차이 |
|---|---|---|---|---|
| L250620 | P10003 | 480 | -20 | 500 |
| L250901 | P10001 | 0 | -210 | 210 |
| L251110 | P10002 | 395 | -105 | 500 |
| L260105 | P10001 | 1,900 | 1,900 | 0 |
| R260201 | R20001 | 500 | 500 | 0 |

2026년에 입고된 두 로트는 정확히 맞고, 2025년에 만든 세 로트는 입고 기록이 원천에 없어 차이가 납니다. 이 차이가 곧 **기초재고**입니다. DW 오픈 시점의 기초재고를 이관 기준일 스냅샷으로 한 번 받아 수불 팩트에 "기초(OPEN)" 유형으로 넣어야 수불 대사가 0이 됩니다. Day 2에서 "기초재고를 확보해야 한다"고 한 이유가 숫자로 보입니다.

### 케이스 3. 구매: 발주와 입고, 그리고 끊어진 연결

```sql
CREATE TABLE lab.dim_vndr AS                       -- 구매처차원 (Type 1)
SELECT ROW_NUMBER() OVER (ORDER BY vndr_no)::INT AS vndr_sk, vndr_no, vndr_nm FROM erp.tb_vndr
UNION ALL SELECT -1, '-1', '알 수 없음';

CREATE TABLE lab.fct_po_line AS                    -- 발주상세팩트: grain = 발주상세
SELECT TO_CHAR(p.po_dt, 'YYYYMMDD')::INT AS po_dt_sk, v.vndr_sk, i.item_sk, p.co_cd,
       p.po_no, d.po_seq, d.po_qty, d.uprc, d.po_qty * d.uprc AS po_amt
  FROM erp.tb_po p
  JOIN erp.tb_po_dtl d  ON d.po_no = p.po_no
  JOIN lab.dim_vndr v   ON v.vndr_no = p.vndr_no
  JOIN dw.dim_item i    ON i.item_cd = d.item_cd;

-- 발주 대비 입고: 원천에 발주번호가 없어 구매처 + 품목으로 "추정" 매칭할 수밖에 없음
SELECT f.po_no, f.po_seq, f.po_qty, f.co_cd AS po_co_cd,
       r.rcv_no, rd.rcv_qty, w.co_cd AS rcv_wh_co_cd, 'VNDR+ITEM 추정' AS match_rule
  FROM lab.fct_po_line f
  JOIN lab.dim_vndr v   ON v.vndr_sk = f.vndr_sk
  JOIN dw.dim_item i    ON i.item_sk = f.item_sk
  LEFT JOIN erp.tb_rcv r      ON r.vndr_no = v.vndr_no AND r.rcv_tp_cd = '01'
  LEFT JOIN erp.tb_rcv_dtl rd ON rd.rcv_no = r.rcv_no AND rd.item_cd = i.item_cd
  LEFT JOIN erp.tb_wh w       ON w.wh_cd = r.wh_cd;
```

PO2026010001(R20001 500 KG)이 RC2026020001(500 KG)과 붙었지만, 이것은 구매처와 품목이 같다는 **추정**입니다. 같은 구매처에서 같은 원료를 두 번 발주하면 어느 입고가 어느 발주인지 알 수 없습니다. 게다가 발주 회사는 4000(한빛케미칼)인데 입고 창고는 2000(한빛로지스) 소속입니다. 둘 다 Day 2에서 본 원천 빈틈입니다. 설계 결론은 "입고상세에 발주번호·발주순번 추가를 ERP 팀에 요구, 그 전까지 발주-입고 매칭 지표는 1차 범위에서 제외"입니다. 추정 매칭으로 대시보드를 먼저 열면 나중에 숫자가 바뀌어 신뢰를 잃습니다.

### 케이스 4. 회계: 총계정원장 팩트와 차대 균형

```sql
CREATE TABLE lab.dim_acct AS                       -- 계정차원
SELECT ROW_NUMBER() OVER (ORDER BY acct_cd)::INT AS acct_sk, acct_cd, acct_nm,
       CASE LEFT(acct_cd, 1) WHEN '1' THEN '자산' WHEN '2' THEN '부채' WHEN '4' THEN '수익' ELSE '기타' END AS acct_cls_nm
  FROM erp.tb_acct;

CREATE TABLE lab.fct_gl_line AS                    -- 총계정원장팩트: grain = 전표상세
SELECT TO_CHAR(s.slip_dt, 'YYYYMMDD')::INT AS slip_dt_sk, s.co_cd, a.acct_sk,
       s.slip_no, d.slip_seq, s.src_doc_no, d.dr_amt, d.cr_amt
  FROM erp.tb_slip s
  JOIN erp.tb_slip_dtl d ON d.slip_no = s.slip_no
  JOIN lab.dim_acct a    ON a.acct_cd = d.acct_cd;

-- 적재 검증 1: 전표별 차변 합 = 대변 합 (불일치 0행이어야 정상)
SELECT slip_no, SUM(dr_amt) AS dr_sum, SUM(cr_amt) AS cr_sum
  FROM lab.fct_gl_line GROUP BY slip_no HAVING SUM(dr_amt) <> SUM(cr_amt);

-- 계정별 3월 발생액과 월말 잔액 (재무상태표 계정 잔액 = 반가산: 월끼리 더하지 않음)
SELECT a.acct_cd, a.acct_nm, a.acct_cls_nm,
       SUM(f.dr_amt) AS dr_amt, SUM(f.cr_amt) AS cr_amt,
       CASE WHEN a.acct_cls_nm = '자산' THEN SUM(f.dr_amt - f.cr_amt)
            ELSE SUM(f.cr_amt - f.dr_amt) END AS mm_end_bal_amt
  FROM lab.fct_gl_line f JOIN lab.dim_acct a ON a.acct_sk = f.acct_sk
 WHERE f.slip_dt_sk BETWEEN 20260301 AND 20260331
 GROUP BY a.acct_cd, a.acct_nm, a.acct_cls_nm
 ORDER BY a.acct_cd;
```

차대 불일치는 0건입니다. 3월 외상매출금 차변 90,200원, 제품매출 대변 82,000원, 부가세예수금 대변 8,200원입니다. 여기서 월말 잔액은 기초잔액이 없다고 가정한 3월 발생분일 뿐입니다. 실제 계정잔액 스냅샷은 이관 기준일의 시산표 잔액을 기초로 받아야 하며, 이것도 재고의 기초재고와 같은 문제입니다.

영업 쪽과 맞춰 보면 하나 더 보입니다. 제품매출 82,000원은 SO2026030001의 주문금액(32,000 + 50,000)과 같지만, 3월에 출고된 나머지 두 주문(2,220,000원)은 전표가 없습니다. "영업실적(출고 기준) ≠ 회계 매출"이 대시보드 오픈 첫날 나올 질문이므로, 두 숫자의 차이를 설명하는 대사 리포트를 미리 준비합니다.

### 그룹 버스 매트릭스

| 계열사 | 업무 프로세스 (팩트) | 날짜 | 회사 | 거래처 | 품목 | 사원 | 창고 | 로트 | 구매처 | 계정 | 현장 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 한빛제약 | 주문 | O | O | O | O | O | | | | | |
| 한빛제약 | 영업목표 (월) | O | O | | | O | | | | | |
| 한빛로지스 | 출고 | O | O | O | O | | O | O | | | |
| 한빛로지스 | 일별재고 | O | O | | O | | O | O | | | |
| 한빛로지스 | 재고수불 | O | O | | O | | O | O | O | | |
| 한빛푸드 | 대리점 주문 | O | O | O | O | O | | | | | |
| 한빛케미칼 | 발주 | O | O | | O | | | | O | | |
| 한빛케미칼 | 생산실적 | O | O | | O | | | O | | | |
| 한빛건설 | 현장 원가 | O | O | | O | | | | O | O | O |
| 전 계열사 | 총계정원장 | O | O | | | | | | | O | |

이 표에서 읽는 결정은 세 가지입니다. 날짜·회사는 모든 행에 있으므로 그룹 단일 차원으로 먼저 확정합니다. 품목은 8개 행에 걸쳐 있고 계열사마다 코드 체계가 다르므로 그룹 품목 MDM(Day 13)이 2차 범위의 선행 조건입니다. 현장 차원은 한빛건설에만 있으므로 그룹 공통 차원으로 만들지 않고 계열사 차원으로 둡니다.

## Before / After

| 케이스 | Before | After |
|---|---|---|
| 재고 | 스냅샷만 적재, 기초재고 확인 안 함 | 스냅샷 + 수불 팩트, "기초 + 수불 = 기말" 대사, 기초재고 이관을 이행 계획에 포함 |
| 구매 | 발주·입고를 구매처 + 품목으로 묶은 한 팩트 | 발주상세·입고상세 팩트 분리, 연결 키 추가 요구, 그 전엔 매칭 지표 제외 |
| 회계 | 전표 헤더에 합계금액만 적재 | 전표상세 grain, 차대 균형 검증, 월말 잔액 스냅샷 (기초잔액 이관) |
| 범위 | 계열사별로 따로 설계 | 그룹 버스 매트릭스로 공통 차원과 계열사 고유 차원을 먼저 구분 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 재고 원천 | WMS가 일 마감 스냅샷을 주면 스냅샷을 정본으로, 수불은 검증용 | 수불만 주면 기초재고 + 수불로 스냅샷 생성, 대사 기준을 WMS 재고 조회 화면으로 |
| 발주-입고 연결 | 원천에 연결 키가 있으면 누적 스냅샷(발주 → 입고 → 검수)까지 | 연결 키가 없으면 지표를 보류하고 원천 개선을 요구. 추정 매칭은 분석용으로만 표시 |
| 회계 grain | 기본은 전표상세 | 원장 조회 성능이 문제면 계정 × 월 잔액 스냅샷을 추가. 상세를 버리지 않음 |
| 영업 vs 회계 매출 | 두 숫자를 다른 이름(출고실적, 회계매출)으로 두고 차이 리포트 제공 | 하나로 통일하라는 요구가 오면 "기준 프로세스가 다르다"를 근거로 정의를 먼저 합의 |
| 계열사 고유 차원 | 한 계열사만 쓰면 계열사 차원 | 두 계열사 이상이 쓰기 시작하면 공통 차원으로 승격하고 버스 매트릭스 갱신 |

## 흔한 실수 3가지

1. **수불 대사를 하지 않고 재고 마트를 여는 실수.** 기초재고가 빠진 수불로 재고를 계산하면 마이너스 재고가 나옵니다. 오픈 전에 "기초 + 수불 = 기말"을 로트 단위로 맞춰 봅니다.
2. **추정 매칭을 정식 지표로 내보내는 실수.** 구매처 + 품목 매칭으로 "발주 대비 입고율"을 공개하면 연결 키가 생긴 뒤 숫자가 바뀌고 신뢰가 떨어집니다. 추정은 추정이라고 표시하거나 보류합니다.
3. **회계 매출과 영업 실적을 같은 이름으로 부르는 실수.** 기준 프로세스(전표 vs 출고)가 다르면 숫자가 다른 것이 정상입니다. 이름을 나누고 차이 리포트를 함께 제공합니다.

## 셀프 체크 질문

**Q1. 재고 DW를 설계할 때 스냅샷 팩트와 수불 트랜잭션 팩트를 둘 다 두는 이유는 무엇입니까?**

:::answer 모범 답안 보기
답하는 질문이 다르고 서로를 검증하기 때문입니다. 스냅샷은 "그 시점에 얼마나 있나"(결품, 유효기한 임박, 월말 재고)에, 수불 팩트는 "왜 바뀌었나"(입고·출고·조정 유형별 흐름, 회전율)에 답합니다. 그리고 "기초 + 수불 합계 = 기말"이라는 식으로 두 팩트가 서로를 대사합니다. 공통 샘플에서도 이 대사로 2025년 로트 세 개의 기초재고가 원천에 없다는 것을 찾았습니다. 하나만 두면 이런 누락을 발견할 수단이 없습니다.
:::

**Q2. 입고상세에 발주번호가 없습니다. 구매 마트의 "발주 대비 입고율"을 어떻게 하겠습니까?**

:::answer 모범 답안 보기
정식 지표로는 보류하고, ERP 팀에 입고상세의 발주번호·발주순번 추가를 요구사항으로 올립니다. 구매처 + 품목으로 묶는 추정 매칭은 같은 구매처의 같은 품목 발주가 두 건 이상이면 틀리고, 분할 입고도 구분하지 못합니다. 현업이 당장 필요하다고 하면 "추정"임을 화면에 표시한 분석용 리포트로만 제공하고, 연결 키가 생기면 숫자가 바뀔 수 있다는 점을 사전에 알립니다. 같은 이유로 발주 회사(4000)와 입고 창고 회사(2000)가 다른 구조도 업무 흐름(그룹 물류 대행)인지 데이터 오류인지 확인합니다.
:::

**Q3. 그룹 버스 매트릭스를 보고 2차 범위의 선행 과제를 무엇으로 정하겠습니까?**

:::answer 모범 답안 보기
가장 많은 행에 걸쳐 있으면서 계열사마다 코드가 다른 차원이 선행 과제입니다. 날짜·회사는 그룹 단일 기준을 바로 정할 수 있으므로 1차에서 확정하고, 품목은 제약·푸드·케미칼·건설이 모두 쓰지만 코드 체계가 계열사별이므로 그룹 품목 MDM과 매핑 테이블이 2차의 선행 조건입니다. 거래처도 제약·로지스·푸드가 공유하므로 같은 대상입니다. 반대로 현장처럼 한 계열사만 쓰는 차원은 공통화하지 않고 계열사 범위로 둡니다. 이 판단을 버스 매트릭스에 차원별 오너와 함께 적어 경영지원실과 합의합니다.
:::

## 오늘의 과제

**과제 1.** 재고 수불 팩트에 기초재고를 넣어 대사를 0으로 만드세요. 2026년 1월 1일자로 "OPEN" 유형 행을 차이만큼 넣은 뒤 대사 쿼리를 다시 돌립니다. 결과 모양은 `lot_no, snap_qty, txn_net_qty, diff_qty` 5행이며 모든 diff_qty가 0이어야 합니다.

:::answer 해설 보기
실무에서는 기초재고를 차이에서 역산하지 않고 이관 기준일의 WMS 재고를 받아 넣습니다. 여기서는 학습용으로 대사 차이를 기초재고로 씁니다. 수불 팩트의 유형 코드(OPEN, RCV_PO, RCV_PROD, SHIP)를 Junk 차원이나 수불유형 차원으로 관리하면 유형별 흐름 분석이 쉬워집니다.

```sql
INSERT INTO lab.fct_inv_txn (txn_dt_sk, wh_sk, item_sk, lot_sk, txn_tp_cd, src_doc_no, txn_qty)
SELECT 20260101, s.wh_sk, s.item_sk, s.lot_sk, 'OPEN', 'MIGRATION',
       s.inv_qty - COALESCE((SELECT SUM(t.txn_qty) FROM lab.fct_inv_txn t
                              WHERE t.wh_sk = s.wh_sk AND t.lot_sk = s.lot_sk AND t.txn_dt_sk <= 20260331), 0)
  FROM dw.fct_inv_daily s
 WHERE s.inv_dt_sk = 20260331
   AND s.inv_qty <> COALESCE((SELECT SUM(t.txn_qty) FROM lab.fct_inv_txn t
                               WHERE t.wh_sk = s.wh_sk AND t.lot_sk = s.lot_sk AND t.txn_dt_sk <= 20260331), 0);

SELECT l.lot_no, s.inv_qty AS snap_qty, t.net_qty AS txn_net_qty, s.inv_qty - t.net_qty AS diff_qty
  FROM dw.fct_inv_daily s
  JOIN dw.dim_lot l ON l.lot_sk = s.lot_sk
  JOIN (SELECT wh_sk, lot_sk, SUM(txn_qty) AS net_qty FROM lab.fct_inv_txn
         WHERE txn_dt_sk <= 20260331 GROUP BY wh_sk, lot_sk) t
    ON t.wh_sk = s.wh_sk AND t.lot_sk = s.lot_sk
 WHERE s.inv_dt_sk = 20260331
 ORDER BY l.lot_no;
```

L250620 500, L250901 210, L251110 500의 기초 행 3개가 들어가고 다섯 로트 모두 차이 0입니다.
:::

**과제 2.** 영업 출고실적과 회계 매출의 차이 리포트를 만드세요. 3월 출고된 주문별로 출고금액(FCT_SHIP_LINE)과 매출전표 금액(제품매출 대변, 전표의 SRC_DOC_NO = 주문번호)을 나란히 보여 줍니다. 결과 모양은 `ord_no, ship_amt, gl_sales_amt, diff_amt` 3행입니다.

:::answer 해설 보기
출고는 출고상세 grain, 전표는 전표상세 grain이므로 둘 다 주문번호 수준으로 먼저 접은 뒤 붙입니다. 전표가 없는 주문은 LEFT JOIN으로 0이 나오며 이 행들이 "전표 누락 또는 미발행" 확인 대상입니다.

```sql
WITH s AS (
  SELECT ord_no, SUM(ship_amt) AS ship_amt FROM dw.fct_ship_line
   WHERE ship_dt_sk BETWEEN 20260301 AND 20260331 GROUP BY ord_no
), g AS (
  SELECT f.src_doc_no AS ord_no, SUM(f.cr_amt) AS gl_sales_amt
    FROM lab.fct_gl_line f JOIN lab.dim_acct a ON a.acct_sk = f.acct_sk
   WHERE a.acct_cd = '41100' GROUP BY f.src_doc_no
)
SELECT s.ord_no, s.ship_amt, COALESCE(g.gl_sales_amt, 0) AS gl_sales_amt,
       s.ship_amt - COALESCE(g.gl_sales_amt, 0) AS diff_amt
  FROM s LEFT JOIN g ON g.ord_no = s.ord_no
 ORDER BY s.ord_no;
```

SO2026030001은 82,000 / 82,000으로 차이 0, SO2026030002(60,000)와 SO2026030003(2,160,000)은 전표가 없어 차이가 전액입니다. SRC_DOC_NO에 문서유형이 없어 주문번호인지 다른 문서번호인지 구분할 수 없다는 원천 빈틈(Day 2)도 이 리포트의 주석으로 남깁니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 그룹 버스 매트릭스 | 계열사 × 프로세스 × 공통 차원, 차수, 차원 오너, 계열사 고유 차원 표시 |
| 차원 모델 설계서 | 케이스별 팩트 유형·grain·차원·측정값·가산성 |
| 요구사항정의서 | 원천 개선 요구(입고상세 발주번호, 전표 원천문서유형), 영업실적과 회계매출의 정의 |
| 이행 계획서 | 기초재고·기초잔액 이관 기준일, 이관 방법, 대사 기준 |
| 테스트 시나리오 | 수불 대사, 차대 균형, 출고실적 vs 회계매출 차이 리포트 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 4 "Inventory", Chapter 5 "Procurement", Chapter 6 "Order Management", Chapter 7 "Accounting"(총계정원장 팩트, 기간 잔액 스냅샷).
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드"(DAP·DAsP 공통 교재) — 데이터 모델링 과목.
