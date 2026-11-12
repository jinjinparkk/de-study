# 한빛제약그룹 세계관 (필수 정리 30일 공통)

모든 Day의 예시는 이 세계관 안에서만 듭니다. 회사·사람·제품·거래처는 전부 **가상**입니다. 실존 기업·병원·약국·제품명을 쓰지 않습니다.

## 1. 그룹과 계열사

| 회사코드 (CO_CD) | 회사명 | 업종 | 주요 시스템 | 데이터 예시에 자주 나오는 업무 |
|---|---|---|---|---|
| 1000 | 한빛제약 | 의약품 제조·영업 | ERP(영업·구매·회계), SFA(영업활동) | 병원·약국·도매상 주문, 약가·단가, 영업실적 |
| 2000 | 한빛로지스 | 물류 | WMS | 입고·출고·재고, 창고·로케이션 |
| 3000 | 한빛푸드 | 식음료 | ERP | 대리점 주문, 유통기한 관리 |
| 4000 | 한빛케미칼 | 원료의약품·화학 제조 | ERP, MES | BOM, 작업지시, 생산실적, 로트 |
| 5000 | 한빛건설 | 건설 | ERP(프로젝트) | 현장별 원가, 자재 구매 |
| 9000 | 한빛정보기술 | 그룹 IT 서비스 | 그룹 DW (구축 중) | **나의 소속**. 데이터 아키텍트로 그룹 DW 구축 리딩 |

- 계열사 ERP 운영계 DB는 **Oracle**이라고 가정합니다. 하지만 학습용 실행 환경은 **PostgreSQL**입니다. 모든 예시 SQL은 `schema/` 의 공통 스키마 위에서 PostgreSQL로 실행됩니다.
- Oracle과 문법이 다른 곳은 SQL 바로 아래 `:::note Oracle 차이` 상자에 각주로 적습니다(예: `VARCHAR2`/`NUMBER`, `MERGE` 문법, `CONNECT BY`, `DATE` 리터럴, `NVL` vs `COALESCE`).
- 계열사마다 ERP가 따로 구축돼 있어 **거래처·품목 마스터가 계열사별로 흩어져 있습니다** (Day 13 MDM의 출발점).
- 그룹 DW 프로젝트: 1차 범위 = 한빛제약 영업실적 + 한빛로지스 출고·재고. BI는 Power BI(경영진·영업), Tableau(물류·생산 분석).

## 1-1. 공통 스키마 (실행 환경)

- `schema/00_base.sql`: 공통 테이블 DDL + 샘플 INSERT (PostgreSQL 15 이상 기준). 모든 Day의 SQL은 이 파일을 먼저 실행한 DB에서 돌아가야 합니다.
- 주차별로 테이블이 더 필요하면 `schema/NN_weekN_*.sql` 로 **추가 파일**을 만들고 Day 본문에 "먼저 실행할 파일"을 적습니다. 기존 파일의 테이블 정의는 바꾸지 않습니다.
- 스키마 이름: 운영계 `erp`, DW `dw`. (예: `erp.tb_cust`, `dw.dim_cust`) PostgreSQL은 따옴표 없는 이름을 소문자로 다루므로 SQL에서는 소문자로 쓰고, 문서·표에서는 대문자 물리명(TB_CUST)으로 표기합니다.

## 2. 표준 약어 (표준단어 → 영문 약어)

물리명은 `대문자_언더스코어`. 아래 약어만 씁니다(Day 10에서 이 표 자체를 다룹니다).

| 표준단어 | 약어 | 표준단어 | 약어 | 표준단어 | 약어 |
|---|---|---|---|---|---|
| 거래처(매출처) | CUST | 구매처 | VNDR | 품목 | ITEM |
| 주문 | ORD | 출고 | SHIP | 입고 | RCV |
| 재고 | INV | 창고 | WH | 로트 | LOT |
| 사원 | EMP | 부서 | DEPT | 회사 | CO |
| 번호 | NO | 코드 | CD | 명 | NM |
| 일자 | DT | 일시 | DTM | 여부 | YN |
| 수량 | QTY | 금액 | AMT | 단가 | UPRC |
| 유형 | TP | 상태 | STAT | 순번 | SEQ |
| 시작 | STRT | 종료 | END | 적용 | APLY |
| 상위 | PRNT | 하위 | CHLD | 작업지시 | WO |
| 생산 | PROD | 실적 | RSLT | 전표 | SLIP |
| 계정 | ACCT | 차변 | DR | 대변 | CR |
| 지역 | RGN | 등록 | REG | 사업자등록번호 | BIZ_REG_NO |

- 테이블 접두어: 운영계 `TB_`, DW 스테이징 `STG_`, ODS `ODS_`, 차원 `DIM_`, 팩트 `FCT_`, 마트 `DM_`.
- 서로게이트 키 접미어 `_SK`, 알 수 없는 차원 값은 `-1`.
- 감사 컬럼: `REG_DTM`, `REG_ID`, `UPD_DTM`, `UPD_ID` (DW 적재 시 `LOAD_DTM`, `BATCH_ID`).

## 3. 핵심 운영계 테이블 (한빛제약 ERP 중심)

예시에서 이 이름과 컬럼을 그대로 씁니다. 필요하면 컬럼을 **추가**해도 되지만 이름을 바꾸지 않습니다.

| 테이블 | 논리명 | 주요 컬럼 |
|---|---|---|
| TB_CUST | 거래처 | CUST_NO, CUST_NM, CUST_TP_CD(01 병원, 02 약국, 03 도매상), BIZ_REG_NO, RGN_CD, USE_YN |
| TB_ITEM | 품목 | ITEM_CD, ITEM_NM, ITEM_TP_CD(FG 완제품, RM 원료, PM 포장재), UNIT_CD(EA, BOX), USE_YN |
| TB_EMP | 사원 | EMP_NO, EMP_NM, DEPT_CD |
| TB_DEPT | 부서 | DEPT_CD, DEPT_NM, PRNT_DEPT_CD |
| TB_ORD | 주문(헤더) | ORD_NO, ORD_DT, CUST_NO, EMP_NO, ORD_STAT_CD(10 접수, 20 확정, 30 출고완료, 90 취소) |
| TB_ORD_DTL | 주문상세 | ORD_NO, ORD_SEQ, ITEM_CD, ORD_QTY, UPRC, ORD_AMT |
| TB_ITEM_UPRC_HIST | 품목단가이력 | ITEM_CD, UPRC_TP_CD(01 기준가, 02 보험상한가), APLY_STRT_DT, APLY_END_DT, UPRC |
| TB_CUST_EMP_HIST | 거래처담당이력 | CUST_NO, EMP_NO, APLY_STRT_DT, APLY_END_DT |
| TB_WH | 창고 (한빛로지스) | WH_CD, WH_NM, CO_CD |
| TB_SHIP / TB_SHIP_DTL | 출고 / 출고상세 | SHIP_NO, SHIP_DT, WH_CD, ORD_NO / SHIP_NO, SHIP_SEQ, ITEM_CD, LOT_NO, SHIP_QTY |
| TB_RCV / TB_RCV_DTL | 입고 / 입고상세 | RCV_NO, RCV_DT, WH_CD, VNDR_NO / RCV_NO, RCV_SEQ, ITEM_CD, LOT_NO, RCV_QTY |
| TB_INV_DAILY | 일별재고 | INV_DT, WH_CD, ITEM_CD, LOT_NO, INV_QTY |
| TB_BOM | BOM (한빛케미칼) | PRNT_ITEM_CD, CHLD_ITEM_CD, BOM_QTY, APLY_STRT_DT, APLY_END_DT |
| TB_WO / TB_PROD_RSLT | 작업지시 / 생산실적 | WO_NO, ITEM_CD, WO_QTY / WO_NO, PROD_DT, LOT_NO, GOOD_QTY, DEFECT_QTY |
| TB_VNDR / TB_PO / TB_PO_DTL | 구매처 / 발주 / 발주상세 | VNDR_NO, VNDR_NM / PO_NO, PO_DT, VNDR_NO / PO_NO, PO_SEQ, ITEM_CD, PO_QTY, UPRC |
| TB_SLIP / TB_SLIP_DTL | 전표 / 전표상세 | SLIP_NO, SLIP_DT, CO_CD / SLIP_NO, SLIP_SEQ, ACCT_CD, DR_AMT, CR_AMT |

## 4. 공통 샘플 데이터 (이 값들을 재사용)

거래처 (TB_CUST)

| 거래처번호 (CUST_NO) | 거래처명 (CUST_NM) | 거래처유형코드 (CUST_TP_CD) | 지역코드 (RGN_CD) |
|---|---|---|---|
| C000101 | 청솔내과의원 | 01 병원 | SEL |
| C000102 | 미래종합병원 | 01 병원 | GGD |
| C000201 | 햇살약국 | 02 약국 | SEL |
| C000202 | 늘봄약국 | 02 약국 | BSN |
| C000301 | 바른팜유통 | 03 도매상 | GGD |

품목 (TB_ITEM)

| 품목코드 (ITEM_CD) | 품목명 (ITEM_NM) | 품목유형 (ITEM_TP_CD) | 단위 (UNIT_CD) |
|---|---|---|---|
| P10001 | 한빛펜정 500mg 30T | FG | BOX |
| P10002 | 한빛록스정 60mg 100T | FG | BOX |
| P10003 | 한빛시럽 100mL | FG | EA |
| R20001 | 원료A(주성분) | RM | KG |
| M30001 | PTP 알루미늄 호일 | PM | ROLL |

사원 (TB_EMP): E1001 김도윤(서울1팀), E1002 이서연(서울1팀), E1003 박지훈(경기팀), E1004 최하은(부산팀)

창고 (TB_WH): W01 이천물류센터, W02 양산물류센터

- 날짜 예시는 2026년(예: 2026-03-02)으로 씁니다. 금액은 원 단위.
- 단가·약가 숫자는 **가상**임을 전제로 둥근 값(예: 3,200원)으로 씁니다. 실제 약가 제도의 수치(인하율·고시 주기 등)는 확인되지 않았다면 쓰지 않습니다.

## 5. 등장인물 (회의·의사결정 장면용)

- 나: 한빛정보기술 데이터 아키텍트 (그룹 DW PL)
- 한빛제약 영업기획팀 정 과장: 영업실적 대시보드 요청자
- 한빛로지스 물류운영팀 한 대리: 출고·재고 데이터 담당
- 한빛정보기술 ERP 운영팀: 운영계 DB 담당 (DB 변경 승인권)
- 그룹 경영지원실: 그룹 공통 지표·마스터 오너

## 6. Week 1에서 추가된 설정 (이후 Day에서 재사용)

모두 각 Day SQL 안에서 `lab` 스키마에 만들거나 본문에서만 쓰는 값입니다. 다시 쓸 때는 같은 이름·값을 씁니다.

- 선분이력 규칙(Day 7): `DATE` 기준, 종료일 포함, 현재 = `9999-12-31`, 다음 시작일 = 이전 종료일 + 1. 일시(DTM) 이력만 반열림 구간 `[시작, 종료)`.
- 주문상세유형코드 `ORD_DTL_TP_CD` 01 일반, 02 증정 (Day 4). 증정 라인 예: SO2026030003 3번 라인, P10001 10 BOX, 0원.
- 거래처 서브타입(Day 6): `TB_CUST_HOSP`(HOSP_TP_CD 01 의원/02 병원/03 종합병원, BED_CNT), `TB_CUST_PHAR`(MAIN_HOSP_CUST_NO), `TB_CUST_WHSL`(CRDT_LMT_AMT). 값: C000102 병상 300, C000201 주거래병원 C000101, C000301 여신한도 5천만 원.
- BOM 확장(Day 6): 품목유형 SF(반제품), S40001 록스정 나정 벌크(KG), S40002 록스정 과립(KG), R20002 부형제B(KG), M30002 단상자(EA, ~2026-04-30), M30003 단상자 개선형(EA, 2026-05-01~).
- 한빛로지스 사원(Day 5): E2001 한소율·E2002 오민재(W01), E2003 윤가람(W02).
- 품목단가변경로그(Day 7): `TB_ITEM_UPRC_CHG_LOG` (CHG_SEQ, CHG_DTM, CHG_TP_CD I/U/D, BF_*/AF_* 컬럼, CHG_ID).
- Week 1에서 쓰였지만 표준 약어 표에 없는 단어(Day 10 "표준단어 신청" 예시로 쓰기): TOT(합계), HOSP(병원), PHAR(약국), WHSL(도매), BED, CNT(수), MAIN(주), CRDT(여신), LMT(한도), CHG(변경), LOG, BF(변경전), AF(변경후).
- 00_base.sql 의 의도된 빈틈(Day 2에서 "ERP 팀에 물어볼 질문"으로 다룸): 매출전표가 1건뿐, TB_SLIP.SRC_DOC_NO 에 문서유형 없음(주문번호가 들어감), 입고에 발주번호 없음, TB_ORD_DTL 에 UPD_DTM 없음, 발주 회사(4000)와 입고 창고(W01, 2000) 소속 불일치, CHECK 제약 없음.

## 7. Week 3에서 추가된 설정 (DW)

- 공통 DW 스키마 `schema/10_dw.sql` (dw): DIM_DATE(DATE_SK = YYYYMMDD, 2025~2026, -1 행), DIM_CUST(SCD2, 담당 사원 추적, C000101 은 SK 1·2 두 버전), DIM_ITEM, DIM_EMP(부서·본부 펼침), DIM_WH, DIM_LOT, FCT_ORD_LINE(주문상세 grain, 취소 포함, 상태코드 보유), FCT_SHIP_LINE(출고상세 grain, 출고일·주문일 두 역할, ship_amt = 출고수량 × 주문단가), FCT_INV_DAILY(2026-03-31 하루치). 모든 차원 -1 행, LOAD_DTM, BATCH_ID('INIT'). 팩트 FK 는 NULL 대신 -1.
- 수금(Day 17): lab.tb_coll, CL2026040001 (2026-04-10, SO2026030001, 90,200). 표준단어 신청 대상 COLL(수금).
- 3월 영업목표(Day 18): E1001 100,000 / E1002 150,000 / E1003 2,000,000 / E1004 50,000.
- 2026-05-01 배치 시나리오(Day 19, 배치ID B20260502): C000202 담당 E1004 → E1003, C000102 거래처명 '미래종합병원(본원)' 정정(Type 1), 신규 C000203 새봄약국(02, SEL, 담당 E1002).
- 프로모션 PRM2603(Day 20): 약국 C000201·C000202 × P10001, 3월. C000301 공동 담당 E1003 0.6 / E1004 0.4. 헤더 할인 SO2026030003 50,000, 배송비 SO2026030001 3,000 (원 미만 내림, 남는 원은 금액 최대 라인).
- 수불유형(Day 21): OPEN / RCV_PO / RCV_PROD / SHIP. 기초재고 L250620 500, L250901 210, L251110 500. DIM_CO(회사)·현장 차원은 2차 범위.

## 8. Week 2에서 추가된 설정

- 코드(Day 9): 공통코드 lab.tb_cmm_cd_grp / tb_cmm_cd (CD_GRP_CD = 컬럼 물리명), 개별 코드 lab.tb_ord_stat (STEP_SEQ, SHIP_END_YN, SALES_YN), 가상 주문상태 25 출고지시.
- 표준(Day 10): 승인 단어 USE, PO, UPD, UNIT, SRC, DOC, MFG, GOOD, DEFECT, EXP, SHELF_LIFE, BIZ, BOM, MAIN(주거래), BF/AF(이전/이후), CMM, GRP, SORT. 금칙어: 고객 → 거래처, 날짜·일 → 일자.
- 품질·감사(Day 12): lab.tb_dq_rule / tb_dq_rslt (DQ01~06), 감사 추적 lab.tb_audit_trail (사유·사용자는 set_config('app.chg_rsn'/'app.user_id')), 생산실적 정정 L260105 양품 2000→1990·불량 12→22.
- MDM·로트(Day 13): 계열사 원천 거래처 F-0091 (주)바른팜유통, F-0102 햇살 약국, L-0077 바른팜 유통, L-0080 미래종합병원 → 그룹번호 G000001~G000004. 투입실적 lab.tb_prod_input (L260105 ← R251215 30 KG, M251130 4 ROLL). 유효기한 임박 기준 18개월(가상).
- 반품(Day 14): lab.tb_rtn / tb_rtn_dtl / tb_rtn_stat, 반품사유 RTN_RSN_CD 01 임박 / 02 파손 / 03 오배송, RT2026030001 (햇살약국 P10001 L250901 2 BOX, P10003 L250620 5 EA). 신청 단어 RTN, RSN.

## 9. Week 4에서 추가된 설정

- 신규 기준정보(Day 22~23): 거래처 C000204 다온약국(02, SEL, 담당 E1002, 2026-04-01~), 품목 P10004 한빛펜정 250mg 30T(FG, BOX, 36개월).
- 신규 주문: SO2026040003(Day 22, C000301, P10002 50 BOX), SO2026040004~040007(Day 23 적재 오류·재처리 예시).
- 배치ID B20260404·B20260405·B20260406, 오류 규칙 LKP_CUST·LKP_ITEM·LKP_DATE·QTY_NEG·AMT_CALC (W 경고 / E 거부).
- 작업 ID(Day 24): STG_ORD, STG_SHIP, STG_CUST, DIM_CUST, FCT_ORD_LINE, FCT_SHIP_LINE, CHK_RECON, DM_SALES, BI_PBI_SALES.
- 문서(Day 28): ADR-001 ELT, ADR-002 스타 스키마 + OBT 뷰, 비기능 요구사항 NFR-01~06(07:00 SLA 등, 가상).
