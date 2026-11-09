# Airflow 실습 파일 (5·6일차)

| 파일 | 쓰는 날 | 하는 일 |
|---|---|---|
| `docker-compose.yml` | 5일차 | `apache/airflow:3.3.2` 를 `standalone` 으로 띄움. 웹 화면 http://localhost:8083 |
| `docker-compose.dbt.yml` | 6일차 | 위 설정에 dbt 이미지·shop 프로젝트·landing 폴더를 덧씌움 |
| `Dockerfile` | 6일차 | Airflow 이미지 + `/opt/dbt_venv` 에 dbt-duckdb |
| `dbt/profiles.yml` | 6일차 | 컨테이너 안 dbt 접속 정보 (`dev` / `prod` target) |
| `dags/hello_taskflow.py` | 5일차 | 첫 TaskFlow DAG (태스크 3개) |
| `dags/daily_orders_partition.py` | 5일차 | 날짜별 파일을 멱등하게 쓰는 DAG, 백필 연습 |
| `dags/shop_assets.py` | 6일차 | 공용 Asset 정의 |
| `dags/collect_shop_raw.py` | 6일차 | landing → shop/data 로 옮기고 Asset 갱신 |
| `dags/dbt_shop_build.py` | 6일차 | `dbt build` 를 태스크 하나로 |
| `dags/dbt_shop_layers.py` | 6일차 | 계층별 태스크 + Asset 스케줄 + 재시도·알림·풀 |
| `optional/dbt_shop_cosmos.py` | 6일차(선택) | astronomer-cosmos 예시 (기본 이미지에는 cosmos 가 없음) |

## 5일차

```powershell
docker info --format "{{.ServerVersion}}"   # 숫자가 나와야 함. 오류면 Docker Desktop 을 켜고 1분 뒤 다시
mkdir $HOME\airflow-practice; cd $HOME\airflow-practice
mkdir dags, data, output, logs
# 이 폴더의 파일들을 받아 둔 뒤
Copy-Item $HOME\dbt-practice\shop\data\raw_orders.csv .\data\
docker compose up -d
docker compose logs -f airflow     # "Airflow is ready" 가 보이면 Ctrl+C
```

## 6일차

```powershell
"SHOP_DIR=$($HOME -replace '\\','/')/dbt-practice/shop" | Out-File .env -Encoding ascii
docker compose -f docker-compose.yml -f docker-compose.dbt.yml up -d --build
docker compose exec airflow airflow pools set duckdb 1 "DuckDB single writer"
```

끄기: `docker compose stop` (기록 유지) / `docker compose down` (컨테이너 삭제, 실행 기록도 사라짐). 메모리가 빠듯한 PC 이므로 실습이 끝나면 꼭 둘 중 하나를 하고 `docker ps` 로 확인.
