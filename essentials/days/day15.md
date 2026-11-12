# Day 15. DW 아키텍처 비교

## 오늘의 한 줄

DW 아키텍처는 "학파 고르기"가 아니라 **통합을 어디서 하고, 이력과 감사를 어디에 남기고, 사용자는 어디만 보게 할지**를 정하는 일입니다. Inmon·Kimball·Data Vault·메달리온은 이 세 질문에 다르게 답한 설계 방식이고, 실무 DW는 대개 이들을 레이어별로 섞어 씁니다.

## 왜 중요한가

그룹 DW 킥오프에서 한빛로지스 쪽은 "레이크하우스로 브론즈·실버·골드 하자", 그룹 경영지원실은 "정규화된 전사 DW부터", 정 과장은 "대시보드부터 빨리"를 말합니다. 아키텍트가 기준 없이 한쪽 손을 들어 주면 1년 뒤 계열사마다 다른 "매출"이 마트에 하나씩 생기거나, 반대로 전사 모델만 1년째 그리다 현업이 엑셀로 돌아갑니다. 각 방식이 **무엇을 위해 무엇을 포기하는지** 알아야 "1차 범위는 이렇게, 2차부터는 이렇게"라는 근거 있는 결정을 할 수 있습니다.

## 핵심 개념

### 1. 레이어: 데이터가 거치는 정거장

쉽게 말하면 레이어는 "원천 그대로 받기 → 정리해서 쌓기 → 분석하기 좋게 모양 잡기 → 용도별로 잘라 주기"의 정거장입니다. 정거장을 나누는 이유는 **책임과 변경 주기가 다르기 때문**입니다.

| 레이어 | 접두어 | 한 줄 역할 | 누가 바꾸나 | 보관 |
|---|---|---|---|---|
| Staging | STG_ | 원천을 가공 없이 복사. 적재 실패 시 원천을 다시 안 건드리고 재처리 | 엔지니어 (원천 구조가 바뀔 때) | 짧게 (며칠~몇 회차) |
| ODS | ODS_ | 원천과 거의 같은 구조의 최신 상태. 운영 조회·대사용 | 엔지니어 | 현재 상태 중심 |
| DW (통합) | DIM_, FCT_ 또는 3NF | 계열사·시스템을 같은 키·코드로 통합하고 이력을 남긴 "정본" | 아키텍트·모델러 | 길게 (이력 전체) |
| DM (마트) | DM_ | 부서·대시보드 용도로 집계·평탄화 | BI 담당, 마트 개발자 | 재생성 가능하면 짧아도 됨 |

ODS(Operational Data Store)는 "운영계 복사본을 운영 목적으로 조회하는 곳"이고, Staging은 "적재 작업 공간"입니다. 둘을 합치는 프로젝트도 많지만, 합치면 ODS를 조회하는 사람이 생기는 순간 Staging 구조를 마음대로 못 바꾸게 된다는 점을 알고 합쳐야 합니다.

### 2. Inmon: 정규화된 전사 DW를 먼저

Bill Inmon의 방식은 **전사 통합 DW를 3정규형에 가깝게 먼저 만들고**, 부서 마트는 그 DW에서 뽑아내는 하향식(top-down)입니다. 통합의 정본이 정규화 모델이므로 Week 1에서 배운 운영계 모델링 기술이 그대로 쓰입니다.

장점은 일관성입니다. "거래처"는 그룹 전체에 하나의 엔터티로 존재하고, 마트는 그 파생물이라 숫자가 어긋날 여지가 작습니다. 약점은 시간입니다. 전사 엔터티를 합의하는 데 오래 걸리고, 사용자가 볼 마트는 그 뒤에야 나옵니다. 또 DW 자체는 조인이 많아 BI가 직접 붙기 어렵기 때문에 마트 레이어가 필수입니다.

### 3. Kimball: 차원 모델이 곧 DW, 버스로 통합

Ralph Kimball의 방식은 **업무 프로세스 단위로 스타 스키마를 만들되, 공통 차원(Conformed Dimension)을 공유해서 통합**하는 방식으로, 흔히 상향식(bottom-up)이라 불립니다. 다만 Kimball·Ross는 이 꼬리표에 반대합니다. 계획은 버스 매트릭스로 전사 차원에서 먼저 세우고, 구현만 프로세스 단위로 나눠 한다는 입장입니다. 통합의 장치는 정규화 모델이 아니라 "주문 팩트와 출고 팩트가 같은 품목 차원, 같은 날짜 차원을 쓴다"는 약속이고, 이 약속을 표로 그린 것이 버스 매트릭스(Day 18)입니다.

장점은 속도와 사용성입니다. 1차 범위(영업실적)만으로도 바로 쓸 수 있는 스타 스키마가 나오고, BI 도구가 그대로 붙습니다. 약점은 규율입니다. 공통 차원을 지키지 않으면 프로세스마다 다른 거래처 차원이 생겨 "독립 마트 난립"이 되고, 이것이 Kimball 방식을 쓴다고 하면서 가장 흔히 실패하는 모습입니다.

### 4. Data Vault: 변화와 감사에 강한 통합 원장

Data Vault(Dan Linstedt)는 통합 레이어를 세 종류의 테이블로만 만듭니다. 쉽게 말하면 "업무 키 목록, 관계 목록, 속성 변경 이력"을 따로 쌓는 방식입니다.

| 구성 | 담는 것 | 한빛 예시 |
|---|---|---|
| Hub | 업무 키(Business Key)와 최초 적재 정보만 | HUB_CUST (CUST_NO) |
| Link | 업무 키 간 관계 | LNK_ORD_CUST (주문 ↔ 거래처) |
| Satellite | 속성과 그 변경 이력 (적재일시 기준) | SAT_CUST_EMP (담당영업사원. 엄밀히는 거래처-사원 Link + effectivity satellite이지만 여기서는 단순화) |

원천에 새 속성이 생기면 Satellite를 하나 더 붙이면 되고, 기존 테이블을 고치지 않습니다. 원천 값을 가공 없이 적재일시와 함께 남기므로 "그때 원천이 뭐라고 줬나"를 재현하는 감사에 강합니다. 대신 테이블 수가 많고 조회가 어려워서 **사용자에게 직접 열지 않고**, 그 위에 차원 모델(정보 마트)을 반드시 한 겹 더 올립니다. 즉 Data Vault는 Kimball의 대체재가 아니라 통합 레이어 자리의 선택지입니다.

### 5. 레이크하우스와 메달리온: 저장소가 바뀌어도 질문은 같다

메달리온(Bronze → Silver → Gold)은 Databricks 문서가 널리 퍼뜨린 이름으로, 레이크(파일 저장소) 위의 테이블을 품질 단계로 나누는 방식입니다. Bronze는 원천 그대로(Staging·원본 이력), Silver는 정제·중복 제거·표준화된 통합 데이터(ODS·통합 DW), Gold는 업무용 집계·차원 모델(DM)에 대응합니다.

중요한 점은 메달리온이 **모델링 방법을 정해 주지 않는다**는 것입니다. Silver를 3NF로 만들지, Data Vault로 만들지, Gold를 스타 스키마로 만들지는 여전히 우리가 정합니다. Analytics Engineer에게 익숙한 dbt의 staging → intermediate → marts 구조도 같은 레이어 사고입니다.

## 예시

### 한빛 그룹 DW 레이어 구성안

1차 범위(한빛제약 영업실적 + 한빛로지스 출고·재고)에 대한 구성안입니다.

```text
 HBP_ERP      HBL_WMS      (2차) OTHER_ERP   원천 (Oracle)
    |            |              |
    v            v              v
 +------------------------------------+
 | STG_*                              |   Staging: 원천 그대로
 +------------------------------------+
    |
    v
 +------------------------------------+
 | DIM_DATE  DIM_CUST  DIM_ITEM       |   통합 DW: 공통 차원
 | DIM_EMP   DIM_WH    DIM_LOT        |
 | FCT_ORD_LINE  FCT_SHIP_LINE        |   프로세스별 팩트
 | FCT_INV_DAILY                      |
 +------------------------------------+
    |
    v
 +------------------------------------+
 | DM_SALES_*        DM_LOGI_*        |   마트: 영업실적, 물류 KPI
 +------------------------------------+
    |                   |
 Power BI           Tableau          경영·영업 / 물류 사용자
```

그림의 HBP_ERP는 한빛제약 ERP, HBL_WMS는 한빛로지스 WMS를 가리키는 설명용 약칭입니다.

공통 스키마의 `schema/10_dw.sql`이 이 그림의 통합 DW 레이어입니다. 지금 테이블 목록을 확인해 봅니다.

```sql
-- 그룹 DW(dw 스키마)에 무엇이 있나: 차원과 팩트, 행 수
SELECT 'DIM_DATE' AS tbl, COUNT(*) AS row_cnt FROM dw.dim_date
UNION ALL SELECT 'DIM_CUST', COUNT(*) FROM dw.dim_cust
UNION ALL SELECT 'DIM_ITEM', COUNT(*) FROM dw.dim_item
UNION ALL SELECT 'DIM_EMP', COUNT(*) FROM dw.dim_emp
UNION ALL SELECT 'DIM_WH', COUNT(*) FROM dw.dim_wh
UNION ALL SELECT 'DIM_LOT', COUNT(*) FROM dw.dim_lot
UNION ALL SELECT 'FCT_ORD_LINE', COUNT(*) FROM dw.fct_ord_line
UNION ALL SELECT 'FCT_SHIP_LINE', COUNT(*) FROM dw.fct_ship_line
UNION ALL SELECT 'FCT_INV_DAILY', COUNT(*) FROM dw.fct_inv_daily;
```

날짜 차원은 2025~2026년 730일 + 알 수 없음(-1) 1행 = 731행, 거래처 차원은 거래처 5곳인데 7행입니다(알 수 없음 1행 + 청솔내과의원이 담당 변경으로 2개 버전). 이 "거래처 수보다 많은 행"이 Day 19의 SCD Type 2입니다.

### 같은 원천을 세 학파로 담아 보기

거래처 담당 정보를 Staging → Data Vault → 차원으로 옮겨 봅니다. 모두 `lab` 스키마에 만듭니다.

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

-- 1) Staging: 원천 그대로 + 적재 회차 정보
CREATE TABLE lab.stg_cust_emp_hist AS
SELECT h.*, 'B20260401' AS batch_id, TIMESTAMP '2026-04-01 02:00' AS load_dtm
  FROM erp.tb_cust_emp_hist h;

-- 2) Data Vault: Hub(업무 키) + Satellite(속성 이력)
CREATE TABLE lab.hub_cust (
  cust_hk      CHAR(32)    PRIMARY KEY,   -- 해시 키 = md5(업무 키)
  cust_no      VARCHAR(10) NOT NULL UNIQUE,
  load_dtm     TIMESTAMP   NOT NULL,
  rec_src      VARCHAR(20) NOT NULL       -- 레코드 출처 (어느 시스템에서 왔나)
);
CREATE TABLE lab.sat_cust_emp (
  cust_hk      CHAR(32)    NOT NULL REFERENCES lab.hub_cust(cust_hk),
  load_dtm     TIMESTAMP   NOT NULL,
  aply_strt_dt DATE        NOT NULL,
  aply_end_dt  DATE        NOT NULL,
  emp_no       VARCHAR(10) NOT NULL,
  hash_diff    CHAR(32)    NOT NULL,      -- 속성 묶음의 해시 (변경 감지용)
  rec_src      VARCHAR(20) NOT NULL,
  PRIMARY KEY (cust_hk, load_dtm, aply_strt_dt)
);

INSERT INTO lab.hub_cust
SELECT DISTINCT md5(cust_no), cust_no, load_dtm, 'HBP_ERP'
  FROM lab.stg_cust_emp_hist;

INSERT INTO lab.sat_cust_emp
SELECT md5(cust_no), load_dtm, aply_strt_dt, aply_end_dt, emp_no,
       md5(emp_no || '|' || aply_end_dt::text), 'HBP_ERP'
  FROM lab.stg_cust_emp_hist;

SELECT h.cust_no, s.aply_strt_dt, s.aply_end_dt, s.emp_no, s.rec_src
  FROM lab.hub_cust h JOIN lab.sat_cust_emp s ON s.cust_hk = h.cust_hk
 ORDER BY h.cust_no, s.aply_strt_dt;
```

:::note Oracle 차이
Oracle에는 `md5()` 함수가 없습니다. `STANDARD_HASH(CUST_NO, 'MD5')`(RAW 반환)나 `DBMS_CRYPTO.HASH`를 쓰고, `CREATE TABLE ... AS SELECT`는 같습니다. 해시 알고리즘과 입력 문자열 규칙(구분자, 대소문자, 공백 제거)은 시스템 간에 반드시 같아야 하므로 표준으로 정해 둡니다.
:::

Hub는 거래처 5행, Satellite는 이력 6행입니다. 이제 이 Vault 위에 사용자용 차원을 "뷰"로 올립니다. Data Vault에서 정보 마트를 만드는 전형적인 모습입니다.

```sql
-- 3) Vault 위의 차원 (Kimball 모양): 사용자는 이것만 봅니다
CREATE VIEW lab.v_dim_cust_from_vault AS
SELECT h.cust_no, c.cust_nm, s.emp_no, e.emp_nm, s.aply_strt_dt AS eff_strt_dt, s.aply_end_dt AS eff_end_dt,
       CASE WHEN s.aply_end_dt = DATE '9999-12-31' THEN 'Y' ELSE 'N' END AS curr_yn
  FROM lab.hub_cust h
  JOIN lab.sat_cust_emp s ON s.cust_hk = h.cust_hk
  JOIN erp.tb_cust c      ON c.cust_no = h.cust_no
  JOIN erp.tb_emp e       ON e.emp_no  = s.emp_no;

-- 정본 DW 차원(dw.dim_cust)과 같은 내용인지 대사: 차이 0행이어야 정상
SELECT cust_no, emp_no, eff_strt_dt, eff_end_dt FROM lab.v_dim_cust_from_vault
EXCEPT
SELECT cust_no, emp_no, eff_strt_dt, eff_end_dt FROM dw.dim_cust WHERE cust_sk <> -1;
```

같은 원천이 세 가지 모양으로 담겼고, 사용자에게 보이는 최종 모양(차원)은 같습니다. 차이는 **중간에 무엇을 남겼느냐**입니다. Vault는 "4월 1일 02시 적재분에서 원천이 이렇게 줬다"를 남기고, 차원은 "업무상 이 기간에 이 담당"만 남깁니다.

### 네 방식 한눈에

| 구분 | Inmon | Kimball | Data Vault | 메달리온 |
|---|---|---|---|---|
| 통합하는 곳 | 3NF 전사 DW | 공통 차원 (버스) | Hub·Link | Silver (방법은 자유) |
| 사용자가 보는 곳 | 마트 | 스타 스키마 자체 | 정보 마트 (차원 모델) | Gold |
| 첫 결과물까지 | 오래 걸림 | 빠름 | 중간 (자동화 도구가 있으면 빠름) | 방법에 따라 다름 |
| 원천 변경 대응 | 모델 수정 필요 | 차원·팩트 수정 | Satellite 추가로 흡수 | Bronze가 원본을 보존 |
| 감사·원천 재현 | 설계하기 나름 | 약함 (정제된 값만) | 강함 | Bronze 보존 기간만큼 |
| 필요한 규율 | 전사 합의 | 공통 차원 거버넌스 | 해시·적재 표준 자동화 | 레이어 경계 규칙 |

## Before / After

**Before: 대시보드마다 원천에서 직접 뽑는 구조**

| 원천 | 소비 방식 | "매출"·기준 |
|---|---|---|
| 한빛제약 ERP | 영업실적 엑셀 (정 과장) | 주문금액 합계 |
| 한빛제약 ERP | Power BI 직접 연결 | 출고완료 주문만 |
| 한빛로지스 WMS | Tableau 추출 (한 대리) | 거래처 코드 체계가 ERP와 다름 |

같은 "3월 매출"이 세 가지로 나오고, ERP 마감 시간에 조회 부하가 겹치며, 거래처 코드가 시스템마다 달라 그룹 합산이 안 됩니다.

**After: 레이어와 책임을 나눈 구조**

| 레이어 | 1차 범위 결정 | 이유 |
|---|---|---|
| Staging | 원천별 STG_, 최근 7회차 보관 (보관 기간은 가정) | 재처리 시 운영계 재조회 없이 복구 |
| 통합 DW | Kimball 스타 스키마 + 공통 차원 (DIM_CUST, DIM_ITEM, DIM_DATE) | 1차 범위가 두 프로세스뿐이고 빨리 보여 줘야 함 |
| 마트 | DM_ 영업실적, DM_ 물류 KPI | BI는 마트만 조회. 지표 정의를 한 곳에 |
| 2차 검토 | 계열사 5곳 원천이 붙을 때 통합 레이어를 Data Vault로 둘지 재평가 | 원천 수와 변경 빈도가 커지면 Vault의 장점이 커짐 |

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 통합 레이어 방식 | 원천이 적고 업무가 안정적이며 빨리 보여 줘야 하면 Kimball 스타 스키마를 통합 레이어로 | 원천이 많고 자주 바뀌며 감사 요구(원천 재현)가 강하면 Data Vault를 통합 레이어로 두고 그 위에 차원 |
| 전사 3NF DW | 전사 마스터 합의가 이미 되어 있고 여러 마트가 같은 상세를 다르게 잘라 쓰면 Inmon식 | 합의 전이면 공통 차원부터 합의하는 Kimball 버스가 현실적 |
| ODS를 따로 둘지 | 운영 부서가 "실시간에 가까운 원천 조회"를 DW에 요구하면 ODS 분리 | 그런 요구가 없으면 Staging만 두고 ODS는 만들지 않음 |
| 메달리온 용어 | 레이크하우스 플랫폼을 쓰고 팀이 그 용어에 익숙하면 Bronze/Silver/Gold로 부르되 각 층의 모델링 방법을 따로 명시 | 전통 DBMS 기반이면 STG/DW/DM 용어를 유지. 이름보다 경계 규칙이 중요 |
| 1차 범위가 작을 때 | 최종 구조를 그려 두고 1차는 그중 일부만 구현 (버스 매트릭스로 범위 표시) | "나중에 바꾸자"며 레이어를 건너뛰면, BI가 붙은 뒤에는 바꾸기 어려움 |

판단의 핵심 질문은 셋입니다. **통합은 어디서 하나**(공통 차원? 3NF? Hub?), **원천 재현이 필요한가**(감사·소급 정정), **사용자는 어디까지 내려오나**(마트만? 스타 스키마까지?). 학파 이름은 이 답을 요약한 꼬리표일 뿐입니다.

## 흔한 실수 3가지

1. **"Kimball이니까 마트부터"라며 공통 차원 없이 마트를 만드는 실수.** 영업 마트와 물류 마트가 각자 거래처 테이블을 만들면, 6개월 뒤 두 마트의 거래처 수가 다르고 그룹 합산이 불가능해집니다. 첫 마트를 만들 때 이미 DIM_CUST·DIM_ITEM·DIM_DATE를 공통으로 설계합니다.
2. **Data Vault를 사용자에게 직접 여는 실수.** Hub·Link·Satellite를 BI에 붙이면 조인이 수십 개가 되고 "현재 값" 하나 구하는 데도 최신 Satellite 행을 찾는 로직이 필요합니다. Vault 위에는 반드시 차원 모델을 올립니다.
3. **레이어 이름만 정하고 경계 규칙을 안 정하는 실수.** "Silver에서 코드 표준화를 하나, Gold에서 하나"가 정해지지 않으면 같은 변환이 두 곳에서 다르게 일어납니다. 레이어별로 "여기서 하는 일 / 하지 않는 일"을 설계서에 적습니다.

## 셀프 체크 질문

**Q1. Inmon과 Kimball의 가장 큰 차이를 "통합"이라는 단어로 설명해 보세요.**

:::answer 모범 답안 보기
둘 다 전사 통합을 목표로 하지만, 통합의 장치가 다릅니다. Inmon은 정규화된 전사 DW라는 **하나의 모델**로 통합하고 마트는 그 파생물로 둡니다. Kimball은 프로세스별 스타 스키마를 만들되 **공통 차원(Conformed Dimension)을 공유**해서 통합합니다. 그래서 Inmon은 처음에 전사 엔터티 합의가 오래 걸리지만 일관성이 구조적으로 보장되고, Kimball은 빨리 쓸 수 있지만 공통 차원 거버넌스가 무너지면 독립 마트 난립이 됩니다. 한빛 그룹 1차 범위처럼 프로세스가 두세 개이고 빨리 보여 줘야 하면 Kimball 버스로 시작하고, 버스 매트릭스로 확장 범위를 미리 그려 둡니다.
:::

**Q2. 한빛로지스가 "레이크하우스로 가면 차원 모델링은 필요 없지 않나요?"라고 묻습니다. 어떻게 답하겠습니까?**

:::answer 모범 답안 보기
레이크하우스와 메달리온은 저장소와 품질 단계를 나누는 방식이지 모델링 방법이 아니라고 답합니다. Gold 층에서 Power BI·Tableau가 빠르고 일관되게 쓰려면 여전히 "한 행이 무엇인가(grain)", "어떤 차원으로 자르는가", "거래처는 그룹 공통 기준인가"를 정해야 하고, 그 답을 정리한 것이 차원 모델입니다. 오히려 파일 기반 저장소는 PK·FK 제약이 약해서 grain과 공통 차원을 설계 문서와 테스트로 더 엄격하게 지켜야 합니다. 그래서 "Bronze는 원천 보존, Silver는 표준화·통합, Gold는 공통 차원을 쓰는 스타 스키마"처럼 각 층의 모델링 방법을 명시하자고 제안합니다.
:::

**Q3. Data Vault를 통합 레이어로 도입하자는 의견이 나왔습니다. 도입을 찬성하려면 어떤 조건을 확인하겠습니까?**

:::answer 모범 답안 보기
세 가지를 확인합니다. 첫째, 원천 수와 변경 빈도입니다. 계열사 ERP가 여러 개 붙고 컬럼 추가·시스템 교체가 잦으면 Satellite 추가로 흡수하는 장점이 큽니다. 둘째, 감사 요구입니다. "그때 원천이 무엇을 줬나"를 재현해야 하는 규제·감사 대응이 있으면 적재일시 기준 원본 보존이 가치가 있습니다. 셋째, 자동화 역량입니다. 해시 키 규칙, Hub·Link·Satellite 생성, 그 위의 차원 생성이 코드 생성 도구나 템플릿으로 자동화되지 않으면 테이블 수만큼 수작업이 늘어납니다. 셋 다 약하면 1차는 스타 스키마로 시작하고, 원천 보존은 Staging 보관 기간으로 해결하는 편이 낫습니다.
:::

## 오늘의 과제

**과제 1.** 품목도 Data Vault로 담아 보세요. `lab.hub_item`(ITEM_HK, ITEM_CD, LOAD_DTM, REC_SRC)과 `lab.sat_item`(ITEM_HK, LOAD_DTM, ITEM_NM, ITEM_TP_CD, UNIT_CD, HASH_DIFF, REC_SRC)을 만들고 `erp.tb_item`에서 적재한 뒤, 품목유형별 품목 수를 Vault에서 조회하세요. 결과 모양은 `item_tp_cd, item_cnt` 3행(FG 3, PM 1, RM 1)입니다.

:::answer 해설 보기
Hub에는 업무 키와 출처만, 속성은 Satellite에 둡니다. HASH_DIFF는 다음 적재 때 "속성이 바뀌었나"를 행 비교 없이 해시 하나로 판단하기 위한 값입니다.

```sql
CREATE TABLE lab.hub_item (
  item_hk  CHAR(32) PRIMARY KEY, item_cd VARCHAR(10) NOT NULL UNIQUE,
  load_dtm TIMESTAMP NOT NULL, rec_src VARCHAR(20) NOT NULL);
CREATE TABLE lab.sat_item (
  item_hk  CHAR(32) NOT NULL REFERENCES lab.hub_item(item_hk), load_dtm TIMESTAMP NOT NULL,
  item_nm  VARCHAR(100) NOT NULL, item_tp_cd VARCHAR(2) NOT NULL, unit_cd VARCHAR(5) NOT NULL,
  hash_diff CHAR(32) NOT NULL, rec_src VARCHAR(20) NOT NULL,
  PRIMARY KEY (item_hk, load_dtm));

INSERT INTO lab.hub_item
SELECT md5(item_cd), item_cd, TIMESTAMP '2026-04-01 02:00', 'HBP_ERP' FROM erp.tb_item;
INSERT INTO lab.sat_item
SELECT md5(item_cd), TIMESTAMP '2026-04-01 02:00', item_nm, item_tp_cd, unit_cd,
       md5(item_nm || '|' || item_tp_cd || '|' || unit_cd), 'HBP_ERP'
  FROM erp.tb_item;

SELECT s.item_tp_cd, COUNT(*) AS item_cnt
  FROM lab.hub_item h JOIN lab.sat_item s ON s.item_hk = h.item_hk
 GROUP BY s.item_tp_cd
 ORDER BY s.item_tp_cd;
```

Satellite에 같은 품목의 행이 여러 개 쌓이기 시작하면 "현재 값"은 품목별 최신 LOAD_DTM 행입니다. 이 로직을 매번 쓰지 않게 하려고 Vault 위에 차원을 올립니다.
:::

**과제 2.** 레이어 경계 규칙을 쿼리로 점검해 보세요. 통합 DW의 주문상세 팩트(`dw.fct_ord_line`)가 원천 주문상세(`erp.tb_ord_dtl`)와 행 수·금액 합계가 같은지 한 쿼리로 비교합니다. 결과 모양은 `src_cnt, dw_cnt, src_amt, dw_amt` 1행이며 두 쌍이 같아야 합니다.

:::answer 해설 보기
레이어를 나누면 "레이어 사이에서 데이터가 빠지거나 불어나지 않았나"를 매 적재마다 대사해야 합니다. 건수와 합계 금액 대사가 가장 기본입니다.

```sql
SELECT (SELECT COUNT(*) FROM erp.tb_ord_dtl)   AS src_cnt,
       (SELECT COUNT(*) FROM dw.fct_ord_line)  AS dw_cnt,
       (SELECT SUM(ord_amt) FROM erp.tb_ord_dtl)  AS src_amt,
       (SELECT SUM(ord_amt) FROM dw.fct_ord_line) AS dw_amt;
```

8건, 2,436,000원으로 같습니다. 취소 주문(SO2026040002)도 팩트에 들어 있다는 점에 주의합니다. 팩트는 원천의 사실을 빠짐없이 담고, "매출에서 취소 제외"는 마트나 측정값 정의에서 합니다(Day 26).
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 데이터 아키텍처 정의서 | 레이어 구성도, 레이어별 역할·접두어·보관 기간, "여기서 하는 일 / 하지 않는 일", 통합 레이어 방식 선택 이유 |
| ADR (Day 28) | "1차 범위 통합 레이어 = 스타 스키마, 2차에 Data Vault 재평가" 같은 결정과 대안·근거 |
| 요구사항정의서 | 비기능 요구사항: 감사(원천 재현) 필요 여부, 데이터 신선도, BI 조회 대상 레이어 |
| 표준 정의서 | 레이어 접두어(STG_, ODS_, DIM_, FCT_, DM_), 해시 키 규칙(Vault를 쓸 때) |
| 매핑정의서 | 레이어 간 매핑(원천 → STG → DW → DM)과 레이어별 대사 규칙(건수·합계) |

## 참고할 원전

- Ralph Kimball, Margy Ross, "The Data Warehouse Toolkit", 3rd ed. (Wiley, 2013) — Chapter 1 "Data Warehousing, Business Intelligence, and Dimensional Modeling Primer"(Kimball 아키텍처와 다른 아키텍처 비교).
- W. H. Inmon, "Building the Data Warehouse" (Wiley) — 정규화된 전사 DW와 하향식 접근.
- Dan Linstedt, Michael Olschimke, "Building a Scalable Data Warehouse with Data Vault 2.0" (Morgan Kaufmann, 2015) — Hub·Link·Satellite, 해시 키.
- Databricks 공식 문서 — medallion lakehouse architecture (Bronze·Silver·Gold).
- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드"(DAP·DAsP 공통 교재) — 전사아키텍처 이해 과목.
