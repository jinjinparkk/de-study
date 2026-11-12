# Day 30. 종합 케이스 스터디

## 오늘의 한 줄

"제약사 영업실적 대시보드"를 처음부터 끝까지 따라가 보면, 29일 동안 배운 것은 결국 한 줄입니다. **현업의 결정에서 grain과 지표 정의를 끌어내고, 그 정의가 원천에서 화면까지 같은 숫자로 흐르게 만들고, 흐르는지 매일 증명한다.** 오늘은 각 단계에서 어떤 Day의 판단을 꺼내 쓰는지 연결합니다.

## 왜 중요한가

개별 기법을 다 알아도 프로젝트는 연결부에서 깨집니다. 요구사항에서 정한 "취소 제외"가 매핑정의서에 없고, 매핑정의서의 -1 규칙이 대사 쿼리에 반영되지 않고, 마트의 정의와 DAX 측정값이 다릅니다. 시니어에게 기대하는 것은 기법 하나가 아니라 **끝에서 끝까지 한 숫자를 책임지는 설계**입니다. 면접과 설계 리뷰에서도 질문은 늘 "그래서 그 숫자가 맞다는 걸 어떻게 보장합니까?"로 끝납니다.

## 핵심 개념

### 1. 요구사항 → grain과 지표 정의 (Day 3, 16, 19, 29)

정 과장의 문장 "영업사원별로 목표 대비 실적을 매일 아침 보고 싶다"를 인터뷰(Day 29)로 풀면 결정이 다섯 개 나옵니다. 매출 시점(주문일, 출고일은 보조), 취소 제외, 실적 귀속(주문을 받은 사원, 거래처 담당은 Type 2로 별도, Day 19), 목표 grain(월 × 사원, Day 18), 신선도(D+1 07:00, Day 24). 이 결정이 곧 grain 선언(Day 16)과 지표 사전(Day 26)입니다.

### 2. 아키텍처 (Day 15, 22, 27, 28)

레이어는 STG(원본 보관) → DW(공통 차원·팩트) → DM/BI 뷰 → Power BI 시맨틱 모델입니다(Day 15). 적재는 ELT(ADR-001), BI 모델은 스타(ADR-002)로 결정하고 근거를 ADR로 남깁니다(Day 28). 클라우드 이관을 염두에 두면 Oracle의 빈 문자열·DATE 차이를 STG → DW 변환에서 처리합니다(Day 27).

### 3. 차원 모델 (Day 16~21)

버스 매트릭스에서 주문·영업목표·출고가 날짜·거래처·품목·사원을 공유합니다(Day 18·21). FCT_ORD_LINE은 주문상세 grain, 영업목표는 월 × 사원 grain이라 직접 조인하지 않고 공통 차원으로 각각 집계해 붙입니다(drill-across). 거래처는 담당 사원 Type 2, 거래처명 Type 1(Day 19), 헤더 할인은 라인 배분(Day 20)입니다.

### 4. 적재와 운영 (Day 22~25)

주문은 워터마크 + MERGE + 삭제 감지로 멱등하게(Day 22), 차원 조회 실패는 -1 + 경고, 측정값 오류는 거부(Day 23), 배치는 데이터 의존성과 SLA 역산 시간대로(Day 24), 마트·BI 쿼리는 파티션 키 직접 조건과 월 집계로(Day 25) 설계합니다.

### 5. 품질 검증과 BI 마트 (Day 12, 26)

"맞다"는 매일 쿼리로 증명합니다. ERP 대비 월 금액 대사, -1 건수, SCD 현재 행 1개, 목표 대상 사원 존재 여부를 품질 게이트로 두고(Day 12), 통과해야 Power BI를 갱신합니다. 마트는 지표 규칙을 고정한 뷰와 공통 측정값으로 제공하고, SQL 기준 숫자로 화면을 검수합니다(Day 26).

## 예시

### 전체 흐름

```text
 [요구사항]  정 과장 인터뷰 → 지표 사전, grain 선언, NFR      Day 29, 16
     |
 [원천]  HBP_ERP TB_ORD / TB_ORD_DTL / TB_CUST_EMP_HIST       Day 2
     |   워터마크 + MERGE + 삭제 감지                          Day 22
 [STG]   원본 보관, 빈 문자열·DATE 정제                        Day 27
     |   SK 조회, -1, 오류 테이블                              Day 23
 [DW]    DIM_DATE·CUST(SCD2)·ITEM·EMP + FCT_ORD_LINE           Day 18, 19
     |   영업목표 FCT_SALES_TGT (월 × 사원)
 [DM]    DM_SALES_MM_EMP (월 × 사원 실적·목표)                 Day 20, 25
     |   품질 게이트 통과 시에만                               Day 12, 24
 [BI]    Power BI 스타 모델, 공통 측정값                       Day 26
```

### 영업 마트: 월 × 사원 실적과 목표

```sql
CREATE SCHEMA IF NOT EXISTS lab;

CREATE TABLE lab.fct_sales_tgt (            -- 영업목표팩트 (Day 18 값, 가상): 연월 × 사원
  yyyymm  CHAR(6)     NOT NULL,
  emp_sk  INTEGER     NOT NULL,
  tgt_amt NUMERIC(15) NOT NULL,
  PRIMARY KEY (yyyymm, emp_sk)
);
INSERT INTO lab.fct_sales_tgt
SELECT '202603', e.emp_sk, v.tgt_amt
  FROM (VALUES ('E1001', 100000), ('E1002', 150000), ('E1003', 2000000), ('E1004', 50000)) AS v (emp_no, tgt_amt)
  JOIN dw.dim_emp e ON e.emp_no = v.emp_no;

CREATE TABLE lab.dm_sales_mm_emp (          -- 영업실적마트: grain = 연월 × 사원
  yyyymm    CHAR(6)     NOT NULL,
  emp_sk    INTEGER     NOT NULL,
  emp_nm    VARCHAR(50) NOT NULL,
  dept_nm   VARCHAR(50) NOT NULL,
  sales_amt NUMERIC(15) NOT NULL,           -- 매출금액: 취소(90) 제외 주문금액, 주문일 기준, 받은 사원 귀속
  ord_cnt   INTEGER     NOT NULL,           -- 주문건수: 취소 제외 주문번호 수 (월·사원 수준 전용, 더하지 않음)
  tgt_amt   NUMERIC(15),                    -- 목표금액 (없으면 NULL)
  achv_rt   NUMERIC(6,1),                   -- 달성률(%) = 매출 ÷ 목표
  batch_id  VARCHAR(20) NOT NULL,
  load_dtm  TIMESTAMP   NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (yyyymm, emp_sk)
);

-- drill-across: 실적과 목표를 공통 차원(연월, 사원) 수준으로 각각 집계한 뒤 FULL OUTER JOIN
INSERT INTO lab.dm_sales_mm_emp (yyyymm, emp_sk, emp_nm, dept_nm, sales_amt, ord_cnt, tgt_amt, achv_rt, batch_id)
WITH act AS (
  SELECT d.yyyymm, f.emp_sk,
         SUM(CASE WHEN f.ord_stat_cd <> '90' THEN f.ord_amt ELSE 0 END) AS sales_amt,
         COUNT(DISTINCT CASE WHEN f.ord_stat_cd <> '90' THEN f.ord_no END) AS ord_cnt
    FROM dw.fct_ord_line f JOIN dw.dim_date d ON d.date_sk = f.ord_dt_sk
   GROUP BY d.yyyymm, f.emp_sk
), k AS (
  SELECT COALESCE(a.yyyymm, t.yyyymm) AS yyyymm, COALESCE(a.emp_sk, t.emp_sk) AS emp_sk,
         COALESCE(a.sales_amt, 0) AS sales_amt, COALESCE(a.ord_cnt, 0) AS ord_cnt, t.tgt_amt
    FROM act a FULL OUTER JOIN lab.fct_sales_tgt t ON t.yyyymm = a.yyyymm AND t.emp_sk = a.emp_sk
)
SELECT k.yyyymm, k.emp_sk, e.emp_nm, e.dept_nm, k.sales_amt, k.ord_cnt, k.tgt_amt,
       ROUND(100.0 * k.sales_amt / NULLIF(k.tgt_amt, 0), 1), 'B20260406'
  FROM k JOIN dw.dim_emp e ON e.emp_sk = k.emp_sk;

SELECT yyyymm, emp_nm, dept_nm, sales_amt, ord_cnt, tgt_amt, achv_rt
  FROM lab.dm_sales_mm_emp ORDER BY yyyymm, emp_nm;
```

| yyyymm | emp_nm | dept_nm | sales_amt | ord_cnt | tgt_amt | achv_rt |
|---|---|---|---|---|---|---|
| 202603 | 김도윤 | 서울1팀 | 60,000 | 1 | 100,000 | 60.0 |
| 202603 | 박지훈 | 경기팀 | 2,160,000 | 1 | 2,000,000 | 108.0 |
| 202603 | 이서연 | 서울1팀 | 146,000 | 2 | 150,000 | 97.3 |
| 202603 | 최하은 | 부산팀 | 0 | 0 | 50,000 | 0.0 |
| 202604 | 이서연 | 서울1팀 | 0 | 0 | | |
| 202604 | 최하은 | 부산팀 | 45,000 | 1 | | |

최하은의 3월 행은 목표 쪽에서만 왔습니다. INNER JOIN이었다면 "목표가 있는데 실적이 0인 사원"이 화면에서 사라졌을 것입니다. 4월 이서연 행은 취소 주문만 있어 매출 0입니다. 이 행을 보일지(주문 활동은 있었음) 숨길지는 지표 사전에 정해 둡니다.

### 품질 게이트: 통과해야 BI를 갱신한다

```sql
-- 모든 점검이 PASS 여야 Day 24의 BI_PBI_SALES 작업이 실행됨
WITH erp AS (                     -- 원천: ERP 주문, 취소 제외, 월별
  SELECT TO_CHAR(o.ord_dt, 'YYYYMM') AS yyyymm, SUM(d.ord_amt) AS amt
    FROM erp.tb_ord o JOIN erp.tb_ord_dtl d ON d.ord_no = o.ord_no
   WHERE o.ord_stat_cd <> '90'
   GROUP BY 1
), dm AS (
  SELECT yyyymm, SUM(sales_amt) AS amt FROM lab.dm_sales_mm_emp GROUP BY yyyymm
)
SELECT 'RECON_AMT' AS chk_cd, '원천 대비 월 매출 차이 합(절대값)' AS chk_nm,
       (SELECT COALESCE(SUM(ABS(COALESCE(erp.amt, 0) - COALESCE(dm.amt, 0))), 0)
          FROM erp FULL OUTER JOIN dm ON dm.yyyymm = erp.yyyymm) AS result_val
UNION ALL
SELECT 'UNKNOWN_SK', '주문 팩트 -1 행 수',
       (SELECT COUNT(*) FROM dw.fct_ord_line WHERE -1 IN (ord_dt_sk, cust_sk, item_sk, emp_sk))
UNION ALL
SELECT 'SCD_CURR', '현재 행이 1개가 아닌 거래처 수',
       (SELECT COUNT(*) FROM (SELECT cust_no FROM dw.dim_cust WHERE cust_sk <> -1
                               GROUP BY cust_no HAVING COUNT(*) FILTER (WHERE curr_yn = 'Y') <> 1) x)
UNION ALL
SELECT 'TGT_EMP', '사원 차원에 없는 목표 행 수',
       (SELECT COUNT(*) FROM lab.fct_sales_tgt t
         WHERE NOT EXISTS (SELECT 1 FROM dw.dim_emp e WHERE e.emp_sk = t.emp_sk));
```

네 점검 모두 0입니다. 게이트 결과는 배치 통제 테이블(Day 24)에 남기고, 0이 아니면 하류를 멈추고 알림을 보냅니다. RECON_AMT가 원천 기준으로 계산된다는 점이 중요합니다. 마트끼리, DW끼리만 비교하면 같은 버그를 공유한 두 숫자가 서로 맞는다고 나옵니다.

### 설계 결정 요약 (설계 리뷰 한 장)

| 영역 | 결정 | 근거 Day |
|---|---|---|
| 매출 정의 | 취소 제외 주문금액, 주문일 기준, 받은 사원 귀속. 출고일 기준은 보조 측정값 | 19, 26, 29 |
| grain | 팩트 = 주문상세, 마트 = 연월 × 사원, 목표 = 연월 × 사원 | 16, 18 |
| 이력 | 거래처 담당 Type 2(유효일 = 원천 업무 유효일), 거래처명 Type 1 | 7, 19 |
| 적재 | ELT, 워터마크 + 겹침 10분 + MERGE, 키 비교 삭제 감지, -1 + 오류 테이블 | 22, 23, 28 |
| 운영 | 데이터 의존성 DAG, D+1 07:00 SLA, 품질 게이트 후 BI 갱신 | 24 |
| 성능 | 팩트 월 파티션(파티션 키 직접 조건), 월 집계 마트 | 8, 25 |
| BI | Power BI Import, 스타 모델 단방향, 날짜 테이블 지정, 역할 날짜 비활성 관계 | 26 |
| 거버넌스 | 지표 오너 경영지원실, 거래처 마스터 오너 지정, 표준 용어·약어 적용 | 10, 11, 13 |

## Before / After

| 단계 | Before (기법만 있는 프로젝트) | After (끝에서 끝까지 한 숫자) |
|---|---|---|
| 요구사항 | "대시보드 만들어 주세요" | 결정 → grain·지표 정의·NFR, 범위 밖 명시 |
| 설계 | 테이블은 있는데 이유가 없음 | 버스 매트릭스, SCD 표, 매핑정의서, ADR |
| 적재 | INSERT, 실패하면 수작업 | 멱등 MERGE, -1·거부·재처리, 의존성 DAG |
| 검증 | 화면 눈으로 확인 | 원천 대사·품질 게이트·SQL 기준 숫자 검수 |
| BI | 리포트마다 다른 매출 | 공통 시맨틱 모델, 지표 사전 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 1차 범위 | 한 주제영역(영업실적)을 원천~화면까지 먼저 관통 | 여러 주제를 얇게 동시에 하면 연결부 위험이 늦게 드러남 |
| 정의 충돌 | 같은 이름의 다른 정의는 이름을 나눔(주문매출·출고매출) | 하나로 통일하라는 요구는 오너가 정의를 결정하게 하고 기록 |
| 품질 게이트 실패 | 금액 대사 실패는 BI 갱신 중단 + 전일 유지 표시 | -1 건수 같은 경고성 점검은 갱신하되 리포트에 "미확인 N건" 표시 (사전 합의) |
| 설계 리뷰 | 결정마다 근거 Day(원칙)와 현업 합의를 함께 제시 | 근거가 "관례"뿐이면 ADR로 다시 따져 봄 |

## 흔한 실수 3가지

1. **연결부를 아무도 소유하지 않는 실수.** 모델러·적재 개발자·BI 개발자가 각자 맞는데 숫자가 다릅니다. 아키텍트가 지표 사전 → 매핑정의서 → 측정값의 일치를 직접 점검합니다.
2. **DW끼리만 대사하는 실수.** 마트와 팩트가 같은 버그를 공유하면 둘은 항상 맞습니다. 대사는 원천 기준으로 합니다.
3. **목표 쪽 행을 잃는 실수.** 실적 기준 INNER JOIN은 "목표는 있는데 실적이 없는" 사람을 지웁니다. drill-across는 각각 집계 후 FULL OUTER JOIN입니다.

## 셀프 체크 질문

오늘은 시니어 데이터 아키텍트·엔지니어 면접에서 나올 만한 질문 10개로 셀프 체크를 대신합니다. 각 답은 2~3분 분량으로 말할 수 있게 연습합니다.

**Q1. 영업실적 팩트의 grain을 어떻게 정하고, grain을 잘못 정하면 어떤 일이 생깁니까?**

:::answer 모범 답안 보기
가장 낮은 수준의 업무 사건, 즉 주문상세 1행으로 정합니다. 그래야 품목·거래처·일자 어느 방향으로든 집계할 수 있고 나중에 요구가 늘어도 다시 적재하지 않습니다. grain이 섞이면(헤더 금액과 라인 금액을 한 팩트에) 조인 시 금액이 라인 수만큼 복제되는 fan-out이 생기고, 너무 높게 잡으면(월 × 사원만 적재) 품목별 분석 요청에 답할 수 없습니다. 목표처럼 grain이 다른 사실은 별도 팩트로 두고 공통 차원으로 drill-across 합니다(Day 16, 18, 20).
:::

**Q2. 담당 영업사원이 바뀌었을 때 지난 실적을 어떻게 보여 줄지 어떻게 결정하고 구현합니까?**

:::answer 모범 답안 보기
먼저 현업에게 실적 귀속 규칙을 묻습니다. 보통 당시 담당 기준이므로 거래처 차원의 담당 사원을 Type 2로 두고, 유효기간은 원천 이력의 업무 유효일로 잡아 팩트가 주문일자에 유효했던 SK를 갖게 합니다. 주문을 받은 사원은 팩트의 사원 FK로 따로 둡니다. 현재 담당 기준 추이도 필요하면 현재 담당 컬럼을 더해 Type 6으로 만듭니다. 적재는 "현재 행 닫기 + 새 버전 넣기"를 한 트랜잭션(또는 MERGE)으로 하고, 현재 행 1개·선분 겹침 0건을 매 배치 점검합니다(Day 7, 19).
:::

**Q3. ERP에서 DW로 증분 적재를 설계할 때 무엇을 보장해야 합니까?**

:::answer 모범 답안 보기
누락 없음, 중복 없음, 삭제 반영, 재실행 안전 네 가지입니다. 기준시각을 배치 시작 때 고정한 워터마크에 겹침 구간을 두고, 반영은 키 기준 MERGE로 값이 달라질 때만 갱신하며, 물리 삭제는 키 비교로 따로 감지해 소프트 삭제로 표시합니다. 워터마크 전진은 모든 단계와 같은 트랜잭션에서 합니다. 수정일시가 없는 상세 테이블은 헤더 변경에 묶어 교체하고 주기적 해시 비교로 보완합니다. 마지막으로 원천 대비 건수·금액 대사로 매일 증명합니다(Day 22).
:::

**Q4. 팩트 적재 중 차원을 찾지 못한 행과 금액이 틀린 행을 각각 어떻게 처리합니까?**

:::answer 모범 답안 보기
차원을 못 찾은 행은 금액이 맞으므로 -1로 적재해 합계를 지키고, 원천 키와 오류 값을 오류 테이블에 경고로 남겨 마스터 도착 후 SK를 고칩니다. 업무 키가 정상이고 마스터만 늦으면 추정 멤버가 더 낫습니다. 금액이 틀린 행은 대시보드에 나가면 안 되므로 거부하고 오류 테이블에 보관하며, 원천이 고쳐지면 그 키를 다음 추출에 강제로 포함합니다. 어느 규칙이 경고이고 거부인지는 현업과 합의해 매핑정의서와 품질 규칙에 적습니다(Day 20, 23).
:::

**Q5. Power BI 리포트가 느리다는 불만이 들어왔습니다. 어떻게 접근합니까?**

:::answer 모범 답안 보기
먼저 Import인지 DirectQuery인지 봅니다. Import면 모델 쪽(양방향 관계, 무거운 측정값, 큰 OBT, 불필요한 열)을 보고, DirectQuery면 리포트가 보내는 SQL의 실행계획을 봅니다. 흔한 원인은 날짜 차원 조건만 걸려 팩트 파티션이 잘리지 않는 경우, 상세 팩트를 매번 집계하는 경우입니다. 처방은 팩트 파티션 키에 직접 조건이 걸리게 하거나 월 집계·MV를 두는 것, 모델은 스타 단방향으로 정리하는 것입니다. 측정 전후를 같은 시나리오로 비교해 개선을 확인합니다(Day 25, 26).
:::

**Q6. 스타 스키마와 OBT 중 무엇을 고르겠습니까?**

:::answer 모범 답안 보기
여러 팩트와 리포트가 공유하는 그룹 공통 모델이면 스타를 고릅니다. grain이 다른 목표·재고 팩트를 같은 차원으로 연결할 수 있고, 차원 정정이 차원 행만 갱신하며, Power BI의 필터 흐름과 맞습니다. OBT는 단일 grain·단일 목적의 분석이나 추출에는 단순해서 좋으므로, 스타 위에 OBT 뷰를 따로 제공하는 절충을 씁니다. 결정은 ADR로 남기고, 현업의 "한 장으로" 요구는 표시 폴더·업무 이름 같은 모델 정리로 충족합니다(Day 26, 28).
:::

**Q7. DW 숫자가 ERP와 다르다는 항의가 왔습니다. 어떻게 대응합니까?**

:::answer 모범 답안 보기
먼저 두 숫자의 정의를 맞춥니다. 시점(주문/출고/전표), 취소·반품, 기준 일자, 조회 시각이 같은지 확인합니다. 정의가 같으면 대사 쿼리로 차이를 월 → 일 → 주문번호 수준까지 좁힙니다. 원인은 대개 누락(INNER JOIN, 워터마크), 중복(재실행), 삭제 미반영, -1·거부 건, 늦게 도착한 데이터입니다. 원인을 찾으면 해당 기간을 백필하고, 같은 유형을 잡는 품질 규칙을 추가합니다. 평소에 원천 기준 대사 결과를 매일 남겨 두면 대부분의 항의에 즉시 답할 수 있습니다(Day 12, 22, 23).
:::

**Q8. 계열사마다 거래처 코드가 다릅니다. 그룹 DW에서 어떻게 통합합니까?**

:::answer 모범 답안 보기
기술 문제이기 전에 소유권 문제입니다. 그룹 거래처 마스터의 오너와 스튜어드를 정하고(Day 13), 사업자등록번호 같은 식별 기준으로 계열사 코드를 그룹 거래처에 매핑하는 매핑 테이블을 둡니다. 매칭이 애매한 건은 스튜어드가 판정하는 절차를 만들고, 골든 레코드의 속성별 우선 원천을 정합니다. DW의 거래처 차원은 그룹 거래처를 기준으로 하고 계열사 원천 코드는 속성으로 보존합니다. 매핑 미완료 건은 -1이나 계열사 단위 추정 멤버로 두고 미매핑 건수를 지표로 관리합니다. 1차 범위에서는 한빛제약 ERP와 한빛로지스 WMS의 거래처 매핑이 선행 과제입니다.
:::

**Q9. 제약사 DW에서 데이터 무결성(감사 추적)을 어떻게 보장합니까?**

:::answer 모범 답안 보기
"이 숫자가 어디서, 언제, 어떤 규칙으로 왔는지"를 재현할 수 있게 합니다. 원천 원본을 STG에 보관하고, 모든 행에 적재일시·배치ID를 남기고, 변환 규칙은 버전 관리되는 SQL과 매핑정의서로 남깁니다. 삭제는 소프트 삭제로 흔적을 남기고, 오류·거부 건은 처리 이력과 함께 보관합니다. 원천 대비 대사와 품질 규칙 결과도 기록으로 남깁니다. ALCOA+ 같은 무결성 원칙(Day 12)에 비춰 귀속성·원본성·완전성 항목별로 무엇으로 증명하는지 정리해 두고, 보관 기간과 접근 권한은 품질·법무 부서와 합의합니다.
:::

**Q10. 현업 요청과 기술적 판단이 충돌할 때 어떻게 결정을 이끕니까?**

:::answer 모범 답안 보기
요청의 목적을 먼저 확인합니다. "실시간", "한 장짜리 테이블" 같은 요청 뒤에는 대개 다른 수단으로 충족할 수 있는 목적이 있습니다. 그다음 선택지 두세 개를 현업의 언어(언제 무엇을 볼 수 있나, 비용, 위험, 일정)로 비교하고 추천안을 냅니다. 평가 기준은 결론 전에 합의하고, 결정권자가 고르게 하며, 결과와 포기한 것을 ADR로 남깁니다. 결정이 늦어지면 기한을 정하고 넘기면 기본안으로 진행한다는 것을 기록합니다. 목표는 논쟁에서 이기는 것이 아니라 1년 뒤에도 설명 가능한 결정을 남기는 것입니다(Day 28, 29).
:::

## 오늘의 과제

**과제 1.** 영업본부장이 팀별 3월 달성률을 요청했습니다. 마트(lab.dm_sales_mm_emp)에서 부서별로 다시 집계하세요. 달성률은 사원 달성률의 평균이 아니라 합계끼리 나눠야 합니다. 결과 모양은 `dept_nm, sales_amt, tgt_amt, achv_rt` 3행이고 서울1팀 206,000 / 250,000 / 82.4, 경기팀 108.0, 부산팀 0.0입니다.

:::answer 해설 보기
비율은 비가산입니다(Day 17). 사원 달성률 60.0과 97.3의 평균 78.7은 틀린 값이고, 금액 합계끼리 나눠야 합니다. Power BI 측정값이 DIVIDE(SUM, SUM) 형태여야 하는 이유도 같습니다.

```sql
SELECT dept_nm, SUM(sales_amt) AS sales_amt, SUM(tgt_amt) AS tgt_amt,
       ROUND(100.0 * SUM(sales_amt) / NULLIF(SUM(tgt_amt), 0), 1) AS achv_rt
  FROM lab.dm_sales_mm_emp
 WHERE yyyymm = '202603'
 GROUP BY dept_nm
 ORDER BY dept_nm;
```

경기팀 2,160,000 / 2,000,000 / 108.0, 부산팀 0 / 50,000 / 0.0입니다. 팀이 상위 조직으로 바뀌는 조직개편이 생기면 사원 차원의 부서 속성 SCD 유형(Day 19)을 다시 따져야 합니다.
:::

**과제 2.** 품질 게이트에 "목표가 있는 사원 중 마트에 행이 없는 사원 수" 점검을 추가하는 쿼리를 작성하세요. drill-across가 FULL OUTER JOIN으로 되어 있으면 0이어야 합니다. 결과 모양은 `chk_cd, result_val` 1행(TGT_IN_DM, 0)입니다.

:::answer 해설 보기
목표 팩트를 기준으로 마트에 같은 (연월, 사원) 행이 있는지 봅니다. 마트 적재를 INNER JOIN으로 바꾸면 최하은 3월 행이 빠져 1이 됩니다. 구현이 바뀌어도 규칙이 지켜지는지를 점검이 대신 확인해 줍니다.

```sql
SELECT 'TGT_IN_DM' AS chk_cd, COUNT(*) AS result_val
  FROM lab.fct_sales_tgt t
 WHERE NOT EXISTS (SELECT 1 FROM lab.dm_sales_mm_emp m
                    WHERE m.yyyymm = t.yyyymm AND m.emp_sk = t.emp_sk);
```

이 점검을 품질 규칙 목록에 등록하고, Day 24의 CHK_RECON 작업에 포함합니다.
:::

## 실무 산출물 연결

| 단계 | 이 케이스의 산출물 | 핵심 내용 |
|---|---|---|
| 분석 | 요구사항정의서, 인터뷰 기록, 지표 사전 초안 | 매출 정의 5개 결정, NFR-01·02, 범위 밖(계열사 통합) |
| 설계 | 아키텍처 정의서, ADR-001·002, 버스 매트릭스, ERD, 테이블정의서, 매핑정의서 | 레이어, grain, SCD 표, -1·거부 규칙, 감사 컬럼 |
| 구축 | 적재 프로그램, 마트(DM_SALES_MM_EMP), BI 뷰, 시맨틱 모델 | 멱등 MERGE, drill-across, 공통 측정값 |
| 테스트 | 대사 결과, 품질 게이트 결과, 리포트 검수서, 성능 테스트 | RECON_AMT 0, SQL 기준 숫자 = 화면 숫자 |
| 이행·운영 | 배치 설계서, SLA 합의서, 장애 대응 매뉴얼 | D+1 07:00, 게이트 실패 시 전일 유지 표시 |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 6 "Order Management", Chapter 17 "Kimball DW/BI Lifecycle Overview", Chapter 19 "ETL Subsystems and Techniques".
- Ralph Kimball 외, "The Data Warehouse Lifecycle Toolkit", 2nd ed. (Wiley) — 요구사항에서 배포까지의 전체 수명주기.
- Microsoft Learn, Power BI 문서 — 스타 스키마 설계 지침.
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드(DAsP)" — 전 영역(요구사항, 모델링, 데이터 품질·표준·관리).
