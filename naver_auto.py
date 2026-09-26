"""네이버 블로그(twmsgyu) 새 글을 홈페이지 글로 자동으로 옮긴다.

GitHub Actions(.github/workflows/naver-sync.yml)가 주기적으로 실행한다.
  python naver_auto.py

하는 일
  1) 네이버 RSS 에서 글 목록을 읽는다 (naver_sync.py 의 함수를 그대로 쓴다).
  2) naver_synced.json 에 없는 새 글만 원문 그대로 posts/<날짜>_naver-<logNo>.txt 로 만든다.
     (2026-09-26 사용자 결정: 고쳐 쓰지 않고 원문 그대로 자동 복사)
  3) 금지어(build.py BANNED)는 무난한 말로 바꿔서 넣는다 — 금지어가 있으면 build.py 가 전체를 멈추기 때문.
  4) naver_synced.json 이 비어 있으면 지금 RSS 에 있는 글을 전부 '이미 옮김'으로만 적고 끝낸다.
     (그전 글들은 이미 손으로 고쳐 써서 올렸으므로 중복을 막는다.)

새 글을 만들었으면 종료 코드 0 과 함께 'NEW=개수' 를 출력한다. 이후 build.py 는 워크플로가 실행한다.
"""
import datetime
import email.utils
import html
import re

import naver_sync as ns

KST = datetime.timezone(datetime.timedelta(hours=9))
REPLACE = [("상위 노출", "상단 노출"), ("상위노출", "상단 노출"), ("지식iN", "지식 검색"), ("지식인", "지식 검색"),
           ("보장", "약속"), ("1위", "상위권"), ("100 %", "전부"), ("100%", "전부")]


def clean(s: str) -> str:
    for a, b in REPLACE:
        s = s.replace(a, b)
    return s


def post_date(pub: str) -> str:
    try:
        return email.utils.parsedate_to_datetime(pub).astimezone(KST).date().isoformat()
    except Exception:
        return datetime.datetime.now(KST).date().isoformat()


def to_body(text: str) -> str:
    lines = [ln for ln in text.splitlines() if ln.strip() not in ("[사진]", "출처 입력", "﻿")]
    body = "\n".join(ln.replace("﻿", "") for ln in lines)
    body = re.sub(r"\n{3,}", "\n\n", body).strip()
    return clean(body)


def summary_of(body: str) -> str:
    flat = re.sub(r"\s+", " ", body.replace("**", "")).strip()
    return flat[:90] + ("…" if len(flat) > 90 else "")


def main() -> None:
    state = ns.load_state()
    done = state.setdefault("done", {})
    items = ns.rss_items()

    if not done:                                                       # 기록이 하나도 없을 때만
        for i in items:
            done.setdefault(i["logNo"], {"title": i["title"], "slug": "(자동화 전 글)"})
        ns.save_state(state)
        print(f"첫 실행: 지금 있는 네이버 글 {len(items)}개를 '이미 옮김'으로 적었습니다.")
        print("NEW=0")
        return

    new = [i for i in reversed(items) if i["logNo"] not in done]      # 오래된 글부터
    made = 0
    for i in new:
        body = to_body(ns.post_text(i["logNo"]))
        if not body:
            continue
        date, slug = post_date(i["date"]), f"naver-{i['logNo']}"
        title = clean(html.unescape(i["title"])).replace("\n", " ").strip()
        text = (f"title: {title}\ndate: {date}\ncategory: 네이버 블로그\nslug: {slug}\n"
                f"summary: {summary_of(body)}\nnaver: {i['link']}\n---\n{body}\n")
        (ns.ROOT / "posts" / f"{date}_{slug}.txt").write_text(text, encoding="utf-8")
        done[i["logNo"]] = {"title": i["title"], "slug": slug}
        made += 1
        print(f"  옮김: {title} → blog/{slug}.html")
    ns.save_state(state)
    print(f"NEW={made}")


if __name__ == "__main__":
    main()
