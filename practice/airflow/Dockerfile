# 6일차: Airflow 공식 이미지 + dbt-duckdb (별도 가상환경)
FROM apache/airflow:3.3.2

# dbt 는 Airflow 와 쓰는 라이브러리(jinja2, protobuf 등) 버전이 겹쳐서 같은 파이썬에 넣으면 충돌하기 쉽다.
# → /opt/dbt_venv 라는 "dbt 전용 방"을 따로 만들어 설치한다.
# 버전은 내 PC 와 맞춘다 (pip show dbt-core dbt-duckdb duckdb 로 확인). DuckDB 는 버전이 다르면 파일을 못 읽을 수 있다.
USER root
RUN python -m venv /opt/dbt_venv \
 && /opt/dbt_venv/bin/pip install --no-cache-dir \
      "dbt-core==1.12.6" "dbt-duckdb==1.11.1" "duckdb==2.0.0" \
 && /opt/dbt_venv/bin/dbt --version
USER airflow
