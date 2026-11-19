# Meta 비동기 인사이트 수집기 (모의 서버용) - 표준 라이브러리만
#   $env:META_TOKEN = 'practice-token'; python collect_meta_async.py 2026-06-01 2026-06-07
import csv, json, os, sys, time, urllib.error, urllib.parse, urllib.request
from datetime import datetime
from pathlib import Path

BASE = os.environ.get("META_BASE", "http://localhost:8011/v21.0")
ACCOUNT = "act_1234567890"
TOKEN = os.environ["META_TOKEN"]
SINCE, UNTIL = sys.argv[1], sys.argv[2]
RAW = Path("raw") / f"meta_{SINCE}_{UNTIL}"
RAW.mkdir(parents=True, exist_ok=True)


def call(url, data=None):
    """토큰은 주소가 아니라 헤더에. Meta 에러는 본문의 error.code 로 판단."""
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {TOKEN}"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = json.loads(e.read().decode("utf-8"))
        error = body.get("error", {})
        if error.get("code") in (4, 17, 80004):             # 호출 한도 -> 기다리라는 뜻
            return {"_rate_limited": True}
        raise SystemExit(f"Meta 오류 code={error.get('code')} {error.get('message')}")


# 1) 주문 넣기
order = urllib.parse.urlencode({
    "level": "adset", "time_increment": 1,
    "time_range": json.dumps({"since": SINCE, "until": UNTIL}),
    "fields": "adset_id,adset_name,spend,impressions,clicks,actions",
}).encode()
rid = call(f"{BASE}/{ACCOUNT}/insights", data=order)["report_run_id"]
print("주문 번호:", rid)

# 2) 다 됐는지 묻기 (폴링) - 간격을 점점 늘리고, 최대 대기 시간을 둠
wait, deadline = 1.5, time.time() + 120
while True:
    time.sleep(wait)
    st = call(f"{BASE}/{rid}")
    if st.get("_rate_limited"):
        wait = min(wait * 2, 30)
        print(f"  너무 자주 물었음 -> {wait}초 간격으로")
        continue
    print(f"  {st['async_status']} {st['async_percent_completion']}%")
    if st["async_status"] == "Job Completed":
        break
    if st["async_status"] in ("Job Failed", "Job Skipped"):
        raise SystemExit("작업 실패 - 기간을 줄여 다시 주문")
    if time.time() > deadline:
        raise SystemExit("너무 오래 걸림 - 나중에 같은 번호로 다시 확인")
    wait = min(wait * 1.5, 30)

# 3) 결과 받기 - next 주소가 없을 때까지 (커서 방식: 직접 계산하지 않음)
url, page, rows = f"{BASE}/{rid}/insights?limit=5", 1, []
fetched_at = datetime.now().isoformat(timespec="seconds")
while url:
    data = call(url)
    (RAW / f"p{page}.json").write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    for r in data["data"]:
        acts = {a["action_type"]: a["value"] for a in r.get("actions", [])}   # 목록 안의 목록 -> 펼치기
        rows.append({"date": r["date_start"], "adset_id": r["adset_id"], "adset_name": r["adset_name"],
                     "spend": r["spend"], "impressions": r["impressions"], "clicks": r["clicks"],
                     "purchases": acts.get("purchase", "0"), "fetched_at": fetched_at})
    print(f"  p{page}: {len(data['data'])}행")
    url, page = data["paging"].get("next"), page + 1

out = Path(f"meta_{SINCE}_{UNTIL}.csv")
with out.open("w", newline="", encoding="utf-8-sig") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"완료: {out} {len(rows)}행")
