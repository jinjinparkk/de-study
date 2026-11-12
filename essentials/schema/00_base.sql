-- =====================================================================
-- 한빛제약그룹 공통 스키마 (필수 정리 30일) — PostgreSQL 15 이상
--   실행: psql -f 00_base.sql   (빈 DB에서 실행. 다시 실행해도 처음 상태로 돌아갑니다)
--   운영계 = 스키마 erp, DW = 스키마 dw (DW 테이블은 Week 3~4 추가 파일에서 만듭니다)
--   모든 회사·사람·제품·거래처·숫자는 가상입니다.
--   Oracle 차이: VARCHAR → VARCHAR2, NUMERIC → NUMBER, TIMESTAMP 기본값 SYSTIMESTAMP,
--                스키마 = 사용자(계정). 날짜 리터럴 DATE '2026-03-02' 는 양쪽 공통.
-- =====================================================================

DROP SCHEMA IF EXISTS dw CASCADE;
DROP SCHEMA IF EXISTS erp CASCADE;
CREATE SCHEMA erp;
CREATE SCHEMA dw;

-- ---------------------------------------------------------------------
-- 1. 조직·기준정보
-- ---------------------------------------------------------------------
CREATE TABLE erp.tb_co (               -- 회사
  co_cd        VARCHAR(4)   PRIMARY KEY,          -- 회사코드
  co_nm        VARCHAR(50)  NOT NULL,             -- 회사명
  biz_tp_nm    VARCHAR(30)  NOT NULL              -- 업종명
);

CREATE TABLE erp.tb_dept (             -- 부서
  dept_cd      VARCHAR(10)  PRIMARY KEY,          -- 부서코드
  dept_nm      VARCHAR(50)  NOT NULL,             -- 부서명
  prnt_dept_cd VARCHAR(10)  REFERENCES erp.tb_dept(dept_cd),  -- 상위부서코드
  co_cd        VARCHAR(4)   NOT NULL REFERENCES erp.tb_co(co_cd)
);

CREATE TABLE erp.tb_emp (              -- 사원
  emp_no       VARCHAR(10)  PRIMARY KEY,          -- 사원번호
  emp_nm       VARCHAR(50)  NOT NULL,             -- 사원명
  dept_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_dept(dept_cd),
  use_yn       CHAR(1)      NOT NULL DEFAULT 'Y'
);

CREATE TABLE erp.tb_cust (             -- 거래처(매출처)
  cust_no      VARCHAR(10)  PRIMARY KEY,          -- 거래처번호
  cust_nm      VARCHAR(100) NOT NULL,             -- 거래처명
  cust_tp_cd   VARCHAR(2)   NOT NULL,             -- 거래처유형코드 01 병원, 02 약국, 03 도매상
  biz_reg_no   VARCHAR(12),                       -- 사업자등록번호 (가상)
  rgn_cd       VARCHAR(3)   NOT NULL,             -- 지역코드 SEL 서울, GGD 경기, BSN 부산
  use_yn       CHAR(1)      NOT NULL DEFAULT 'Y',
  reg_dtm      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE erp.tb_item (             -- 품목
  item_cd      VARCHAR(10)  PRIMARY KEY,          -- 품목코드
  item_nm      VARCHAR(100) NOT NULL,             -- 품목명
  item_tp_cd   VARCHAR(2)   NOT NULL,             -- 품목유형코드 FG 완제품, RM 원료, PM 포장재
  unit_cd      VARCHAR(5)   NOT NULL,             -- 단위코드 BOX, EA, KG, ROLL
  shelf_life_mm NUMERIC(3),                       -- 유효기간(개월). 완제품만
  use_yn       CHAR(1)      NOT NULL DEFAULT 'Y'
);

CREATE TABLE erp.tb_item_uprc_hist (   -- 품목단가이력 (선분이력, 종료일 포함 규칙: APLY_END_DT 당일까지 유효, 현재 = 9999-12-31)
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  uprc_tp_cd   VARCHAR(2)   NOT NULL,             -- 단가유형코드 01 기준가, 02 보험상한가
  aply_strt_dt DATE         NOT NULL,             -- 적용시작일자
  aply_end_dt  DATE         NOT NULL DEFAULT DATE '9999-12-31',  -- 적용종료일자
  uprc         NUMERIC(15)  NOT NULL,             -- 단가(원)
  PRIMARY KEY (item_cd, uprc_tp_cd, aply_strt_dt)
);

CREATE TABLE erp.tb_cust_emp_hist (    -- 거래처담당이력 (선분이력, 규칙 동일)
  cust_no      VARCHAR(10)  NOT NULL REFERENCES erp.tb_cust(cust_no),
  aply_strt_dt DATE         NOT NULL,
  aply_end_dt  DATE         NOT NULL DEFAULT DATE '9999-12-31',
  emp_no       VARCHAR(10)  NOT NULL REFERENCES erp.tb_emp(emp_no),
  PRIMARY KEY (cust_no, aply_strt_dt)
);

-- ---------------------------------------------------------------------
-- 2. 영업 (한빛제약): 주문 → 출고 → 매출
-- ---------------------------------------------------------------------
CREATE TABLE erp.tb_ord (              -- 주문(헤더)
  ord_no       VARCHAR(14)  PRIMARY KEY,          -- 주문번호 SO+YYYYMM+4자리
  ord_dt       DATE         NOT NULL,             -- 주문일자
  cust_no      VARCHAR(10)  NOT NULL REFERENCES erp.tb_cust(cust_no),
  emp_no       VARCHAR(10)  NOT NULL REFERENCES erp.tb_emp(emp_no),   -- 주문 시점 담당 영업사원
  ord_stat_cd  VARCHAR(2)   NOT NULL,             -- 10 접수, 20 확정, 30 출고완료, 90 취소
  reg_dtm      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
  upd_dtm      TIMESTAMP
);

CREATE TABLE erp.tb_ord_dtl (          -- 주문상세
  ord_no       VARCHAR(14)  NOT NULL REFERENCES erp.tb_ord(ord_no),
  ord_seq      NUMERIC(4)   NOT NULL,             -- 주문순번
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  ord_qty      NUMERIC(10)  NOT NULL,             -- 주문수량
  uprc         NUMERIC(15)  NOT NULL,             -- 주문 시점 단가
  ord_amt      NUMERIC(15)  NOT NULL,             -- 주문금액 = 수량 × 단가
  PRIMARY KEY (ord_no, ord_seq)
);

-- ---------------------------------------------------------------------
-- 3. 물류 (한빛로지스): 입고·출고·재고, 로트·유효기한
-- ---------------------------------------------------------------------
CREATE TABLE erp.tb_wh (               -- 창고
  wh_cd        VARCHAR(5)   PRIMARY KEY,
  wh_nm        VARCHAR(50)  NOT NULL,
  co_cd        VARCHAR(4)   NOT NULL REFERENCES erp.tb_co(co_cd)
);

CREATE TABLE erp.tb_lot (              -- 로트 (제조번호·유효기한)
  lot_no       VARCHAR(20)  PRIMARY KEY,          -- 로트번호
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  mfg_dt       DATE         NOT NULL,             -- 제조일자
  exp_dt       DATE         NOT NULL              -- 유효기한일자
);

CREATE TABLE erp.tb_vndr (             -- 구매처
  vndr_no      VARCHAR(10)  PRIMARY KEY,
  vndr_nm      VARCHAR(100) NOT NULL,
  use_yn       CHAR(1)      NOT NULL DEFAULT 'Y'
);

CREATE TABLE erp.tb_rcv (              -- 입고(헤더)
  rcv_no       VARCHAR(14)  PRIMARY KEY,
  rcv_dt       DATE         NOT NULL,
  wh_cd        VARCHAR(5)   NOT NULL REFERENCES erp.tb_wh(wh_cd),
  vndr_no      VARCHAR(10)  REFERENCES erp.tb_vndr(vndr_no),          -- 구매 입고일 때만
  rcv_tp_cd    VARCHAR(2)   NOT NULL              -- 01 구매입고, 02 생산입고
);

CREATE TABLE erp.tb_rcv_dtl (          -- 입고상세
  rcv_no       VARCHAR(14)  NOT NULL REFERENCES erp.tb_rcv(rcv_no),
  rcv_seq      NUMERIC(4)   NOT NULL,
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  lot_no       VARCHAR(20)  NOT NULL REFERENCES erp.tb_lot(lot_no),
  rcv_qty      NUMERIC(10)  NOT NULL,
  PRIMARY KEY (rcv_no, rcv_seq)
);

CREATE TABLE erp.tb_ship (             -- 출고(헤더)
  ship_no      VARCHAR(14)  PRIMARY KEY,
  ship_dt      DATE         NOT NULL,
  wh_cd        VARCHAR(5)   NOT NULL REFERENCES erp.tb_wh(wh_cd),
  ord_no       VARCHAR(14)  NOT NULL REFERENCES erp.tb_ord(ord_no)
);

CREATE TABLE erp.tb_ship_dtl (         -- 출고상세 (한 주문상세가 여러 로트로 나뉘어 출고될 수 있음)
  ship_no      VARCHAR(14)  NOT NULL REFERENCES erp.tb_ship(ship_no),
  ship_seq     NUMERIC(4)   NOT NULL,
  ord_no       VARCHAR(14)  NOT NULL,
  ord_seq      NUMERIC(4)   NOT NULL,
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  lot_no       VARCHAR(20)  NOT NULL REFERENCES erp.tb_lot(lot_no),
  ship_qty     NUMERIC(10)  NOT NULL,
  PRIMARY KEY (ship_no, ship_seq),
  FOREIGN KEY (ord_no, ord_seq) REFERENCES erp.tb_ord_dtl(ord_no, ord_seq)
);

CREATE TABLE erp.tb_inv_daily (        -- 일별재고 (일자 마감 시점 수량 = 스냅샷)
  inv_dt       DATE         NOT NULL,
  wh_cd        VARCHAR(5)   NOT NULL REFERENCES erp.tb_wh(wh_cd),
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  lot_no       VARCHAR(20)  NOT NULL REFERENCES erp.tb_lot(lot_no),
  inv_qty      NUMERIC(12)  NOT NULL,
  PRIMARY KEY (inv_dt, wh_cd, item_cd, lot_no)
);

-- ---------------------------------------------------------------------
-- 4. 구매
-- ---------------------------------------------------------------------
CREATE TABLE erp.tb_po (               -- 발주(헤더)
  po_no        VARCHAR(14)  PRIMARY KEY,
  po_dt        DATE         NOT NULL,
  vndr_no      VARCHAR(10)  NOT NULL REFERENCES erp.tb_vndr(vndr_no),
  co_cd        VARCHAR(4)   NOT NULL REFERENCES erp.tb_co(co_cd)
);

CREATE TABLE erp.tb_po_dtl (           -- 발주상세
  po_no        VARCHAR(14)  NOT NULL REFERENCES erp.tb_po(po_no),
  po_seq       NUMERIC(4)   NOT NULL,
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  po_qty       NUMERIC(10)  NOT NULL,
  uprc         NUMERIC(15)  NOT NULL,
  PRIMARY KEY (po_no, po_seq)
);

-- ---------------------------------------------------------------------
-- 5. 생산 (한빛케미칼): BOM, 작업지시, 생산실적
-- ---------------------------------------------------------------------
CREATE TABLE erp.tb_bom (              -- BOM (자기참조: 상위품목 ← 하위품목)
  prnt_item_cd VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  chld_item_cd VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  bom_qty      NUMERIC(12,4) NOT NULL,            -- 상위 1단위당 소요량
  aply_strt_dt DATE         NOT NULL,
  aply_end_dt  DATE         NOT NULL DEFAULT DATE '9999-12-31',
  PRIMARY KEY (prnt_item_cd, chld_item_cd, aply_strt_dt)
);

CREATE TABLE erp.tb_wo (               -- 작업지시
  wo_no        VARCHAR(14)  PRIMARY KEY,
  wo_dt        DATE         NOT NULL,
  item_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_item(item_cd),
  wo_qty       NUMERIC(10)  NOT NULL
);

CREATE TABLE erp.tb_prod_rslt (        -- 생산실적
  wo_no        VARCHAR(14)  NOT NULL REFERENCES erp.tb_wo(wo_no),
  prod_dt      DATE         NOT NULL,
  lot_no       VARCHAR(20)  NOT NULL REFERENCES erp.tb_lot(lot_no),
  good_qty     NUMERIC(10)  NOT NULL,             -- 양품수량
  defect_qty   NUMERIC(10)  NOT NULL DEFAULT 0,   -- 불량수량
  PRIMARY KEY (wo_no, lot_no)
);

-- ---------------------------------------------------------------------
-- 6. 회계
-- ---------------------------------------------------------------------
CREATE TABLE erp.tb_acct (             -- 계정과목
  acct_cd      VARCHAR(10)  PRIMARY KEY,
  acct_nm      VARCHAR(50)  NOT NULL
);

CREATE TABLE erp.tb_slip (             -- 전표(헤더)
  slip_no      VARCHAR(14)  PRIMARY KEY,
  slip_dt      DATE         NOT NULL,
  co_cd        VARCHAR(4)   NOT NULL REFERENCES erp.tb_co(co_cd),
  src_doc_no   VARCHAR(14)                        -- 원천 문서번호 (주문·입고 등)
);

CREATE TABLE erp.tb_slip_dtl (         -- 전표상세 (차변 합계 = 대변 합계)
  slip_no      VARCHAR(14)  NOT NULL REFERENCES erp.tb_slip(slip_no),
  slip_seq     NUMERIC(4)   NOT NULL,
  acct_cd      VARCHAR(10)  NOT NULL REFERENCES erp.tb_acct(acct_cd),
  dr_amt       NUMERIC(15)  NOT NULL DEFAULT 0,
  cr_amt       NUMERIC(15)  NOT NULL DEFAULT 0,
  PRIMARY KEY (slip_no, slip_seq)
);

-- =====================================================================
-- 샘플 데이터
-- =====================================================================
INSERT INTO erp.tb_co VALUES
 ('1000','한빛제약','의약품 제조·영업'), ('2000','한빛로지스','물류'), ('3000','한빛푸드','식음료'),
 ('4000','한빛케미칼','원료의약품·화학 제조'), ('5000','한빛건설','건설'), ('9000','한빛정보기술','그룹 IT 서비스');

INSERT INTO erp.tb_dept VALUES
 ('D100','영업본부',NULL,'1000'), ('D110','서울1팀','D100','1000'), ('D120','경기팀','D100','1000'),
 ('D130','부산팀','D100','1000'), ('D900','영업기획팀',NULL,'1000');

INSERT INTO erp.tb_emp (emp_no, emp_nm, dept_cd) VALUES
 ('E1001','김도윤','D110'), ('E1002','이서연','D110'), ('E1003','박지훈','D120'), ('E1004','최하은','D130');

INSERT INTO erp.tb_cust (cust_no, cust_nm, cust_tp_cd, biz_reg_no, rgn_cd) VALUES
 ('C000101','청솔내과의원','01','101-11-00001','SEL'),
 ('C000102','미래종합병원','01','124-81-00002','GGD'),
 ('C000201','햇살약국','02','201-12-00003','SEL'),
 ('C000202','늘봄약국','02','602-13-00004','BSN'),
 ('C000301','바른팜유통','03','135-86-00005','GGD');

INSERT INTO erp.tb_item (item_cd, item_nm, item_tp_cd, unit_cd, shelf_life_mm) VALUES
 ('P10001','한빛펜정 500mg 30T','FG','BOX',36),
 ('P10002','한빛록스정 60mg 100T','FG','BOX',36),
 ('P10003','한빛시럽 100mL','FG','EA',24),
 ('R20001','원료A(주성분)','RM','KG',NULL),
 ('M30001','PTP 알루미늄 호일','PM','ROLL',NULL);

INSERT INTO erp.tb_item_uprc_hist VALUES
 ('P10001','01',DATE '2025-01-01',DATE '2026-03-31', 3200),
 ('P10001','01',DATE '2026-04-01',DATE '9999-12-31', 3000),
 ('P10002','01',DATE '2025-01-01',DATE '9999-12-31',12000),
 ('P10003','01',DATE '2025-07-01',DATE '9999-12-31', 2500),
 ('P10001','02',DATE '2025-01-01',DATE '9999-12-31', 3500);

INSERT INTO erp.tb_cust_emp_hist VALUES
 ('C000101',DATE '2025-01-01',DATE '2026-03-15','E1001'),
 ('C000101',DATE '2026-03-16',DATE '9999-12-31','E1002'),   -- 3/16 담당 변경
 ('C000102',DATE '2025-01-01',DATE '9999-12-31','E1003'),
 ('C000201',DATE '2025-01-01',DATE '9999-12-31','E1002'),
 ('C000202',DATE '2025-01-01',DATE '9999-12-31','E1004'),
 ('C000301',DATE '2025-01-01',DATE '9999-12-31','E1003');

INSERT INTO erp.tb_ord (ord_no, ord_dt, cust_no, emp_no, ord_stat_cd) VALUES
 ('SO2026030001',DATE '2026-03-02','C000201','E1002','30'),
 ('SO2026030002',DATE '2026-03-02','C000101','E1001','30'),
 ('SO2026030003',DATE '2026-03-10','C000301','E1003','30'),
 ('SO2026030004',DATE '2026-03-20','C000101','E1002','20'),
 ('SO2026040001',DATE '2026-04-03','C000202','E1004','10'),
 ('SO2026040002',DATE '2026-04-03','C000201','E1002','90');

INSERT INTO erp.tb_ord_dtl VALUES
 ('SO2026030001',1,'P10001', 10, 3200,  32000),
 ('SO2026030001',2,'P10003', 20, 2500,  50000),
 ('SO2026030002',1,'P10002',  5,12000,  60000),
 ('SO2026030003',1,'P10001',300, 3200, 960000),
 ('SO2026030003',2,'P10002',100,12000,1200000),
 ('SO2026030004',1,'P10001', 20, 3200,  64000),
 ('SO2026040001',1,'P10001', 15, 3000,  45000),
 ('SO2026040002',1,'P10003', 10, 2500,  25000);

INSERT INTO erp.tb_wh VALUES ('W01','이천물류센터','2000'), ('W02','양산물류센터','2000');

INSERT INTO erp.tb_lot VALUES
 ('L250901','P10001',DATE '2025-09-01',DATE '2028-08-31'),
 ('L260105','P10001',DATE '2026-01-05',DATE '2029-01-04'),
 ('L251110','P10002',DATE '2025-11-10',DATE '2028-11-09'),
 ('L250620','P10003',DATE '2025-06-20',DATE '2027-06-19'),
 ('R260201','R20001',DATE '2026-02-01',DATE '2028-01-31');

INSERT INTO erp.tb_vndr (vndr_no, vndr_nm) VALUES ('V0001','대양케미컬(가상)'), ('V0002','한결포장(가상)');

INSERT INTO erp.tb_rcv VALUES
 ('RC2026020001',DATE '2026-02-03','W01','V0001','01'),
 ('RC2026010001',DATE '2026-01-08','W01',NULL,'02');
INSERT INTO erp.tb_rcv_dtl VALUES
 ('RC2026020001',1,'R20001','R260201',500),
 ('RC2026010001',1,'P10001','L260105',2000);

INSERT INTO erp.tb_ship VALUES
 ('SH2026030001',DATE '2026-03-03','W01','SO2026030001'),
 ('SH2026030002',DATE '2026-03-03','W01','SO2026030002'),
 ('SH2026030003',DATE '2026-03-11','W01','SO2026030003');
INSERT INTO erp.tb_ship_dtl VALUES
 ('SH2026030001',1,'SO2026030001',1,'P10001','L250901', 10),
 ('SH2026030001',2,'SO2026030001',2,'P10003','L250620', 20),
 ('SH2026030002',1,'SO2026030002',1,'P10002','L251110',  5),
 ('SH2026030003',1,'SO2026030003',1,'P10001','L250901',200),   -- 오래된 로트 먼저(FEFO)
 ('SH2026030003',2,'SO2026030003',1,'P10001','L260105',100),   -- 같은 주문상세가 두 로트로
 ('SH2026030003',3,'SO2026030003',2,'P10002','L251110',100);

INSERT INTO erp.tb_inv_daily VALUES
 (DATE '2026-03-31','W01','P10001','L250901',   0),
 (DATE '2026-03-31','W01','P10001','L260105',1900),
 (DATE '2026-03-31','W01','P10002','L251110', 395),
 (DATE '2026-03-31','W01','P10003','L250620', 480),
 (DATE '2026-03-31','W01','R20001','R260201', 500);

INSERT INTO erp.tb_po VALUES ('PO2026010001',DATE '2026-01-20','V0001','4000');
INSERT INTO erp.tb_po_dtl VALUES ('PO2026010001',1,'R20001',500,85000);

INSERT INTO erp.tb_bom VALUES
 ('P10001','R20001',0.0150,DATE '2025-01-01',DATE '9999-12-31'),
 ('P10001','M30001',0.0020,DATE '2025-01-01',DATE '9999-12-31');

INSERT INTO erp.tb_wo VALUES ('WO2026010001',DATE '2026-01-04','P10001',2000);
INSERT INTO erp.tb_prod_rslt VALUES ('WO2026010001',DATE '2026-01-05','L260105',2000,12);

INSERT INTO erp.tb_acct VALUES ('11300','외상매출금'), ('41100','제품매출'), ('25500','부가세예수금');
INSERT INTO erp.tb_slip VALUES ('SL2026030001',DATE '2026-03-03','1000','SO2026030001');
INSERT INTO erp.tb_slip_dtl VALUES
 ('SL2026030001',1,'11300',90200,0),
 ('SL2026030001',2,'41100',0,82000),
 ('SL2026030001',3,'25500',0, 8200);
