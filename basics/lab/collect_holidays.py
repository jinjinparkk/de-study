# 2026년 공휴일 수집기 - 표준 라이브러리만 사용 (pip 설치 불필요)
import csv, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

BASE = os.environ.get("HOLIDAY_BASE", "http://localhost:8010")      # 진짜: https://apis.data.go.kr
PATH = "/B090041/openapi/service/SpcdeInfoService/getRestDeInfo"
KEY = os.environ["DATA_GO_KR_KEY"]          # Decoding 키를 환경 변수로 (코드 · git 에 키를 쓰지 않음)
YEAR = sys.argv[1] if len(sys.argv) > 1 else "2026"
RAW = Path("raw") / f"holidays_{YEAR}"      # 받은 그대로 저장하는 곳
RAW.mkdir(parents=True, exist_ok=True)


def call(params, tries=4):
    """한 번 호출. 일시 오류(429 · 5xx · 네트워크)는 기다렸다 재시도, 내 잘못(4xx)은 바로 멈춤."""
    url = BASE + PATH + "?" + urllib.parse.urlencode(params)   # 여기서 키가 한 번 인코딩됨
    for i in range(tries):
        try:
            with urllib.request.urlopen(url, timeout=10) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")
            if e.code == 429 or e.code >= 500:
                wait = 2 ** i                       # 1, 2, 4, 8초 (지수 백오프)
                print(f"  {e.code} 일시 오류, {wait}초 뒤 재시도")
                time.sleep(wait)
                continue
            raise SystemExit(f"{e.code} 요청 오류 - 재시도해도 소용없음: {body}")
        except urllib.error.URLError as e:
            print(f"  네트워크 오류 {e.reason}, 재시도")
            time.sleep(2 ** i)
    raise SystemExit("재시도를 다 썼음")


def items_of(data):
    """header 확인 + item 을 항상 목록으로."""
    header = data["response"]["header"]
    if header["resultCode"] != "00":                     # HTTP 200 이어도 실패일 수 있음
        raise SystemExit(f"서비스 오류 {header['resultCode']} {header['resultMsg']}")
    body = data["response"]["body"]
    items = body.get("items") or {}                      # 0건이면 "" 로 옴
    item = items.get("item", [])
    return (item if isinstance(item, list) else [item]), body["totalCount"]


rows = []
fetched_at = datetime.now().isoformat(timespec="seconds")
for m in range(1, 13):
    page = 1
    while True:
        params = {"serviceKey": KEY, "solYear": YEAR, "solMonth": f"{m:02d}",
                  "numOfRows": 2, "pageNo": page, "_type": "json"}   # 일부러 작게 - 페이지 넘김 연습
        data = call(params)
        (RAW / f"{m:02d}_p{page}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
        got, total = items_of(data)
        rows += [{**it, "fetched_at": fetched_at} for it in got]
        print(f"{YEAR}-{m:02d} p{page}: {len(got)}건 (전체 {total})")
        if page * params["numOfRows"] >= total:
            break
        page += 1
        time.sleep(0.2)                                  # 예의상 천천히 (트래픽 한도)

out = Path(f"holidays_{YEAR}.csv")                       # 같은 해를 다시 돌리면 덮어씀 = 중복 없음
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=["locdate", "dateName", "isHoliday", "dateKind", "seq", "fetched_at"])
    w.writeheader()
    w.writerows(rows)
print(f"완료: {out} {len(rows)}행")
