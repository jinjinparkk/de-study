# 기상청 단기예보 API 연습 도구 - 표준 라이브러리만
#   python weather_tools.py            -> 키 없이: 격자 변환 · 발표 시각 계산 · 긴 표를 넓은 표로
#   python weather_tools.py live       -> 내 키로 진짜 호출 (환경 변수 DATA_GO_KR_KEY = Decoding 키)
import json, math, os, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta


def latlon_to_grid(lat, lon):
    """위도 · 경도 -> 기상청 격자 (nx, ny). 기상청 활용 가이드의 람베르트 정각원추도법 공식."""
    RE, GRID = 6371.00877, 5.0                  # 지구 반지름(km), 격자 간격(km)
    SLAT1, SLAT2, OLON, OLAT = 30.0, 60.0, 126.0, 38.0
    XO, YO = 43, 136                            # 기준점의 격자 좌표
    D = math.pi / 180.0
    re = RE / GRID
    slat1, slat2, olon, olat = SLAT1 * D, SLAT2 * D, OLON * D, OLAT * D
    sn = math.log(math.cos(slat1) / math.cos(slat2)) / math.log(
        math.tan(math.pi * 0.25 + slat2 * 0.5) / math.tan(math.pi * 0.25 + slat1 * 0.5))
    sf = math.tan(math.pi * 0.25 + slat1 * 0.5) ** sn * math.cos(slat1) / sn
    ro = re * sf / math.tan(math.pi * 0.25 + olat * 0.5) ** sn
    ra = re * sf / math.tan(math.pi * 0.25 + lat * D * 0.5) ** sn
    theta = lon * D - olon
    if theta > math.pi:
        theta -= 2.0 * math.pi
    if theta < -math.pi:
        theta += 2.0 * math.pi
    theta *= sn
    return int(ra * math.sin(theta) + XO + 0.5), int(ro - ra * math.cos(theta) + YO + 0.5)


def latest_base(now):
    """지금 부를 수 있는 가장 최근 단기예보 발표 (base_date, base_time).
    발표는 02 · 05 · 08 · 11 · 14 · 17 · 20 · 23시, API 에는 발표 후 약 10분 뒤 올라옴."""
    t = now - timedelta(minutes=10)
    hours = [h for h in (2, 5, 8, 11, 14, 17, 20, 23) if h <= t.hour]
    if not hours:                               # 02:10 전이면 전날 23시 발표
        t -= timedelta(days=1)
        return t.strftime("%Y%m%d"), "2300"
    return t.strftime("%Y%m%d"), f"{hours[-1]:02d}00"


def to_wide(items):
    """긴 표(한 행 = 시각 x 항목 하나) -> 넓은 표(한 행 = 시각, 열 = 항목)."""
    wide = {}
    for it in items:
        key = (it["fcstDate"], it["fcstTime"])
        wide.setdefault(key, {"fcstDate": it["fcstDate"], "fcstTime": it["fcstTime"]})[it["category"]] = it["fcstValue"]
    return [wide[k] for k in sorted(wide)]


SAMPLE = [  # 응답 item 모양 그대로 (값은 연습용)
    {"baseDate": "20261119", "baseTime": "0500", "category": "TMP", "fcstDate": "20261119", "fcstTime": "0600", "fcstValue": "3", "nx": 60, "ny": 127},
    {"baseDate": "20261119", "baseTime": "0500", "category": "SKY", "fcstDate": "20261119", "fcstTime": "0600", "fcstValue": "1", "nx": 60, "ny": 127},
    {"baseDate": "20261119", "baseTime": "0500", "category": "PTY", "fcstDate": "20261119", "fcstTime": "0600", "fcstValue": "0", "nx": 60, "ny": 127},
    {"baseDate": "20261119", "baseTime": "0500", "category": "PCP", "fcstDate": "20261119", "fcstTime": "0600", "fcstValue": "강수없음", "nx": 60, "ny": 127},
    {"baseDate": "20261119", "baseTime": "0500", "category": "TMP", "fcstDate": "20261119", "fcstTime": "0700", "fcstValue": "2", "nx": 60, "ny": 127},
    {"baseDate": "20261119", "baseTime": "0500", "category": "SKY", "fcstDate": "20261119", "fcstTime": "0700", "fcstValue": "3", "nx": 60, "ny": 127},
    {"baseDate": "20261119", "baseTime": "0500", "category": "PTY", "fcstDate": "20261119", "fcstTime": "0700", "fcstValue": "1", "nx": 60, "ny": 127},
    {"baseDate": "20261119", "baseTime": "0500", "category": "PCP", "fcstDate": "20261119", "fcstTime": "0700", "fcstValue": "1mm 미만", "nx": 60, "ny": 127},
]


def live(nx, ny):
    base_date, base_time = latest_base(datetime.now())
    params = {"serviceKey": os.environ["DATA_GO_KR_KEY"], "dataType": "JSON", "numOfRows": 1000, "pageNo": 1,
              "base_date": base_date, "base_time": base_time, "nx": nx, "ny": ny}
    url = "https://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getVilageFcst?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=10) as r:
        data = json.loads(r.read().decode("utf-8"))
    header = data["response"]["header"]
    if header["resultCode"] != "00":
        raise SystemExit(f"서비스 오류 {header['resultCode']} {header['resultMsg']}")
    item = data["response"]["body"]["items"]["item"]
    return base_date, base_time, to_wide(item if isinstance(item, list) else [item])


if __name__ == "__main__":
    print("서울시청 (37.5665, 126.9780) ->", latlon_to_grid(37.5665, 126.9780))
    print("부산시청 (35.1796, 129.0756) ->", latlon_to_grid(35.1796, 129.0756))
    for s in ("2026-11-19 01:30", "2026-11-19 05:05", "2026-11-19 05:15", "2026-11-19 13:59"):
        print(s, "->", latest_base(datetime.strptime(s, "%Y-%m-%d %H:%M")))
    print("긴 표", len(SAMPLE), "행 -> 넓은 표:")
    for row in to_wide(SAMPLE):
        print(" ", row)
    if sys.argv[1:] == ["live"]:
        bd, bt, rows = live(*latlon_to_grid(37.5665, 126.9780))
        print(f"\n진짜 예보 (발표 {bd} {bt}) 처음 5시간:")
        for row in rows[:5]:
            print(" ", row)
