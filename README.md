# dbt · Airflow · Spark 7일

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
| `dictionary.html` | 프로시저 ↔ dbt 사전 |
| `glossary.html` | 용어집 |
| `cheatsheet.html` | 명령어 모음 |
| `practice/` | 실습 데이터(CSV), Airflow·Spark 설정 |
| `CURRICULUM.md` | 커리큘럼 설계와 페이지 작성 규칙 |
