"""온뷰랩 홈페이지 블로그 만들기.

posts/ 폴더의 글 파일(.txt)을 읽어
  - blog/<slug>.html  (글 페이지)
  - blog/index.html   (글 목록)
  - index.html        (첫 화면 블로그 칸, 최신 4개)
  - sitemap.xml       (site.json 에 도메인이 있을 때)
를 만든다. 금지어가 들어간 글이 있으면 아무것도 만들지 않고 멈춘다.

글 파일 모양:
    title: 제목
    date: 2026-09-21
    category: 플레이스
    slug: place-basic-setting        (주소에 쓰는 영어 이름)
    summary: 목록에 보일 한두 줄
    ---
    본문. 빈 줄로 문단을 나눈다.
    ## 소제목
    > 강조 상자
    **굵게**
"""
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
POSTS = ROOT / "posts"
BLOG = ROOT / "blog"
# 기존 홈페이지(obl-marketing.kr)와 같은 연락처를 쓴다
KAKAO = "http://pf.kakao.com/_xjvXxfX"
CONSULT = "https://naver.me/551aHEwL"
TEL = "tel:+821028020674"

# 2026-09-21 사용자: 상위노출 · 지식인 · 보장 · 1위 · 100% 같은 말은 빼고 올린다
BANNED = ["상위노출", "상위 노출", "지식인", "지식iN", "보장", "1위", "100%", "100 %"]



def header(prefix: str) -> str:
    return f"""<header class="top">
  <div class="wrap">
    <a class="logo" href="{prefix}">
      <img src="{prefix}logo.png" alt="">
      ONLINE BEAUTY LAB <small>온뷰랩</small>
    </a>
    <nav class="nav">
      <a href="{prefix}#service">서비스</a>
      <a href="{prefix}#process">진행 방식</a>
      <a href="{prefix}#case">사례</a>
      <a href="{prefix}#pricing">요금</a>
      <a href="{prefix}blog/about-onviewlab.html">회사 소개</a>
      <a href="{prefix}blog/">블로그</a>
    </nav>
    <a class="btn btn-a btn-sm" href="{CONSULT}" target="_blank" rel="noopener">무료 상담 신청</a>
  </div>
</header>"""


FOOTER = f"""<footer>
  <div class="wrap">
    <div><strong>ONLINE BEAUTY LAB · 온뷰랩</strong> · 뷰티 매장 전문 마케팅</div>
    <div><a href="{CONSULT}" target="_blank" rel="noopener">무료 상담 신청</a> · <a href="{KAKAO}" target="_blank" rel="noopener">카카오톡</a> · <a href="{TEL}">010-2802-0674</a> · <a href="https://blog.naver.com/twmsgyu" target="_blank" rel="noopener">네이버 블로그</a></div>
    <div class="biz">대표자 김민규 · 사업자번호 125-32-01712 · 통신판매업 제 2026-경기안산-1103 호 · 월~금 09:00~19:00 · onview.lab@gmail.com</div>
  </div>
</footer>
<a class="btn btn-kakao float-kakao" href="{KAKAO}" target="_blank" rel="noopener">카카오톡으로 상담하기</a>"""


def head(title: str, desc: str, prefix: str, og_type: str = "website", canonical: str = "") -> str:
    t, d = html.escape(title), html.escape(desc)
    can = f'\n<link rel="canonical" href="{canonical}">' if canonical else ""
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{t}</title>
<meta name="description" content="{d}">
<meta property="og:type" content="{og_type}">
<meta property="og:title" content="{t}">
<meta property="og:description" content="{d}">{can}
<link rel="icon" href="{prefix}logo.png" type="image/png">
<link rel="stylesheet" href="{prefix}style.css">
</head>
<body>
"""


def load_site() -> dict:
    p = ROOT / "site.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def parse(path: Path) -> dict:
    text = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    meta_part, _, body = text.partition("\n---\n")
    meta = {}
    for line in meta_part.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    for k in ("title", "date", "category", "slug", "summary"):
        if not meta.get(k):
            sys.exit(f"[{path.name}] '{k}:' 줄이 없습니다.")
    if not re.fullmatch(r"[a-z0-9-]+", meta["slug"]):
        sys.exit(f"[{path.name}] slug 는 영어 소문자 · 숫자 · - 만 쓸 수 있습니다: {meta['slug']}")
    meta["body"] = body.strip()
    meta["file"] = path.name
    return meta


def banned_in(post: dict) -> list[str]:
    whole = " ".join([post["title"], post["summary"], post["body"]])
    return [w for w in BANNED if w in whole]


def inline(s: str) -> str:
    s = html.escape(s, quote=False)
    return re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)


def render_body(body: str) -> str:
    out = []
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if not block:
            continue
        if block.startswith("## "):
            out.append(f"  <h2>{inline(block[3:].strip())}</h2>")
        elif block.startswith(">"):
            lines = [ln.lstrip("> ").strip() for ln in block.splitlines()]
            out.append(f"  <blockquote>{'<br>'.join(inline(ln) for ln in lines)}</blockquote>")
        else:
            out.append(f"  <p>{'<br>'.join(inline(ln.strip()) for ln in block.splitlines())}</p>")
    return "\n".join(out)


def faq_items(body: str) -> list[tuple[str, str]]:
    """본문에서 '## Q. 질문' 소제목과 그 아래 문단(다음 소제목 전까지)을 질문 · 답 쌍으로 뽑는다."""
    items, q, ans = [], None, []
    for block in re.split(r"\n\s*\n", body):
        block = block.strip()
        if block.startswith("## "):
            if q:
                items.append((q, " ".join(ans)))
            head = block[3:].strip()
            q, ans = (head[2:].strip(), []) if head.startswith("Q.") else (None, [])
        elif q and block:
            text = re.sub(r"\*\*(.+?)\*\*", r"\1", block)
            ans.append(" ".join(ln.lstrip("-> ").strip() for ln in text.splitlines()))
    if q:
        items.append((q, " ".join(ans)))
    return [(q, a) for q, a in items if a]


def nice_date(d: str) -> str:
    y, m, dd = d.split("-")
    return f"{int(y)}. {int(m)}. {int(dd)}."


def post_page(p: dict, site: dict) -> str:
    domain = site.get("domain", "").rstrip("/")
    canonical = f"{domain}/blog/{p['slug']}.html" if domain else ""
    ld = {"@context": "https://schema.org", "@type": "BlogPosting", "headline": p["title"],
          "description": p["summary"], "datePublished": p["date"], "dateModified": p["date"],
          "inLanguage": "ko", "articleSection": p["category"],
          "author": {"@type": "Organization", "name": "온뷰랩 (ONLINE BEAUTY LAB)", "url": "https://obl-marketing.kr/"},
          "publisher": {"@type": "Organization", "name": "온뷰랩 (ONLINE BEAUTY LAB)", "url": "https://obl-marketing.kr/"}}
    if canonical:
        ld["mainEntityOfPage"] = canonical
    ld_tag = ('<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + "</script>\n")
    faq = faq_items(p["body"])
    if faq:                                      # "## Q. 질문" 소제목이 있으면 AI 가 읽는 FAQ 표시도 넣는다
        faq_ld = {"@context": "https://schema.org", "@type": "FAQPage",
                  "mainEntity": [{"@type": "Question", "name": q,
                                  "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in faq]}
        ld_tag += '<script type="application/ld+json">' + json.dumps(faq_ld, ensure_ascii=False) + "</script>\n"
    page_head = head(f"{p['title']} | 온뷰랩", p["summary"], "../", "article", canonical)
    page_head = page_head.replace("</head>", ld_tag + "</head>")
    return page_head + header("../") + f"""

<main>
<article class="article">
  <span class="eyebrow">{html.escape(p['category'])}</span>
  <h1>{inline(p['title'])}</h1>
  <div class="meta">온뷰랩 · {nice_date(p['date'])}</div>
  <div style="height:16px"></div>
{render_body(p['body'])}

  <p style="margin-top:36px;display:flex;flex-wrap:wrap;gap:10px"><a class="btn btn-a" href="{CONSULT}" target="_blank" rel="noopener">무료 상담 신청</a><a class="btn btn-kakao" href="{KAKAO}" target="_blank" rel="noopener">카카오톡으로 물어보기</a></p>
  <p style="margin-top:28px"><a href="./">← 블로그 목록으로</a></p>
</article>
</main>

{FOOTER}
</body>
</html>
"""


def card(p: dict, href_prefix: str) -> str:
    return f"""      <a class="card post-card" href="{href_prefix}{p['slug']}.html">
        <div class="meta">{html.escape(p['category'])} · {nice_date(p['date'])}</div>
        <h3>{inline(p['title'])}</h3>
        <p>{inline(p['summary'])}</p>
      </a>"""


def blog_index(posts: list[dict]) -> str:
    cards = "\n".join(card(p, "") for p in posts)
    return head("블로그 | 온뷰랩", "뷰티샵 원장님께 도움이 되는 플레이스 · 블로그 · 체험단 마케팅 이야기, 온뷰랩 블로그.", "../") + header("../") + f"""
<main>
<section>
  <div class="wrap">
    <div class="sec-head">
      <div class="label">BLOG</div>
      <h2>원장님께 도움이 되는 마케팅 이야기</h2>
      <p>플레이스 · 블로그 · 체험단을 직접 운영하며 알게 된 내용을 정리합니다.</p>
    </div>
    <div class="grid grid-2">
{cards}
    </div>
  </div>
</section>
</main>
{FOOTER}
</body>
</html>
"""


def update_home(posts: list[dict]) -> None:
    home = ROOT / "index.html"
    text = home.read_text(encoding="utf-8")
    cards = "\n".join(card(p, "blog/") for p in posts[:4])
    block = f"<!--POSTS-->\n    <div class=\"grid grid-2\">\n{cards}\n    </div>\n    <!--/POSTS-->"
    new, n = re.subn(r"<!--POSTS-->.*?<!--/POSTS-->", lambda _m: block, text, flags=re.S)
    if n == 1:
        home.write_text(new, encoding="utf-8")


AI_BOTS = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-SearchBot", "PerplexityBot",
           "Google-Extended", "Bingbot", "Googlebot", "Yeti"]


def robots(site: dict) -> None:
    """2026-09-21 사용자: ChatGPT 가 글을 수집하게 하려고 웹 블로그를 쓴다 — AI 검색 로봇을 이름으로 허용한다."""
    domain = site.get("domain", "").rstrip("/")
    lines = []
    for bot in AI_BOTS:
        lines += [f"User-agent: {bot}", "Allow: /", ""]
    lines += ["User-agent: *", "Allow: /", ""]
    if domain:
        lines.append(f"Sitemap: {domain}/sitemap.xml")
    (ROOT / "robots.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")


def llms_txt(posts: list[dict], site: dict) -> None:
    """AI 가 사이트를 한눈에 알 수 있게 요약한 llms.txt."""
    domain = site.get("domain", "").rstrip("/")
    base = domain or ""
    out = ["# 온뷰랩 ONLINE BEAUTY LAB (뷰티 매장 전문 마케팅)", "",
           "> 미용실 · 네일샵 · 피부관리실 · 반영구 등 뷰티샵 전문 마케팅 대행사. 1:1 컨설팅으로 매장 상태를 먼저 확인하고 "
           "플레이스 · 브랜드 블로그 · 체험단 · SNS 마케팅을 데이터 기반으로 운영합니다.", "",
           f"- 홈페이지: {base or 'https://obl-marketing.kr'}/", f"- 무료 상담 신청: {CONSULT}", f"- 카카오톡 채널: {KAKAO}",
           "- 전화: 010-2802-0674", "- 이메일: onview.lab@gmail.com", "- 대표자: 김민규 (경기 안산)",
           "- 네이버 블로그: https://blog.naver.com/twmsgyu", "", "## 블로그 글", ""]
    out += [f"- [{p['title']}]({base}/blog/{p['slug']}.html): {p['summary']}" for p in posts]
    (ROOT / "llms.txt").write_text("\n".join(out) + "\n", encoding="utf-8")


def sitemap(posts: list[dict], site: dict) -> None:
    domain = site.get("domain", "").rstrip("/")
    if not domain:
        return
    urls = [(f"{domain}/", posts[0]["date"] if posts else ""), (f"{domain}/blog/", posts[0]["date"] if posts else "")]
    urls += [(f"{domain}/blog/{p['slug']}.html", p["date"]) for p in posts]
    items = "\n".join(f"  <url><loc>{u}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>" for u, d in urls)
    (ROOT / "sitemap.xml").write_text(
        f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{items}\n</urlset>\n',
        encoding="utf-8")


def main() -> None:
    site = load_site()
    posts = [parse(f) for f in sorted(POSTS.glob("*.txt"))]
    bad = [(p["file"], banned_in(p)) for p in posts if banned_in(p)]
    if bad:
        for f, words in bad:
            print(f"금지어: {f} → {', '.join(words)}")
        sys.exit("금지어가 있어 만들지 않았습니다. 위 글을 고친 뒤 다시 실행하세요.")
    slugs = [p["slug"] for p in posts]
    dup = {s for s in slugs if slugs.count(s) > 1}
    if dup:
        sys.exit(f"slug 가 겹칩니다: {', '.join(dup)}")
    posts.sort(key=lambda p: (p["date"], p["file"]), reverse=True)
    posts.sort(key=lambda p: p.get("pin") != "yes")          # 'pin: yes' 글은 목록 맨 위에 고정

    BLOG.mkdir(exist_ok=True)
    keep = {f"{p['slug']}.html" for p in posts} | {"index.html"}
    for old in BLOG.glob("*.html"):              # posts/ 에서 지운 글은 페이지도 지운다
        if old.name not in keep:
            old.unlink()
    for p in posts:
        (BLOG / f"{p['slug']}.html").write_text(post_page(p, site), encoding="utf-8")
    (BLOG / "index.html").write_text(blog_index(posts), encoding="utf-8")
    update_home(posts)
    sitemap(posts, site)
    robots(site)
    llms_txt(posts, site)
    print(f"글 {len(posts)}개를 만들었습니다.")


if __name__ == "__main__":
    main()
