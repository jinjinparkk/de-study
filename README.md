# DAS — dbt · Airflow · Spark

프로시저로 마트를 만들어 온 analytics engineer를 위한 7일 학습 사이트입니다.
이론(비유·프로시저 비교·구조도) + 내 PC 실습(dbt-duckdb, Docker로 Airflow·Spark) + 퀴즈.

- 사이트: https://jinjinparkk.github.io/de-study/
- 진도는 브라우저 localStorage 에 저장됩니다.
- 빌드 단계 없는 정적 HTML입니다. 로컬에서 보려면 `python -m http.server 8001` 후 http://localhost:8001

## 구성

| 경로 | 내용 |
|---|---|
| `index.html` | 커리큘럼·진도 |
| `days/day1~7.html` | 일차별 학습 |
| `dbt30/` | dbt 30일 집중 코스(BigQuery). 일정·평가는 `index.html`, 본문은 `dayNN.html`, 일차 목록은 `assets/dbt30-days.js`(`ready: true`인 날만 본문 있음), 모델링 관점은 `modeling.html` |
| `essentials/` | 필수 정리: 데이터 아키텍트·엔지니어 30일(가상 그룹사 한빛제약그룹). 본문은 `essentials/days/dayNN.md`, 목록은 `curriculum.json`, PostgreSQL 공통 스키마는 `essentials/schema/`. 편집 안내는 `essentials/README.md` |
| `dictionary.html` | 프로시저 ↔ dbt 사전 |
| `glossary.html` | 용어집 |
| `cheatsheet.html` | 명령어 모음 |
| `practice/` | 실습 데이터(CSV), Airflow·Spark 설정 |
| `CURRICULUM.md` | 커리큘럼 설계와 페이지 작성 규칙 |
