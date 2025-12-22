import requests
from bs4 import BeautifulSoup
import os
import re
from datetime import datetime

# --- 설정값 ---
WEBHOOK_MAIN = os.getenv("DISCORD_WEBHOOK") # 기존 이름 유지
HEADERS = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'}

def get_notices(url):
    try:
        response = requests.get(url, headers=HEADERS)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        notices = []
        items = soup.select('.board-list-wrap li')
        for item in items:
            title_tag = item.select_one('.board-list-content-title a')
            if not title_tag: continue
            title = title_tag.text.strip()
            href = title_tag.get('href', '')
            link = url.split('.do')[0] + ".do" + href if ".do" in href else url + href
            match = re.search(r'articleNo=(\d+)', href)
            if match:
                num = int(match.group(1))
                notices.append({'num': num, 'title': title, 'link': link})
        notices.sort(key=lambda x: x['num'], reverse=True)
        return notices
    except Exception as e:
        print(f"[!] {url} 크롤링 에러: {e}")
        return []

def send_discord_embed(webhook_url, title, link, site_name, color):
    """디스코드 임베드 메시지를 전송하는 함수"""
    if not webhook_url: return

    # 임베드 구조 설정
    payload = {
        "embeds": [{
            "title": f"📌 {title}",
            "url": link,
            "description": f"새로운 공지가 등록되었습니다.",
            "color": color, # 10진수 색상값
            "author": {
                "name": f"성균관대학교 - {site_name}",
                "icon_url": "https://www.skku.edu/_res/skku/img/common/logo_footer.png"
            },
            "timestamp": datetime.utcnow().isoformat(),
            "footer": {
                "text": "SKKU Notice Bot"
            }
        }]
    }
    requests.post(webhook_url, json=payload)

def process_site(url, db_file, site_name, webhook_url, color, keywords=None):
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
        if keywords is None or any(kw in n['title'] for kw in keywords):
            # 임베드 함수 호출
            send_discord_embed(webhook_url, n['title'], n['link'], site_name, color)
            print(f"[+] 임베드 알림 전송: {n['title']}")
        
    if new_notices:
        with open(db_file, 'w') as f:
            f.write(str(max(n['num'] for n in notices)))

def main():
    # 사이트별 색상 설정 (10진수 색상 코드)
    # 성대 상징색(녹색 계열): 32768, 금색 계열: 16761035
    COLOR_MAIN = 32768
    COLOR_AICON = 16761035

    # 1. 성대 메인
    process_site("https://www.skku.edu/skku/campus/skk_comm/notice01.do", 
                 "last_notice_main.txt", "성대메인", none)
    
    # 2. AICON (전체 공지)
    process_site("https://aicon.skku.edu/aicon/notice.do", 
                 "last_notice_aicon.txt", "AICON", WEBHOOK_MAIN, COLOR_AICON, None)

if __name__ == "__main__":
    main()
