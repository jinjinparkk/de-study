# 공공데이터포털 '특일 정보' 흉내 서버 (연습용) - python mock_datagokr.py 로 실행, http://localhost:8010
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qs

KEY = "my+test/key=="          # 연습용 '진짜 키' (Decoding 모양)
# 연습용 목록 (실제 공휴일과 다를 수 있음 - 진짜는 4단계에서 포털로)
HOLIDAYS = [("20260101", "1월1일"), ("20260216", "설날"), ("20260217", "설날"), ("20260218", "설날"),
            ("20260301", "삼일절"), ("20260302", "대체공휴일"), ("20260505", "어린이날"),
            ("20260524", "부처님오신날"), ("20260525", "대체공휴일"), ("20260603", "전국동시지방선거"),
            ("20260606", "현충일"), ("20260815", "광복절"), ("20260817", "대체공휴일"),
            ("20260924", "추석"), ("20260925", "추석"), ("20260926", "추석"), ("20261003", "개천절"),
            ("20261005", "대체공휴일"), ("20261009", "한글날"), ("20261225", "기독탄신일")]
calls = {"n": 0}

class H(BaseHTTPRequestHandler):
    def send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json;charset=UTF-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(u.query).items()}   # parse_qs 가 %2B -> + 로 한 번 풀어 줌
        if u.path != "/B090041/openapi/service/SpcdeInfoService/getRestDeInfo":
            return self.send(404, {"error": "no such path"})
        # 1층: 게이트웨이 - 키 검사 (실제 포털과 같은 모양)
        key = q.get("serviceKey") or q.get("ServiceKey")
        if not key:
            return self.send(401, {"OpenAPI_ServiceResponse": {"cmmMsgHeader": {
                "errMsg": "SERVICE_KEY_IS_NULL", "returnAuthMsg": "서비스 접근거부", "returnReasonCode": "20"}}})
        if key != KEY:
            return self.send(403, {"OpenAPI_ServiceResponse": {"cmmMsgHeader": {
                "errMsg": "SERVICE_KEY_IS_NOT_REGISTERED_ERROR", "returnAuthMsg": "등록되지 않은 서비스키", "returnReasonCode": "30"}}})
        # 가끔 일부러 실패 (재시도 연습)
        calls["n"] += 1
        if calls["n"] % 4 == 0:
            return self.send(503, {"error": "잠시 후 다시 시도"})
        # 2층: 서비스 - 요청 변수 검사
        year, month = q.get("solYear"), q.get("solMonth")
        if not year or not month or len(month) != 2:
            return self.send(200, {"response": {"header": {"resultCode": "10", "resultMsg": "INVALID_REQUEST_PARAMETER_ERROR"}}})
        rows = [{"dateKind": "01", "dateName": n, "isHoliday": "Y", "locdate": int(d), "seq": 1}
                for d, n in HOLIDAYS if d[:4] == year and d[4:6] == month]
        size, page = int(q.get("numOfRows", 10)), int(q.get("pageNo", 1))
        part = rows[(page - 1) * size: page * size]
        # XML 을 JSON 으로 바꾼 API 의 버릇: 0건이면 items 가 빈 문자열, 1건이면 item 이 목록이 아니라 객체
        items = "" if not part else {"item": part[0] if len(part) == 1 else part}
        self.send(200, {"response": {"header": {"resultCode": "00", "resultMsg": "NORMAL SERVICE."},
                                     "body": {"items": items, "numOfRows": size, "pageNo": page, "totalCount": len(rows)}}})

    def log_message(self, fmt, *args):
        print(self.command, self.path[:110], "->", args[1] if len(args) > 1 else "")

if __name__ == "__main__":
    print("모의 공공데이터포털: http://localhost:8010  (Ctrl+C 로 종료)")
    HTTPServer(("127.0.0.1", 8010), H).serve_forever()
