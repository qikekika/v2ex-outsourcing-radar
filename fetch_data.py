#!/usr/bin/env python3
"""
V2EX 外包节点数据抓取脚本
- 从 V2EX RSS Feed 获取最新帖子
- 通过 Jina AI Reader 解析详情页内容
- 提取预算、技术栈、联系方式、紧急度等关键信息
- 仅保留买家帖子（求、找人、需要、预算等关键词）
- 输出 data.json 供前端使用
"""

import json
import re
import requests
import time
from datetime import datetime
from typing import List, Dict, Optional

V2EX_RSS = "https://www.v2ex.com/feed/outsourcing.xml"
V2EX_JSON = "https://www.v2ex.com/api/topics/show.json?node_name=outsourcing"
# Try to get more pages from JSON API
V2EX_JSON_PAGES = [f"https://www.v2ex.com/api/topics/show.json?node_name=outsourcing&page={i}" for i in range(1, 4)]

BUYER_KEYWORDS = [
    '求', '找人', '找个', '谁能', '需要', '急需', '外包', '兼职', '接单',
    '预算', '报价', '多少钱', '雇佣', '招募', '招人', '发包', '甲方', '买家',
    'looking for', 'need', 'hire', 'budget', 'quote', 'freelance',
    'outsourcing', 'rfp', 'help wanted', '求助', '求推荐'
]

SELLER_KEYWORDS = [
    '接单', '承接', '提供', '服务', '出售', '代做', '代写', '外包服务',
    '团队', '工作室', '个人开发', '全栈', '独立开发', 'demo', '作品集',
    '案例', '报价单', '价目表', '擅长', '技术栈', '经验', '年薪'
]

TECH_KEYWORDS = [
    'Python', 'Java', 'Go', 'Golang', 'C++', 'C#', 'JavaScript', 'TypeScript',
    'React', 'Vue', 'Next.js', 'Node.js', 'Django', 'Flask', 'FastAPI', 'Spring',
    'MySQL', 'PostgreSQL', 'Redis', 'Docker', 'Kubernetes', 'AWS', 'GCP', 'Azure',
    'Linux', '爬虫', '逆向', 'AI', 'LLM', '大模型', '算法', '区块链', 'Web3',
    'Solidity', 'Rust', 'PHP', 'Laravel', 'Android', 'iOS', 'Flutter',
    'React Native', 'Electron', 'Qt', 'C', '嵌入式', '硬件', 'FPGA', 'Verilog'
]

BUDGET_PATTERNS = [
    re.compile(r'(\d+(?:\.\d+)?)\s*[kK万]'),
    re.compile(r'[预算报价价格薪资]\s*[:：]?\s*(\d+(?:\.\d+)?)\s*[kK万]?', re.IGNORECASE),
    re.compile(r'(\d+(?:\.\d+)?)\s*[-~到]\s*(\d+(?:\.\d+)?)\s*[kK万]'),
    re.compile(r'¥\s*(\d+(?:,\d{3})*(?:\.\d+)?)'),
    re.compile(r'￥\s*(\d+(?:,\d{3})*(?:\.\d+)?)'),
]

CONTACT_PATTERNS = [
    re.compile(r'(?:微信|wx|wechat|vx)[:：]\s*([a-zA-Z0-9_-]{6,20})', re.IGNORECASE),
    re.compile(r'(?:QQ|qq)[:：]\s*(\d{5,12})', re.IGNORECASE),
    re.compile(r'(?:邮箱|email|mail)[:：]\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', re.IGNORECASE),
    re.compile(r'(?:Telegram|TG|tg)[:：]\s*(@?[a-zA-Z0-9_]{4,32})', re.IGNORECASE),
    re.compile(r'(?:Base64|base64)[:：]\s*([A-Za-z0-9+/=]{20,})', re.IGNORECASE),
    re.compile(r'(?:联系|contact)[:：]\s*([^\s\n]{4,50})', re.IGNORECASE),
]

URGENT_KEYWORDS = ['急', '急需', '马上', '立即', '尽快', 'ASAP', 'urgent', '即刻', '火速']


def is_buyer_post(title: str, content: str) -> bool:
    text = (title + ' ' + content).lower()
    # Hard filter: explicit seller markers
    seller_hard_markers = ['[接单]', '[承接]', '[提供]', '[出售]', '[代做]', '[代写]', '[外包服务]', '[团队]', '[工作室]', '[个人开发]', '[全栈]', '[独立开发]', '[作品集]', '[案例]', '[报价单]', '[价目表]']
    for marker in seller_hard_markers:
        if marker.lower() in text:
            return False

    buyer_score = sum(1 for kw in BUYER_KEYWORDS if kw.lower() in text)
    seller_score = sum(1 for kw in SELLER_KEYWORDS if kw.lower() in text)
    return buyer_score > seller_score


def parse_budget(text: str) -> Optional[int]:
    max_val = 0
    for pattern in BUDGET_PATTERNS:
        for match in pattern.finditer(text):
            val_str = match.group(1).replace(',', '')
            try:
                val = float(val_str)
                matched_text = match.group(0)
                unit = 10000 if ('万' in matched_text or 'k' in matched_text.lower() or 'K' in matched_text) else 1
                max_val = max(max_val, int(val * unit))
            except ValueError:
                continue
    return max_val if max_val > 0 else None


def extract_tech(text: str) -> List[str]:
    # Filter out navigation/UI text that Jina AI returns from V2EX layout
    nav_keywords = ['way to explore', 'home', 'sign up', 'sign in', 'v2ex', 'creative commons', 'about', 'faq', 'api', '节点', '登录', '注册', '广告投放', '版权声明']
    text_lower = text.lower()
    if any(nav in text_lower for nav in nav_keywords):
        # Only extract from first 2000 chars to avoid nav/footer
        text = text[:2000]
    return [t for t in TECH_KEYWORDS if re.search(r'\b' + re.escape(t) + r'\b', text, re.IGNORECASE)]


def extract_contacts(text: str) -> List[str]:
    contacts = []
    for pattern in CONTACT_PATTERNS:
        for match in pattern.finditer(text):
            contacts.append(match.group(0))
    return list(set(contacts))


def extract_urgency(text: str) -> bool:
    return any(re.search(kw, text, re.IGNORECASE) for kw in URGENT_KEYWORDS)


def fetch_v2ex_rss() -> List[Dict]:
    try:
        resp = requests.get(V2EX_RSS, timeout=30, headers={'User-Agent': 'v2ex-radar/1.0'})
        resp.raise_for_status()
        return parse_rss(resp.text)
    except Exception as e:
        print(f"RSS fetch failed: {e}")
        return []


def fetch_v2ex_json() -> List[Dict]:
    all_items = []
    seen_ids = set()
    for url in V2EX_JSON_PAGES:
        try:
            resp = requests.get(url, timeout=30, headers={'User-Agent': 'v2ex-radar/1.0'})
            resp.raise_for_status()
            data = resp.json()
            if not data:
                break
            new_items = 0
            for item in data:
                item_id = item.get('id')
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    all_items.append({
                        'id': item_id,
                        'title': item.get('title', ''),
                        'content': item.get('content', ''),
                        'url': f"https://www.v2ex.com/t/{item_id}",
                        'created': item.get('created', int(time.time())),
                        'member': {'username': item.get('member', {}).get('username', 'unknown')}
                    })
                    new_items += 1
            if new_items == 0:
                break  # No new items, stop pagination
            time.sleep(0.5)  # Rate limit
        except Exception as e:
            print(f"JSON API fetch failed for {url}: {e}")
            break
    return all_items


def parse_rss(xml: str) -> List[Dict]:
    items = []
    item_regex = re.compile(r'<item>([\s\S]*?)</item>')
    for match in item_regex.finditer(xml):
        item_xml = match.group(1)
        title = (re.search(r'<title><!\[CDATA\[(.*?)\]\]></title>', item_xml) or
                re.search(r'<title>(.*?)</title>', item_xml))
        link = re.search(r'<link>(.*?)</link>', item_xml)
        desc = (re.search(r'<description><!\[CDATA\[(.*?)\]\]></description>', item_xml) or
               re.search(r'<description>(.*?)</description>', item_xml))
        pub_date = re.search(r'<pubDate>(.*?)</pubDate>', item_xml)

        title_text = title.group(1) if title else ''
        link_text = link.group(1) if link else ''
        desc_text = desc.group(1) if desc else ''
        pub_date_text = pub_date.group(1) if pub_date else ''

        id_match = re.search(r'/t/(\d+)', link_text)
        topic_id = int(id_match.group(1)) if id_match else int(time.time() * 1000)

        created = 0
        if pub_date_text:
            try:
                from email.utils import parsedate_to_datetime
                created = int(parsedate_to_datetime(pub_date_text).timestamp())
            except:
                created = int(time.time())
        else:
            created = int(time.time())

        items.append({
            'id': topic_id,
            'title': title_text,
            'content': desc_text,
            'url': link_text,
            'created': created,
            'member': {'username': 'v2ex'}
        })
    return items


def enrich_with_jina(item: Dict) -> Dict:
    try:
        url = item['url']
        # Use Jina AI to fetch the actual topic page content
        jina_url = f"https://r.jina.ai/http://{url.replace('https://', '').replace('http://', '')}"
        resp = requests.get(jina_url, timeout=30, headers={'User-Agent': 'v2ex-radar/1.0'})
        if resp.status_code == 200:
            full_content = resp.text
            # Only use if we got substantial content (not just navigation)
            if len(full_content) > 200 and 'way to explore' not in full_content[:500]:
                item['content'] = full_content[:5000]
            elif len(full_content) > len(item.get('content', '')):
                item['content'] = full_content[:5000]
    except Exception as e:
        print(f"Jina enrich failed for {item.get('url')}: {e}")
    return item


def process_item(item: Dict) -> Optional[Dict]:
    title = item.get('title', '')
    content = item.get('content', '')
    url = item.get('url', f"https://www.v2ex.com/t/{item.get('id')}")
    created = item.get('created', int(time.time()))
    author = item.get('member', {}).get('username', 'unknown')

    if not is_buyer_post(title, content):
        return None

    full_text = title + '\n' + content
    budget = parse_budget(full_text)
    techs = extract_tech(full_text)
    contacts = extract_contacts(full_text)
    urgent = extract_urgency(full_text)
    days_ago = max(0, int((time.time() - created) / 86400))

    return {
        'id': item.get('id'),
        'title': title,
        'url': url,
        'author': author,
        'created': created,
        'daysAgo': days_ago,
        'budget': budget,
        'techs': techs,
        'contacts': contacts,
        'urgent': urgent,
        'snippet': content[:200].replace('\n', ' ')
    }


def main():
    import sys
    import io
    # Force UTF-8 output on Windows
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

    print("Fetching V2EX outsourcing posts...")

    # Try RSS first (has more items and full descriptions)
    raw_items = fetch_v2ex_rss()
    if not raw_items:
        print("RSS empty, trying JSON API...")
        raw_items = fetch_v2ex_json()

    print(f"Got {len(raw_items)} raw items")

    # Enrich with Jina AI for first 30 items
    enriched_items = []
    for item in raw_items[:30]:
        enriched = enrich_with_jina(item)
        enriched_items.append(enriched)
        time.sleep(0.3)

    signals = []
    all_techs = set()
    for item in enriched_items:
        processed = process_item(item)
        if processed:
            signals.append(processed)
            all_techs.update(processed['techs'])

    print(f"Filtered to {len(signals)} buyer signals")
    print(f"Found techs: {sorted(all_techs)}")

    signals.sort(key=lambda s: (
        not s['urgent'],
        -(s['budget'] or 0),
        -s['created']
    ))

    output = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'signals': signals,
        'techs': sorted(all_techs),
        'total_fetched': len(raw_items),
        'total_signals': len(signals)
    }

    with open('data.json', 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("data.json written successfully")
    print(f"Total signals: {len(signals)}")
    for s in signals[:5]:
        budget_str = f"¥{s['budget']:,}" if s['budget'] else "无预算"
        print(f"  - {s['title'][:50]}... | {budget_str} | {', '.join(s['techs'][:3])} | {'⚡' if s['urgent'] else ''}")


if __name__ == '__main__':
    main()