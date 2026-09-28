"""빙·네이버(IndexNow)에 새 글 주소를 자동으로 알려주는 스크립트.

- 기본: 이번 실행에서 sitemap.xml 에 새로 생긴 주소만 제출
- INDEXNOW_ALL=1 이면 sitemap.xml 의 모든 주소를 제출
"""
import json
import os
import re
import subprocess
import urllib.request

HOST = "obl-marketing.kr"
KEY = "74c4bb86f20943d980b63498203ecd07"
KEY_LOCATION = f"https://{HOST}/{KEY}.txt"
ENDPOINTS = [
    ("빙", "https://api.indexnow.org/indexnow"),
    ("네이버", "https://searchadvisor.naver.com/indexnow"),
]


def locs(text):
    return re.findall(r"<loc>\s*([^<\s]+)\s*</loc>", text or "")


def previous_sitemap():
    try:
        return subprocess.run(
            ["git", "show", "HEAD:sitemap.xml"],
            capture_output=True, text=True, check=True,
        ).stdout
    except subprocess.CalledProcessError:
        return ""


def main():
    with open("sitemap.xml", encoding="utf-8") as f:
        current = locs(f.read())

    if os.environ.get("INDEXNOW_ALL") == "1":
        urls = current
    else:
        before = set(locs(previous_sitemap()))
        urls = [u for u in current if u not in before]

    if not urls:
        print("IndexNow: 제출할 새 주소 없음")
        return

    body = json.dumps({
        "host": HOST,
        "key": KEY,
        "keyLocation": KEY_LOCATION,
        "urlList": urls,
    }).encode("utf-8")
    for name, endpoint in ENDPOINTS:
        req = urllib.request.Request(
            endpoint, data=body, method="POST",
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as res:
                print(f"IndexNow {name}: {len(urls)}개 제출, 응답 {res.status}")
        except urllib.error.HTTPError as e:
            print(f"IndexNow {name}: 제출 실패 {e.code} {e.read()[:200]!r}")
        except OSError as e:
            print(f"IndexNow {name}: 연결 실패 {e}")
    for u in urls:
        print("  ", u)


if __name__ == "__main__":
    main()
