import requests
from bs4 import BeautifulSoup
import os
import re

# --- 설정값 ---
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

# 1. 메인 공지 설정
URL_MAIN = "https://www.skku.edu/skku/campus/skk_comm/notice01.do"
DB_MAIN = "last_notice_main.txt"
KEYWORDS_MAIN = ["장학", "AI", "대학원", "근로", "참여자", "인공지능", "성적", "수강신청"]]

# 2. AICON 공지 설정
URL_AICON = "https://aicon.skku.edu/aicon/notice.do"
DB_AICON = "last_notice_aicon.txt"

def get_notices(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        notices = []
        
        # 성대 게시판 특유의 li 구조 타겟팅
        items = soup.select('.board-list-wrap li')
        for item in items:
            title_tag = item.select_one('.board-list-content-title a')
            if not title_tag: continue

            title = title_tag.text.strip()
            href = title_tag.get('href', '')
            link = url + href
            
            match = re.search(r'articleNo=(\d+)', href)
            if match:
                num = int(match.group(1))
                notices.append({'num': num, 'title': title, 'link': link})
        
        notices.sort(key=lambda x: x['num'], reverse=True)
        return notices
    except Exception as e:
        print(f"[!] {url} 크롤링 에러: {e}")
        return []

def send_discord_msg(content):
    if not DISCORD_WEBHOOK_URL: return
    requests.post(DISCORD_WEBHOOK_URL, json={"content": content})

def process_site(url, db_file, site_name, keywords=None):
    notices = get_notices(url)
    if not notices: return

    last_num = 0
    if os.path.exists(db_file):
        with open(db_file, 'r') as f:
            line = f.read().strip()
            if line: last_num = int(line)

    new_notices = [n for n in notices if n['num'] > last_num]
    print(f"[*] {site_name} 새 공지: {len(new_notices)}개")

    for n in reversed(new_notices):
        # 키워드가 있으면 필터링, 없으면(None) 모두 통과
        if keywords is None or any(kw in n['title'] for kw in keywords):
            tag = f"[{site_name}]"
            msg = f"🔔 **{tag} 새 공지!**\n📌 제목: {n['title']}\n🔗 <{n['link']}>"
            send_discord_msg(msg)
            print(f"[+] 알림 전송: {n['title']}")
        
    if new_notices:
        with open(db_file, 'w') as f:
            f.write(str(max(n['num'] for n in notices)))

def main():
    # 사이트 1: 메인 공지 (키워드 필터링 적용)
    process_site(URL_MAIN, DB_MAIN, "성대메인", KEYWORDS_MAIN)
    
    # 사이트 2: AICON 공지 (모든 글 알림 - Keywords 자리에 None 입력)
    process_site(URL_AICON, DB_AICON, "AICON", None)

if __name__ == "__main__":
    main()

