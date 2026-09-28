"""구글 서치콘솔에 sitemap.xml 을 다시 제출해 새 글이 생겼다고 알려주는 스크립트.

- GitHub Actions 에서 새 글이 올라간 뒤에 실행된다.
- 비밀값 GSC_SERVICE_ACCOUNT (서비스 계정 JSON 키 전체) 가 없으면 아무것도 안 하고 끝난다.
- 서비스 계정 이메일이 서치콘솔 속성 https://obl-marketing.kr/ 의 '소유자' 로 추가돼 있어야 한다.
"""
import json
import os
import urllib.parse

SITE = "https://obl-marketing.kr/"
SITEMAP = "https://obl-marketing.kr/sitemap.xml"
SCOPES = ["https://www.googleapis.com/auth/webmasters"]


def main():
    raw = os.environ.get("GSC_SERVICE_ACCOUNT", "").strip()
    if not raw:
        print("구글: GSC_SERVICE_ACCOUNT 비밀값이 없어 건너뜀")
        return

    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession

    creds = service_account.Credentials.from_service_account_info(
        json.loads(raw), scopes=SCOPES)
    session = AuthorizedSession(creds)

    url = "https://www.googleapis.com/webmasters/v3/sites/{}/sitemaps/{}".format(
        urllib.parse.quote(SITE, safe=""), urllib.parse.quote(SITEMAP, safe=""))
    res = session.put(url, timeout=30)
    if res.ok:
        print(f"구글: 사이트맵 다시 제출 완료 ({res.status_code})")
    else:
        print(f"구글: 사이트맵 제출 실패 {res.status_code} {res.text[:300]}")


if __name__ == "__main__":
    main()
