# Meta(페이스북) 광고 '비동기 인사이트' 흉내 서버 (연습용) - python mock_meta.py, http://localhost:8011
# 실제 Graph API 의 모양만 따라 함: 주문(POST) -> report_run_id -> 상태 묻기(GET) -> 결과 페이지(cursor)
import base64, json, time
from datetime import date, timedelta
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

TOKEN = "practice-token"
VER = "v21.0"                                   # 실제로는 그때의 최신 버전 번호
ADSETS = [("23850001", "MW_릴스_봄"), ("23850002", "MW_피드_리타겟"), ("23850003", "NK_스토리_신규")]
JOBS = {}                                       # report_run_id -> {start, rows, last_poll}
JOB_SECONDS = 6                                 # 작업이 끝나는 데 걸리는 시간


def make_rows(since, until):
    rows, d = [], date.fromisoformat(since)
    while d <= date.fromisoformat(until):
        for i, (aid, name) in enumerate(ADSETS):
            n = d.toordinal() * 7 + i * 13          # 늘 같은 값이 나오게 (난수 대신)
            clicks, buys = 300 + n % 500, 3 + n % 11
            rows.append({"adset_id": aid, "adset_name": name, "date_start": d.isoformat(), "date_stop": d.isoformat(),
                         "spend": f"{(clicks * 412.5):.2f}", "impressions": str(clicks * 37), "clicks": str(clicks),
                         "actions": [{"action_type": "link_click", "value": str(clicks)},
                                     {"action_type": "purchase", "value": str(buys)}]})
        d += timedelta(days=1)
    return rows


def err(message, code, etype="OAuthException", status=400):
    return status, {"error": {"message": message, "type": etype, "code": code, "fbtrace_id": "AbCdEf123"}}


class H(BaseHTTPRequestHandler):
    def reply(self, status, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def params(self):
        q = {k: v[0] for k, v in parse_qs(urlparse(self.path).query).items()}
        n = int(self.headers.get("Content-Length") or 0)
        if n:
            q.update({k: v[0] for k, v in parse_qs(self.rfile.read(n).decode("utf-8")).items()})
        return q

    def token_ok(self, q):
        auth = self.headers.get("Authorization", "")
        return q.get("access_token") == TOKEN or auth == f"Bearer {TOKEN}"

    def route(self, method):
        q = self.params()
        parts = urlparse(self.path).path.strip("/").split("/")
        if not self.token_ok(q):
            return err("Invalid OAuth access token - Cannot parse access token", 190)
        if not parts or parts[0] != VER:
            return err(f"Unsupported version. Use {VER}", 2635, "GraphMethodException")
        # 1) 주문: POST /v21.0/act_<id>/insights
        if method == "POST" and len(parts) == 3 and parts[1].startswith("act_") and parts[2] == "insights":
            tr = json.loads(q.get("time_range", "{}"))
            if "since" not in tr or "until" not in tr:
                return err("(#100) time_range must have since and until", 100, "OAuthException")
            rid = str(1200000 + len(JOBS) + 1)
            JOBS[rid] = {"start": time.time(), "rows": make_rows(tr["since"], tr["until"]), "last_poll": 0}
            return 200, {"report_run_id": rid}
        if len(parts) >= 2 and parts[1] in JOBS:
            job = JOBS[parts[1]]
            # 2) 상태: GET /v21.0/<report_run_id>
            if method == "GET" and len(parts) == 2:
                now = time.time()
                if now - job["last_poll"] < 1.0:          # 너무 자주 물으면 한도 초과
                    return err("(#17) User request limit reached", 17)
                job["last_poll"] = now
                pct = min(100, int((now - job["start"]) / JOB_SECONDS * 100))
                status = "Job Completed" if pct >= 100 else ("Job Running" if pct > 0 else "Job Not Started")
                return 200, {"id": parts[1], "async_status": status, "async_percent_completion": pct}
            # 3) 결과: GET /v21.0/<report_run_id>/insights?limit=&after=
            if method == "GET" and len(parts) == 3 and parts[2] == "insights":
                if time.time() - job["start"] < JOB_SECONDS:
                    return err("(#100) Report is not ready yet", 100)
                limit = int(q.get("limit", 25))
                start = int(base64.b64decode(q["after"]).decode()) if "after" in q else 0
                page = job["rows"][start:start + limit]
                out = {"data": page, "paging": {"cursors": {
                    "before": base64.b64encode(str(start).encode()).decode(),
                    "after": base64.b64encode(str(start + len(page)).encode()).decode()}}}
                if start + limit < len(job["rows"]):    # 다음 페이지가 있을 때만 next
                    after = out["paging"]["cursors"]["after"]
                    out["paging"]["next"] = f"http://localhost:8011/{VER}/{parts[1]}/insights?limit={limit}&after={after}"
                return 200, out
        return err("Unknown path components", 2500, "OAuthException")

    def do_GET(self):
        self.reply(*self.route("GET"))

    def do_POST(self):
        self.reply(*self.route("POST"))

    def log_message(self, fmt, *args):
        print(self.command, self.path.split("?")[0], "->", args[1] if len(args) > 1 else "")


if __name__ == "__main__":
    print("모의 Meta Graph API: http://localhost:8011  (Ctrl+C 로 종료)")
    HTTPServer(("127.0.0.1", 8011), H).serve_forever()
