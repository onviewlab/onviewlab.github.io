"""네이버 블로그(twmsgyu) 새 글 가져오기.

  python naver_sync.py            새 글이 있는지 보고 원문을 내려받는다
  python naver_sync.py --list     이미 옮긴 글 목록만 보여 준다

하는 일
  1) 네이버 블로그 RSS 를 읽어 글 목록을 가져온다.
  2) 이미 옮긴 글(naver_synced.json 에 적힌 logNo)은 건너뛴다.
  3) 새 글은 본문을 내려받아 `새글_원문/<logNo>_<제목>.txt` 로 저장한다.

원문은 참고용이다. 홈페이지 글(posts/*.txt)은 이 원문을 그대로 쓰지 않고
새로 고쳐 쓴다 (2026-09-21 사용자 결정 — 같은 문서가 두 곳에 있으면 둘 다 검색에서 손해).
옮긴 뒤에는 naver_synced.json 에 logNo 와 홈페이지 slug 를 적어 둔다.

이 PC 는 SSL 중간 검사가 걸려 있어 truststore 주입이 없으면 HTTPS 가 전부 실패한다.
"""
import argparse
import html
import json
import re
import ssl
import sys
import urllib.request
from pathlib import Path

try:
    import truststore
    truststore.inject_into_ssl()
except ImportError:                               # 없으면 윈도우 인증서를 못 써서 대부분 실패한다
    print("truststore 가 없습니다. pip install truststore 후 다시 실행하세요.", file=sys.stderr)

ROOT = Path(__file__).resolve().parent
BLOG_ID = "twmsgyu"
RSS = f"https://rss.blog.naver.com/{BLOG_ID}.xml"
VIEW = "https://blog.naver.com/PostView.naver?blogId={bid}&logNo={log}&redirect=Dlog&widgetTypeCall=true&directAccess=false"
STATE = ROOT / "naver_synced.json"
RAW = ROOT / "새글_원문"
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=20, context=ssl.create_default_context()) as r:
        raw = r.read()
    for enc in ("utf-8", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "replace")


def load_state() -> dict:
    if STATE.exists():
        return json.loads(STATE.read_text(encoding="utf-8"))
    return {"done": {}}


def save_state(state: dict) -> None:
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def rss_items() -> list[dict]:
    """RSS 에서 글 목록을 뽑는다. 최신 글이 앞에 온다."""
    xml = fetch(RSS)
    items = []
    for block in re.findall(r"<item>(.*?)</item>", xml, re.S):
        def tag(name: str) -> str:
            m = re.search(rf"<{name}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{name}>", block, re.S)
            return html.unescape(m.group(1).strip()) if m else ""
        link = tag("link")
        log = re.search(r"logNo=(\d+)|/(\d{6,})", link)
        items.append({"logNo": (log.group(1) or log.group(2)) if log else "",
                      "title": tag("title"), "link": link, "date": tag("pubDate")})
    return [i for i in items if i["logNo"]]


def post_text(log_no: str) -> str:
    """글 본문을 글자만 남겨 돌려준다 (사진 · 스티커는 [사진] 으로)."""
    page = fetch(VIEW.format(bid=BLOG_ID, log=log_no))
    start = page.find('class="se-main-container"')
    if start < 0:
        raise RuntimeError(f"{log_no}: 본문(se-main-container)을 찾지 못했습니다.")
    body = page[page.find(">", start) + 1:]
    # 본문 뒤에 붙는 태그 · 공감 · 댓글 영역 앞에서 자른다
    for end_mark in ('wrap_tag', 'class="post-btn', 'class="area_sympathy', 'id="area_sympathy'):
        cut = body.find(end_mark)
        if cut > 0:
            body = body[:cut]
            break
    body = re.sub(r"<script.*?</script>|<style.*?</style>", "", body, flags=re.S)
    body = re.sub(r"<img[^>]*>", "\n[사진]\n", body)
    body = re.sub(r"</p>|<br\s*/?>|</div>", "\n", body, flags=re.I)
    body = re.sub(r"<[^>]*$", "", body)                     # 자르면서 반쯤 남은 태그
    text = html.unescape(re.sub(r"<[^>]+>", "", body))
    text = re.sub(r"[ \t​\xa0]+", " ", text)
    text = "\n".join(ln.strip() for ln in text.splitlines())
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def safe(name: str) -> str:
    return re.sub(r'[\\/:*?"<>|]', "", name).strip()[:60]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="이미 옮긴 글만 보여 준다")
    args = ap.parse_args()
    state = load_state()
    done = state["done"]

    if args.list:
        print(f"이미 옮긴 글 {len(done)}개")
        for log, info in done.items():
            print(f"  {log}  {info.get('title','')}  →  {info.get('slug','(아직 없음)')}")
        return

    items = rss_items()
    new = [i for i in items if i["logNo"] not in done]
    print(f"네이버 글 {len(items)}개 중 새 글 {len(new)}개")
    if not new:
        return
    RAW.mkdir(exist_ok=True)
    for i in new:
        body = post_text(i["logNo"])
        path = RAW / f"{i['logNo']}_{safe(i['title'])}.txt"
        path.write_text(f"제목: {i['title']}\n주소: {i['link']}\n날짜: {i['date']}\n\n{body}\n", encoding="utf-8")
        print(f"  받음: {path.name}  ({len(body)}자)")
    print("\n원문은 참고용입니다. 홈페이지 글은 새로 고쳐 써서 posts/ 에 넣고,")
    print("올린 뒤 naver_synced.json 에 logNo · slug 를 적어 주세요.")


if __name__ == "__main__":
    main()
