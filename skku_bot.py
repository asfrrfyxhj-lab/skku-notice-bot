import requests
from bs4 import BeautifulSoup
import os

# --- 설정값 ---
# DISCORD_WEBHOOK_URL = "https://discordapp.com/api/webhooks/1452553441250381897/013WGyLd3NPaMCEZWOf_rOTMpBU46wv9OmMFbEuQsjExVeBmVEe1RrD4pydfeg_NyFXp"
# 수정 후: 시스템(깃허브)에 저장된 비밀 값을 가져오라는 뜻입니다.
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK")
SKKU_NOTICE_URL = "https://www.skku.edu/skku/campus/skk_comm/notice01.do"
KEYWORDS = ["장학", "AI", "대학원", "근로", "참여자", "인공지능", "성적", "수강신청"] 
DB_FILE = "last_notice.txt"

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
}

def get_latest_notices():
    try:
        response = requests.get(SKKU_NOTICE_URL, headers=HEADERS)
        response.encoding = 'utf-8'
        soup = BeautifulSoup(response.text, 'html.parser')
        notices = []
        
        # 1. 공지사항 리스트를 담고 있는 전체 컨테이너를 찾습니다.
        # 성대 사이트는 보통 board-list-wrap 클래스를 사용합니다.
        container = soup.select_one('.board-list-wrap')
        if not container:
            print("[!] 공지사항 컨테이너를 찾을 수 없습니다.")
            return []

        # 2. 표(tr)가 아니라 리스트(li) 태그를 모두 가져옵니다.
        items = container.select('li')
        print(f"[*] 사이트에서 {len(items)}개의 공지 아이템을 발견했습니다.")
        
        for item in items:
            # 제목이 들어있는 태그 찾기
            title_tag = item.select_one('.board-list-content-title a')
            if not title_tag:
                continue

            title = title_tag.text.strip()
            # href에서 글 번호를 추출하거나 전체 링크를 만듭니다.
            href = title_tag.get('href', '')
            link = "https://www.skku.edu/skku/campus/skk_comm/notice01.do" + href
            
            # 글 번호(ID) 추출 - href에 'articleNo=12345' 형태가 있는지 확인
            import re
            match = re.search(r'articleNo=(\d+)', href)
            if match:
                num = int(match.group(1))
                notices.append({'num': num, 'title': title, 'link': link})
        
        # 번호가 큰 순서(최신순)로 정렬
        notices.sort(key=lambda x: x['num'], reverse=True)
        return notices

    except Exception as e:
        print(f"[!] 에러 발생: {e}")
        return []

def send_discord_msg(content):
    data = {"content": content}
    requests.post(DISCORD_WEBHOOK_URL, json=data)

def main():
    notices = get_latest_notices()
    if not notices:
        print("[!] 공지사항을 하나도 가져오지 못했습니다. 구조 확인이 필요합니다.")
        return

    # 마지막 번호 로드
    last_num = 0
    if os.path.exists(DB_FILE):
        with open(DB_FILE, 'r') as f:
            line = f.read().strip()
            if line: last_num = int(line)
    
    print(f"[*] 기록된 마지막 번호: {last_num}")
    
    new_notices = [n for n in notices if n['num'] > last_num]
    print(f"[*] 새 공지 개수: {len(new_notices)}개")

    for n in reversed(new_notices):
        if any(kw in n['title'] for kw in KEYWORDS):
            msg = f"🔔 **성대 새 공지!**\n📌 제목: {n['title']}\n🔗 <{n['link']}>"
            send_discord_msg(msg)
            print(f"[+] 알림 전송: {n['title']}")
        
    if new_notices:
        with open(DB_FILE, 'w') as f:
            f.write(str(max(n['num'] for n in notices)))

if __name__ == "__main__":
    main()