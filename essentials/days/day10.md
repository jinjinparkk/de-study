# Day 10. 데이터 표준화

## 오늘의 한 줄

데이터 표준화는 "같은 것은 같은 이름·같은 타입으로, 다른 것은 다른 이름으로" 부르게 하는 약속을 사전으로 만들어 지키는 일입니다. 표준단어를 모아 표준용어를 만들고, 용어의 마지막 단어(분류어)가 표준도메인을 정하며, 코드형 용어는 표준코드로 값을 묶습니다.

## 왜 중요한가

한빛제약 ERP는 거래처번호를 CUST_NO, 한빛푸드 ERP는 CLNT_ID, 한빛로지스 WMS는 CUSTOMER_CODE라고 부릅니다. 그룹 DW 매핑정의서를 쓰는 사람은 세 컬럼이 같은 것인지 매번 물어야 하고, 길이도 10·15·20으로 달라 조인 키를 맞추느라 변환이 늘어납니다. 더 위험한 것은 반대 경우입니다. 한빛제약의 "유효기간"(36개월)과 한빛푸드의 "유효기간"(2026-09-30 같은 날짜)이 같은 이름으로 DW에 들어오면 아무도 모르게 서로 다른 값을 같은 컬럼에 섞게 됩니다. 한국 SI와 그룹 IT 프로젝트에서 표준화 산출물이 설계 단계 첫 관문인 이유입니다.

## 핵심 개념

### 1. 네 가지 사전의 관계

| 사전 | 담는 것 | 예 |
|---|---|---|
| 표준단어 | 더 쪼개지 않는 업무 단어와 영문 약어 | 거래처 = CUST, 번호 = NO |
| 표준도메인 | 값의 형식 (타입·길이·소수자리) | 번호V10 = VARCHAR(10), 금액N15 = NUMERIC(15) |
| 표준용어 | 단어를 조합한 컬럼 이름 + 도메인 | 거래처번호 = CUST_NO, 도메인 번호V10 |
| 표준코드 | 코드형 용어가 가질 수 있는 값 목록 | 거래처유형코드 = 01 병원, 02 약국, 03 도매상 (Day 9) |

쉽게 말하면 단어는 레고 블록, 용어는 블록을 조립한 완성품, 도메인은 완성품의 규격, 코드는 그 규격 안에서 허용되는 값입니다. 순서가 중요합니다. **단어가 먼저 있어야 용어를 만들 수 있고**, 사전에 없는 단어가 필요하면 표준단어 신청부터 합니다.

### 2. 명명규칙: 주제어 + 수식어 + 분류어

표준용어는 "무엇의(주제어) 어떤(수식어) 무엇(분류어)"로 조립합니다. 마지막 단어가 **분류어**(class word)이고 분류어가 도메인 후보를 정합니다.

| 표준용어 | 조립 | 물리명 | 분류어 → 도메인 |
|---|---|---|---|
| 거래처번호 | 거래처 + 번호 | CUST_NO | 번호 → 번호V10 |
| 주문상태코드 | 주문 + 상태 + 코드 | ORD_STAT_CD | 코드 → 코드V2 |
| 적용시작일자 | 적용 + 시작 + 일자 | APLY_STRT_DT | 일자 → 일자D |
| 여신한도금액 | 여신 + 한도 + 금액 | CRDT_LMT_AMT | 금액 → 금액N15 |

분류어 없는 용어(그냥 "거래처")는 컬럼명이 될 수 없고, 분류어는 적게 유지합니다(번호·코드·명·일자·일시·여부·수량·금액·단가·순번 정도). 물리명 길이 상한(예: 30자)도 정합니다.

### 3. 표준도메인: 같은 의미는 같은 타입

Day 8에서 "같은 의미 = 같은 타입"이라고 했습니다. 표준도메인은 그 규칙을 사전으로 만든 것입니다. 모든 컬럼은 등록된 도메인 중 하나를 고르고, **도메인에 없는 타입·길이는 쓸 수 없습니다.** 도메인은 분류어마다 여러 개일 수 있지만(번호V10, 번호V14), 너무 많으면 표준이 아니라 목록에 불과합니다. 도메인을 하나 추가할 때마다 "기존 것으로 안 되는 이유"를 적게 합니다.

### 4. 금칙어, 이음동의어, 동음이의어

- **금칙어**: 표준 대신 쓰면 안 되는 단어입니다. "고객"은 그룹 안에서 매출처·소비자·환자를 모두 가리킬 수 있어 금칙어로 두고 "거래처"로 안내합니다.
- **이음동의어**: 다른 말, 같은 뜻입니다. 매출처·거래처, 가격·단가. 하나만 표준으로 두고 나머지는 사전에 "→ 거래처"처럼 연결합니다. 검색할 때 이음동의어로 찾아도 표준단어가 나오게 하는 것이 목적입니다.
- **동음이의어**: 같은 말, 다른 뜻입니다. 이것이 가장 위험합니다. **유효기간**(제조 후 사용 가능한 기간, 36개월)과 **유효기한**(그 로트를 쓸 수 있는 마지막 날짜, EXP_DT)은 한 글자 차이로 전혀 다른 값입니다. 둘을 다른 단어로 등록하고 각각 정의를 적습니다.

### 5. 표준은 "신청과 심의"로 자랍니다

표준 사전은 한 번 만들고 끝나지 않습니다. 설계자가 사전에 없는 단어를 쓰고 싶으면 신청하고, 데이터 표준 담당(DA)이 기존 단어로 표현 가능한지, 이음동의어는 아닌지, 약어가 겹치지 않는지 보고 승인·반려합니다. 신청 없이 쓰인 단어는 설계 리뷰나 자동 점검에서 걸러냅니다.

## 예시

### 표준 사전 테이블과 표준단어 등록

WORLD 2절의 표준 약어표를 표준단어로 등록합니다. 분류어 여부(CLS_WORD_YN)를 함께 둡니다.

```sql
DROP SCHEMA IF EXISTS lab CASCADE;   -- 앞 Day 실습 테이블 정리(한 DB에서 이어서 실행해도 되도록)
CREATE SCHEMA lab;

CREATE TABLE lab.tb_std_word (                 -- 표준단어
  word_nm     VARCHAR(30) PRIMARY KEY,
  abbr_nm     VARCHAR(20) NOT NULL UNIQUE,     -- 영문 약어 (물리명 조각)
  cls_word_yn CHAR(1)     NOT NULL DEFAULT 'N' CHECK (cls_word_yn IN ('Y', 'N')),
  word_desc   VARCHAR(200)
);
INSERT INTO lab.tb_std_word (word_nm, abbr_nm, cls_word_yn) VALUES
 ('거래처','CUST','N'), ('구매처','VNDR','N'), ('품목','ITEM','N'), ('주문','ORD','N'), ('출고','SHIP','N'),
 ('입고','RCV','N'), ('재고','INV','N'), ('창고','WH','N'), ('로트','LOT','N'), ('사원','EMP','N'),
 ('부서','DEPT','N'), ('회사','CO','N'), ('번호','NO','Y'), ('코드','CD','Y'), ('명','NM','Y'),
 ('일자','DT','Y'), ('일시','DTM','Y'), ('여부','YN','Y'), ('수량','QTY','Y'), ('금액','AMT','Y'),
 ('단가','UPRC','Y'), ('유형','TP','N'), ('상태','STAT','N'), ('순번','SEQ','Y'), ('시작','STRT','N'),
 ('종료','END','N'), ('적용','APLY','N'), ('상위','PRNT','N'), ('하위','CHLD','N'), ('작업지시','WO','N'),
 ('생산','PROD','N'), ('실적','RSLT','N'), ('전표','SLIP','N'), ('계정','ACCT','N'), ('차변','DR','N'),
 ('대변','CR','N'), ('지역','RGN','N'), ('등록','REG','N'), ('사업자등록번호','BIZ_REG_NO','Y');

CREATE TABLE lab.tb_std_word_syn (             -- 금칙어·이음동의어
  syn_word_nm VARCHAR(30) PRIMARY KEY,
  std_word_nm VARCHAR(30) NOT NULL REFERENCES lab.tb_std_word (word_nm),
  syn_tp_cd   VARCHAR(2)  NOT NULL CHECK (syn_tp_cd IN ('01', '02'))   -- 01 금칙어, 02 이음동의어
);
INSERT INTO lab.tb_std_word_syn VALUES
 ('고객','거래처','01'), ('매출처','거래처','02'), ('공급업체','구매처','02'),
 ('가격','단가','02'), ('날짜','일자','01'), ('일','일자','01'), ('개수','수량','01');
```

사업자등록번호는 사업자 + 등록 + 번호로 쪼갤 수도 있지만, 업무에서 한 덩어리로 쓰이고 외부 기관 기준이 있는 값이라 복합 단어 하나로 등록했습니다. 이렇게 **쪼개지 않기로 한 복합어**도 표준의 일부로 목록화합니다.

### 공통 스키마를 표준단어로 점검하기

운영계 컬럼명을 언더스코어로 쪼개 각 조각이 표준단어 약어에 있는지 봅니다. 공통 스키마가 표준을 얼마나 지키는지 알 수 있습니다.

```sql
SELECT tok AS unregistered_abbr, COUNT(*) AS col_cnt,
       string_agg(table_name || '.' || column_name, ', ' ORDER BY table_name) AS used_in
  FROM (SELECT table_name, column_name,
               upper(regexp_split_to_table(replace(column_name, 'biz_reg_no', 'bizregno'), '_')) AS tok
          FROM information_schema.columns
         WHERE table_schema = 'erp') x
 WHERE tok <> 'BIZREGNO'
   AND tok NOT IN (SELECT abbr_nm FROM lab.tb_std_word)
 GROUP BY tok
 ORDER BY col_cnt DESC, tok;
```

15개 조각이 나옵니다. 발주(PO, 5개 컬럼), 사용(USE, 4개)처럼 매일 쓰는 단어가 표에 빠져 있었고, 나머지는 한 컬럼씩입니다(BIZ, BOM, DEFECT, DOC, EXP, GOOD, LIFE, MFG, MM, SHELF, SRC, UNIT, UPD). 이 목록이 곧 **표준단어 신청 목록**입니다.

### 표준단어 신청 심의

공통 스키마의 미등록 조각과, Week 1에서 쓰였지만 표에 없던 단어(WORLD 6절)를 함께 심의합니다.

| 신청 단어 (약어) | 쓰인 곳 | 판정 | 이유 |
|---|---|---|---|
| 발주 (PO) | TB_PO.PO_NO | 승인 | 업무 핵심 단어. 구매 영역 전체가 씀 |
| 사용 (USE) | USE_YN | 승인 | 사용여부는 거의 모든 마스터에 있음 |
| 수정 (UPD) | UPD_DTM | 승인 | 감사 컬럼 표준(REG_*/UPD_*)의 짝 |
| 단위 (UNIT), 원천 (SRC), 문서 (DOC) | UNIT_CD, SRC_DOC_NO | 승인 | 기존 단어로 대체 불가 |
| 제조 (MFG), 양품 (GOOD), 불량 (DEFECT) | MFG_DT, GOOD_QTY | 승인 | 생산·품질 영역 단어 |
| 유효기한 (EXP) | EXP_DT | 승인 | "유효기간"과 구별되도록 정의를 함께 등록 |
| 유효기간 (SHELF_LIFE) + 개월수 (MM) | SHELF_LIFE_MM | 조건부 | 유효기간은 복합 단어로 승인. MM을 분류어로 늘릴지는 아래 판단 |
| 사업 (BIZ) | BIZ_TP_NM (업종명) | 승인 | 사업 + 유형 = 업종. BIZ_REG_NO와 약어가 어긋나지 않음 |
| BOM | BOM_QTY | 승인 | 업계 통용 약어 그대로. 한글 단어도 "BOM"으로 등록 |
| 합계 (TOT), 변경 (CHG), 로그 (LOG) | 집계·이력 테이블 | 승인 | |
| 병원 (HOSP), 약국 (PHAR), 도매 (WHSL) | TB_CUST_HOSP 등 | 승인 | 서브타입 테이블명. 단 거래처유형 코드값과 이름이 겹치니 정의에 "거래처 서브타입" 명시 |
| 병상 (BED), 수 (CNT) | BED_CNT | 승인 | 수(CNT)는 분류어로 등록, 도메인 건수N10 |
| 여신 (CRDT), 한도 (LMT) | CRDT_LMT_AMT | 승인 | |
| 주 (MAIN) | MAIN_HOSP_CUST_NO | 반려 → 수정 승인 | "주"는 한 글자라 주(週)·주식과 헷갈림. "주거래 (MAIN)"로 등록 |
| 변경전 (BF), 변경후 (AF) | BF_UPRC, AF_UPRC | 수정 승인 | "변경전"은 변경 + 전의 조합. 단어는 "이전 (BF)", "이후 (AF)"로 등록하고 용어로 "이전단가" |
| 공통 (CMM), 그룹 (GRP), 정렬 (SORT) | Day 9 공통코드 | 승인 | |

판정의 핵심 질문은 세 가지입니다. 기존 단어 조합으로 표현되는가(변경전 → 이전), 다른 뜻과 헷갈리지 않는가(주 → 주거래), 약어가 기존 약어와 부딪히지 않는가.

### 표준도메인과 도메인 위반 점검

```sql
CREATE TABLE lab.tb_std_domain (               -- 표준도메인
  domain_nm   VARCHAR(30) PRIMARY KEY,
  cls_abbr_nm VARCHAR(20) NOT NULL,            -- 분류어 약어
  data_tp     VARCHAR(10) NOT NULL,
  data_len    NUMERIC(4),
  data_scale  NUMERIC(2)
);
INSERT INTO lab.tb_std_domain VALUES
 ('번호V10','NO','VARCHAR',10,NULL), ('번호V14','NO','VARCHAR',14,NULL), ('번호V20','NO','VARCHAR',20,NULL),
 ('사업자등록번호V12','BIZ_REG_NO','VARCHAR',12,NULL),
 ('코드V2','CD','VARCHAR',2,NULL), ('코드V5','CD','VARCHAR',5,NULL), ('코드V10','CD','VARCHAR',10,NULL),
 ('명V50','NM','VARCHAR',50,NULL), ('명V100','NM','VARCHAR',100,NULL),
 ('일자D','DT','DATE',NULL,NULL), ('일시TS','DTM','TIMESTAMP',NULL,NULL), ('여부C1','YN','CHAR',1,NULL),
 ('수량N10','QTY','NUMERIC',10,0), ('소요량N12_4','QTY','NUMERIC',12,4),
 ('금액N15','AMT','NUMERIC',15,0), ('단가N15','UPRC','NUMERIC',15,0), ('순번N4','SEQ','NUMERIC',4,0);

-- 컬럼의 분류어(마지막 조각)와 실제 타입이 등록된 도메인 중 어느 것과도 맞지 않는 컬럼
WITH col AS (
  SELECT c.table_name, c.column_name,
         CASE WHEN c.column_name LIKE '%biz_reg_no' THEN 'BIZ_REG_NO'
              ELSE upper(substring(c.column_name FROM '[^_]+$')) END AS cls_abbr_nm,
         CASE c.data_type WHEN 'character varying' THEN 'VARCHAR' WHEN 'character' THEN 'CHAR'
                          WHEN 'numeric' THEN 'NUMERIC' WHEN 'date' THEN 'DATE'
                          WHEN 'timestamp without time zone' THEN 'TIMESTAMP' END AS data_tp,
         COALESCE(c.character_maximum_length, c.numeric_precision) AS data_len,
         c.numeric_scale AS data_scale
    FROM information_schema.columns c
   WHERE c.table_schema = 'erp'
)
SELECT cls_abbr_nm, data_tp, data_len, data_scale,
       string_agg(table_name || '.' || column_name, ', ' ORDER BY table_name) AS cols
  FROM col
 WHERE NOT EXISTS (SELECT 1 FROM lab.tb_std_domain d
                    WHERE d.cls_abbr_nm = col.cls_abbr_nm
                      AND d.data_tp = col.data_tp
                      AND d.data_len IS NOT DISTINCT FROM col.data_len
                      AND COALESCE(d.data_scale, 0) = COALESCE(col.data_scale, 0))
 GROUP BY cls_abbr_nm, data_tp, data_len, data_scale
 ORDER BY 1, 3;
```

다섯 묶음이 나옵니다. 회사코드 CO_CD(VARCHAR(4), 5개 테이블), 지역코드 RGN_CD(VARCHAR(3)), 업종명 BIZ_TP_NM(VARCHAR(30)), 유효기간 SHELF_LIFE_MM(분류어 MM에 도메인 없음), 재고수량 INV_QTY(NUMERIC(12)). 위반을 보면 고칠 대상과 도메인을 늘릴 대상을 나눠야 합니다.

| 위반 | 판단 |
|---|---|
| CO_CD VARCHAR(4) | 그룹 회사코드는 4자리가 정해진 체계. 도메인 "회사코드V4"를 추가 (예외를 목록으로 관리) |
| RGN_CD VARCHAR(3) | 코드V5로 맞출지, 지역 체계가 3자리로 고정인지 확인 후 결정 |
| BIZ_TP_NM VARCHAR(30) | 명V50으로 맞춤. 30자 근거가 없음 |
| SHELF_LIFE_MM | 분류어를 늘리는 대신 "수 (CNT)"를 쓰는 용어 "유효기간개월수 (SHELF_LIFE_MM_CNT)"로 바꾸는 안(이때 MM은 일반 단어 "개월"로 등록하고 CNT가 분류어)과, MM을 분류어로 인정하는 안 중 택일. 운영 중인 컬럼명 변경 비용이 크면 후자 |
| INV_QTY NUMERIC(12) | 재고는 거래수량보다 커질 수 있다는 근거가 있으면 "재고수량N12" 추가, 없으면 수량N10과 통일 |

### 표준용어사전 샘플과 금칙어 점검

```sql
CREATE TABLE lab.tb_std_term (                 -- 표준용어
  term_nm    VARCHAR(50)  PRIMARY KEY,
  phys_nm    VARCHAR(30)  NOT NULL UNIQUE,
  domain_nm  VARCHAR(30)  NOT NULL REFERENCES lab.tb_std_domain (domain_nm),
  term_desc  VARCHAR(300) NOT NULL
);
INSERT INTO lab.tb_std_term VALUES
 ('거래처번호','CUST_NO','번호V10','매출처(병원·약국·도매상)를 식별하는 번호. C + 6자리'),
 ('거래처유형코드','CUST_TP_CD','코드V2','거래처 분류. 표준코드 CUST_TP_CD'),
 ('주문번호','ORD_NO','번호V14','SO + 연월 6자리 + 일련 4자리'),
 ('주문금액','ORD_AMT','금액N15','주문수량 × 단가. 원 단위, 부가세 제외'),
 ('로트번호','LOT_NO','번호V20','제조 단위 식별 번호'),
 ('유효기한일자','EXP_DT','일자D','해당 로트를 사용할 수 있는 마지막 날짜 (당일 포함)'),
 ('고객명','CUST_NM','명V100','거래처 이름');

-- 용어명에 금칙어가 들어간 용어 찾기
SELECT t.term_nm, t.phys_nm, s.syn_word_nm AS forbidden_word, s.std_word_nm AS use_instead
  FROM lab.tb_std_term t
  JOIN lab.tb_std_word_syn s ON s.syn_tp_cd = '01' AND t.term_nm LIKE '%' || s.syn_word_nm || '%';
```

두 행이 나옵니다. '고객명'은 금칙어 "고객"에 걸려 "거래처명"으로 바꿔야 합니다. 물리명 CUST_NM은 맞는데 한글 용어명만 틀렸고, 한글 용어명은 화면 라벨·BI 필드명으로 그대로 쓰이므로 물리명만 맞으면 된다는 생각은 위험합니다. '유효기한일자'는 금칙어 "일"이 '일자' 안에 들어 있어 걸린 **오탐**입니다. 한 글자 금칙어는 LIKE가 아니라 단어 단위로 쪼개서 비교해야 합니다.

## Before / After

**Before: 계열사마다 각자의 이름**

| 회사 | 거래처번호 | 유효기간 | 주문금액 |
|---|---|---|---|
| 한빛제약 | CUST_NO VARCHAR(10) | SHELF_LIFE_MM (개월수) | ORD_AMT NUMERIC(15) |
| 한빛푸드 | CLNT_ID VARCHAR(15) | EXPIRE_PERIOD (날짜) | ORDER_PRICE NUMBER |
| 한빛로지스 | CUSTOMER_CODE VARCHAR(20) | 없음 | 없음 |

**After: 그룹 표준용어로 정렬한 DW 컬럼**

| 표준용어 | 물리명 | 도메인 | 원천 매핑 |
|---|---|---|---|
| 거래처번호 | CUST_NO | 번호V10 (그룹 통합번호는 Day 13 MDM) | CUST_NO / CLNT_ID / CUSTOMER_CODE |
| 유효기간개월수 | SHELF_LIFE_MM_CNT (또는 승인된 이름) | 개월수N3 | 제약 SHELF_LIFE_MM |
| 유효기한일자 | EXP_DT | 일자D | 푸드 EXPIRE_PERIOD (이름은 "기간"이지만 실제로는 기한) |
| 주문금액 | ORD_AMT | 금액N15 | ORD_AMT / ORDER_PRICE |

원천 이름을 바꾸라는 것이 아닙니다. 원천은 그대로 두고 **DW와 신규 시스템은 표준으로**, 그 사이는 매핑정의서로 연결합니다.

## 시니어는 이렇게 판단한다

| 판단 지점 | 이럴 땐 A | 저럴 땐 B |
|---|---|---|
| 기존 운영계에 표준 적용 | 신규 테이블·DW·마트는 표준 강제 | 운영 중인 패키지 ERP 컬럼은 바꾸지 않고 매핑으로 흡수 |
| 신청 단어 | 기존 단어 조합으로 안 되고 뜻이 분명하면 승인 | 조합 가능하거나 동음이의 위험이 있으면 반려·수정 |
| 도메인 위반 | 근거 없는 길이 차이면 표준에 맞춤 | 업무상 고정 체계(회사코드 4자리)면 예외 도메인 등록 + 사유 |
| 분류어 추가 | 기존 분류어로 값의 성격이 설명 안 되면 추가 | 대부분은 기존 분류어(수, 수량, 번호)로 충분 |

표준화의 실패 원인은 대개 사전의 질보다 **집행**입니다. 설계 리뷰에서 테이블정의서를 사전과 자동 대조하는 단계(위 쿼리들)를 넣지 않으면 사전은 문서함 속에서 낡아 갑니다.

## 흔한 실수 3가지

1. **약어부터 정하고 한글 정의를 비워 두는 실수.** "EXP"만 등록하면 누군가는 비용(expense)으로, 누군가는 유효기한으로 씁니다. 단어마다 한 줄 정의와 쓰지 말아야 할 비슷한 단어를 함께 적습니다.
2. **도메인을 컬럼마다 하나씩 만드는 실수.** "주문수량N10", "출고수량N10", "입고수량N10"을 따로 두면 도메인이 아니라 컬럼 목록입니다. 도메인은 값의 형식 단위로 묶습니다.
3. **운영 중인 원천 컬럼명을 표준에 맞춰 바꾸자고 하는 실수.** 패키지·인터페이스·리포트가 모두 깨집니다. 표준은 신규 설계와 DW에 적용하고 원천은 매핑으로 연결합니다.

## 셀프 체크 질문

**Q1. 표준단어·표준도메인·표준용어·표준코드의 관계를 한빛제약 예시로 설명해 보세요.**

:::answer 모범 답안 보기
표준단어는 더 쪼개지 않는 업무 단어와 약어입니다(거래처 CUST, 유형 TP, 코드 CD). 표준용어는 단어를 조합한 컬럼 이름이며(거래처유형코드 CUST_TP_CD), 마지막 단어인 분류어 "코드"가 도메인 후보를 정합니다. 표준도메인은 값의 형식으로, 거래처유형코드는 코드V2 = VARCHAR(2)를 씁니다. 표준코드는 그 용어가 가질 수 있는 값 목록(01 병원, 02 약국, 03 도매상)입니다. 순서는 단어 → 용어 → 도메인 지정 → 코드형이면 코드 정의이고, 사전에 없는 단어는 먼저 신청·심의를 거칩니다.
:::

**Q2. 설계자가 "변경전단가"를 위해 BF라는 단어를 신청했습니다. 어떻게 심의하시겠습니까?**

:::answer 모범 답안 보기
"변경전"은 "변경"과 "전"의 조합이라 단어로는 너무 큽니다. 단어로는 "이전 (BF)"과 "이후 (AF)"를 등록하고, 용어를 "이전단가 (BF_UPRC)"로 만들도록 수정 승인하겠습니다. 이렇게 하면 이전재고수량, 이전상태코드처럼 같은 단어를 재사용할 수 있습니다. 심의 기준은 기존 단어 조합으로 표현되는지, 다른 뜻과 헷갈리지 않는지, 약어가 겹치지 않는지 세 가지입니다.
:::

**Q3. 한빛푸드 원천의 EXPIRE_PERIOD 컬럼을 그룹 DW에 넣으려 합니다. 무엇을 확인하겠습니까?**

:::answer 모범 답안 보기
이름보다 값을 먼저 봅니다. 이름은 "기간"이지만 값이 날짜라면 유효기한(EXP_DT)이고, 개월수라면 유효기간입니다. 두 단어는 동음이의 위험이 크므로 표준 사전에 각각 정의돼 있어야 하고, 매핑정의서에 "EXPIRE_PERIOD → EXP_DT (값 확인 결과 날짜)"처럼 판단 근거를 적습니다. 값 프로파일링(최솟값·최댓값·형식)과 한빛푸드 담당자 확인을 함께 합니다. 같은 이름에 다른 값이 섞여 있다면(일부는 날짜, 일부는 개월수) 품질 이슈로 올립니다.
:::

## 오늘의 과제

**과제 1.** 표준용어를 넣을 때 물리명이 사전의 단어로만 조립됐는지 검사하는 쿼리를 작성하세요. 위 표준용어 7건 중 물리명에 미등록 약어가 들어간 용어를 찾습니다. 결과 모양은 `term_nm, phys_nm, bad_abbr`입니다.

:::answer 해설 보기
물리명을 언더스코어로 쪼개 각 조각을 표준단어 약어와 비교합니다. 복합 단어(BIZ_REG_NO)는 먼저 한 덩어리로 바꿔 둡니다.

```sql
SELECT t.term_nm, t.phys_nm, x.tok AS bad_abbr
  FROM lab.tb_std_term t
 CROSS JOIN LATERAL regexp_split_to_table(replace(t.phys_nm, 'BIZ_REG_NO', 'BIZREGNO'), '_') AS x (tok)
 WHERE x.tok <> 'BIZREGNO'
   AND x.tok NOT IN (SELECT abbr_nm FROM lab.tb_std_word)
 ORDER BY t.term_nm;
```

유효기한일자(EXP_DT)의 EXP 한 건이 나옵니다. 신청 심의에서 승인했지만 아직 사전에 넣지 않았기 때문입니다. "승인"과 "등록"이 따로 놀면 이런 일이 생깁니다.
:::

**과제 2.** 승인된 신청 단어 중 사용(USE), 발주(PO), 유효기한(EXP)을 표준단어에 등록하고, 과제 1을 다시 돌려 0건이 되는지 확인하세요. 이어서 앞의 "미등록 조각" 쿼리를 다시 돌리면 몇 개가 남는지 확인합니다.

:::answer 해설 보기
```sql
INSERT INTO lab.tb_std_word (word_nm, abbr_nm, cls_word_yn, word_desc) VALUES
 ('사용', 'USE', 'N', '사용여부 등'),
 ('발주', 'PO',  'N', '구매처에 품목을 주문하는 행위. 판매 주문(ORD)과 구별'),
 ('유효기한', 'EXP', 'N', '로트를 사용할 수 있는 마지막 날짜. 유효기간(개월수)과 구별');

SELECT COUNT(*) AS remain_cnt
  FROM (SELECT DISTINCT upper(regexp_split_to_table(replace(column_name, 'biz_reg_no', 'bizregno'), '_')) AS tok
          FROM information_schema.columns
         WHERE table_schema = 'erp') x
 WHERE tok <> 'BIZREGNO'
   AND tok NOT IN (SELECT abbr_nm FROM lab.tb_std_word);
```

과제 1은 0건이 되고, 미등록 조각은 15개에서 12개로 줄어듭니다. 단어 정의에 "구별해야 할 비슷한 단어"를 적어 둔 것이 표준단어 품질의 핵심입니다.
:::

## 실무 산출물 연결

| 산출물 | 무엇을 적나 |
|---|---|
| 표준단어사전 | 단어, 영문 약어, 영문명, 분류어 여부, 정의, 이음동의어·금칙어, 등록일·신청자. |
| 표준도메인사전 | 도메인명, 분류어, 데이터 타입·길이·소수자리, 허용 예외와 사유. |
| 표준용어사전 | 용어명, 물리명, 도메인, 정의, 표준코드 여부(코드형이면 코드그룹). |
| 표준코드정의서 | Day 9의 코드 목록. 용어사전의 코드형 용어와 1:1. |
| 데이터 표준 관리 지침 | 명명규칙(주제어 + 수식어 + 분류어, 물리명 길이 상한), 신청·심의 절차, 예외 승인 권한. |
| 테이블정의서 검토 결과 | 표준 미준수 컬럼 목록(미등록 단어, 도메인 위반)과 조치. |

## 참고할 원전

- 한국데이터산업진흥원(K-DATA), "데이터아키텍처 전문가 가이드"(DAP·DAsP 공통 교재) — 데이터 표준화 과목: 표준 단어·도메인·용어·코드, 표준화 절차.
- 행정안전부, 「공공기관의 데이터베이스 표준화 지침」 — 공공 부문의 표준 용어·도메인 관리 기준.
- DAMA International, "DAMA-DMBOK: Data Management Body of Knowledge", 2nd ed. (Technics Publications, 2017) — Metadata Management 장 (명명 표준과 비즈니스 용어집).
