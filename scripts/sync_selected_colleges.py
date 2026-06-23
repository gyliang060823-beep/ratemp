import hashlib
import html
import json
import os
import re
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse
from urllib.request import Request, urlopen


SUPABASE_URL = "https://yongznyjoipfhusfovuw.supabase.co"
SUPABASE_KEY = "sb_publishable_oNmwyxPHP2EHQijG28q41g_OApP8_Gr"
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
OUTPUT_PATH = Path("data/selected_colleges_teachers.json")

SITES = {
    "sem": {
        "college": "经济管理学院",
        "home": "https://www.sem.tsinghua.edu.cn/",
        "start": "https://www.sem.tsinghua.edu.cn/js/szdw.htm",
    },
    "civil": {
        "college": "土木水利学院",
        "home": "https://www.civil.tsinghua.edu.cn/",
        "start": "https://www.civil.tsinghua.edu.cn/ce/szdw/jiaosh.htm",
    },
    "sppm": {
        "college": "公共管理学院",
        "home": "https://www.sppm.tsinghua.edu.cn/",
        "start": "https://www.sppm.tsinghua.edu.cn/szdw/qzjs/qyjs.htm",
    },
    "env": {
        "college": "环境学院",
        "home": "http://www.env.tsinghua.edu.cn/",
        "start": "http://www.env.tsinghua.edu.cn/szdw/jyjs.htm",
    },
    "smarx": {
        "college": "马克思主义学院",
        "home": "http://www.smarx.tsinghua.edu.cn/",
        "start": "http://www.smarx.tsinghua.edu.cn/szqk/js.htm",
    },
}

SKIP_NAMES = {"首页", "教师", "教授", "副教授", "讲师", "下页", "尾页", "上页", "详情", "更多", "清华大学"}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self.href is not None:
            text = normalize_text("".join(self.text))
            if text:
                self.links.append((self.href, text))
            self.href = None
            self.text = []


def normalize_text(value):
    return re.sub(r"\s+", " ", html.unescape(value or "")).strip()


def strip_tags(value):
    return normalize_text(re.sub(r"<[^>]+>", " ", value or ""))


def fetch(url):
    request = Request(url, headers={"User-Agent": "ratemp-selected-college-sync/0.1"})
    with urlopen(request, timeout=25) as response:
        return response.read().decode("utf-8", errors="replace")


def links(page_html, base_url):
    parser = LinkParser()
    parser.feed(page_html)
    return [(urljoin(base_url, href), text) for href, text in parser.links]


def is_name(value):
    value = normalize_text(value)
    if value in SKIP_NAMES:
        return False
    return bool(re.fullmatch(r"[\u4e00-\u9fff·]{2,5}", value))


def teacher_id(prefix, college, name, source_url):
    digest = hashlib.sha1(f"{college}::{name}::{source_url}".encode("utf-8")).hexdigest()[:16]
    return f"thu-{prefix}-{digest}"


def make_record(prefix, college, name, title, email, research, source_url):
    return {
        "id": teacher_id(prefix, college, name, source_url),
        "name": normalize_text(name),
        "college": college,
        "title": clean_missing(title),
        "email": clean_missing(email),
        "research": clean_missing(research),
        "intro": f"Imported from official Tsinghua faculty page: {source_url}",
        "source_url": source_url,
        "scraped_at": datetime.now().isoformat(timespec="seconds"),
    }


def clean_missing(value):
    text = normalize_text(value)
    return text if text else "To be added"


def page_title(page_html):
    match = re.search(r"<title>(.*?)</title>", page_html, re.S | re.I)
    if not match:
        return ""
    title = strip_tags(match.group(1))
    return title.split("-")[0].strip()


def collect_internal_pages(start_url, include_pattern, limit=60):
    start_html = fetch(start_url)
    found = {start_url}
    host = urlparse(start_url).netloc
    for href, _ in links(start_html, start_url):
        if urlparse(href).netloc != host:
            continue
        if include_pattern(href):
            found.add(href)
    return sorted(found)[:limit]


def scrape_sem():
    cfg = SITES["sem"]
    pages = collect_internal_pages(
        cfg["start"],
        lambda href: "/js/szdw" in href and href.endswith(".htm"),
        limit=40,
    )
    records = {}
    for url in pages:
        page_html = fetch(url)
        for block in re.findall(r'<div class="detailsdes">(.*?)</div>\s*</div>\s*</div>', page_html, re.S):
            name = strip_tags(re.search(r'<div class="name">(.*?)</div>', block, re.S).group(1)) if re.search(r'<div class="name">(.*?)</div>', block, re.S) else ""
            if not is_name(name):
                continue
            title_block = strip_tags(re.search(r'<div class="contenttitle">(.*?)</div>', block, re.S).group(1)) if re.search(r'<div class="contenttitle">(.*?)</div>', block, re.S) else ""
            dept_match = re.search(r"<span>(.*?)</span>", block, re.S)
            dept = strip_tags(dept_match.group(1)) if dept_match else "经济管理学院"
            title = title_block.replace(dept, "").strip()
            email_match = re.search(r"邮箱:</div>\s*<p>(.*?)</p>", block, re.S)
            email = strip_tags(email_match.group(1)) if email_match else ""
            href_match = re.search(r'<a href="([^"]+)"[^>]*>详情', block)
            source_url = urljoin(url, href_match.group(1)) if href_match else url
            rec = make_record("sem", cfg["college"], name, title, email, dept, source_url)
            records[rec["id"]] = rec
    return list(records.values())


def scrape_sppm():
    cfg = SITES["sppm"]
    page_html = fetch(cfg["start"])
    records = {}
    for arr in re.findall(r"var\s+ret\s*=\s*(\[.*?\]);", page_html, re.S):
        try:
            items = json.loads(arr)
        except json.JSONDecodeError:
            continue
        for item in items:
            name = normalize_text(item.get("showTitle", "")).replace(" ", "")
            fields = item.get("fields") or {}
            if not is_name(name):
                continue
            source_url = urljoin(cfg["start"], item.get("url", ""))
            rec = make_record("sppm", cfg["college"], name, fields.get("zc", ""), fields.get("Email", ""), fields.get("yjs", ""), source_url)
            records[rec["id"]] = rec
    return list(records.values())


def scrape_card_site(prefix, college, start_url, page_filter, default_title=""):
    pages = collect_internal_pages(start_url, page_filter, limit=80)
    records = {}
    for url in pages:
        page_html = fetch(url)
        research = page_title(page_html) or college
        for block in re.findall(r'<li[^>]*class="[^"]*wow[^"]*"[^>]*>(.*?)</li>', page_html, re.S):
            name_match = re.search(r'class="teacher-name".*?<a[^>]+href="([^"]+)"[^>]*>(.*?)</a>', block, re.S)
            if not name_match:
                continue
            name = strip_tags(name_match.group(2)).replace(" ", "")
            if not is_name(name):
                continue
            text = strip_tags(block)
            title_match = re.search(r"职称[:：]\s*([^电话邮箱]+)", text)
            title = normalize_text(title_match.group(1)) if title_match else default_title
            email_match = re.search(r"[\w.\-+]+@[\w.\-]+\.[A-Za-z]{2,}", text)
            email = email_match.group(0) if email_match else ""
            source_url = urljoin(url, name_match.group(1))
            rec = make_record(prefix, college, name, title, email, research, source_url)
            records[rec["id"]] = rec
        for href, text in links(page_html, url):
            name = text.replace(" ", "")
            if "/info/" in href and is_name(name):
                rec = make_record(prefix, college, name, default_title, "", research, href)
                records[rec["id"]] = rec
    return list(records.values())


def scrape_civil():
    cfg = SITES["civil"]
    return scrape_card_site(
        "civil",
        cfg["college"],
        cfg["start"],
        lambda href: "/ce/szdw/jiaosh/" in href and href.endswith(".htm"),
    )


def scrape_env():
    cfg = SITES["env"]
    return scrape_card_site(
        "env",
        cfg["college"],
        cfg["start"],
        lambda href: "/szdw/jyjs/" in href and href.endswith(".htm"),
    )


def scrape_smarx():
    cfg = SITES["smarx"]
    pages = collect_internal_pages(
        cfg["start"],
        lambda href: "/szqk/" in href and href.endswith(".htm"),
        limit=30,
    )
    records = []
    for url in pages:
        title = page_title(fetch(url))
        if title in {"教授", "副教授", "讲师"} or "教授" in title or "讲师" in title:
            records.extend(scrape_card_site("smarx", cfg["college"], url, lambda href: href == url, default_title=title))
    unique = {record["id"]: record for record in records}
    return list(unique.values())


def scrape_all():
    groups = {
        "sem": scrape_sem(),
        "civil": scrape_civil(),
        "sppm": scrape_sppm(),
        "env": scrape_env(),
        "smarx": scrape_smarx(),
    }
    all_records = []
    for key, records in groups.items():
        print(f"{key}: {len(records)}")
        all_records.extend(records)
    unique = {}
    for record in all_records:
        key = (record["college"], record["name"])
        current = unique.get(key)
        if not current or current["title"] == "To be added":
            unique[key] = record
    return sorted(unique.values(), key=lambda item: (item["college"], item["research"], item["name"]))


def save_local(records):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8")


def supabase_request(path, method="GET", payload=None):
    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError("SUPABASE_SERVICE_ROLE_KEY is required.")
    data = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        f"{SUPABASE_URL}/rest/v1/{path}",
        data=data,
        method=method,
        headers={
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "return=representation",
        },
    )
    with urlopen(request, timeout=30) as response:
        body = response.read().decode("utf-8", errors="replace")
    return json.loads(body) if body else None


def sync_supabase(records):
    existing = supabase_request("teachers?select=id,name,college")
    existing_ids = {item["id"] for item in existing}
    existing_people = {(item.get("name"), item.get("college")) for item in existing}
    to_insert = [
        {
            "id": item["id"],
            "name": item["name"],
            "college": item["college"],
            "title": item["title"],
            "email": item["email"],
            "research": item["research"],
            "intro": item["intro"],
        }
        for item in records
        if item["id"] not in existing_ids and (item["name"], item["college"]) not in existing_people
    ]
    for start in range(0, len(to_insert), 100):
        supabase_request("teachers", method="POST", payload=to_insert[start:start + 100])
    if to_insert:
        supabase_request("system_logs", method="POST", payload={
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": f"Imported {len(to_insert)} teachers from selected Tsinghua college websites.",
        })
    return len(to_insert), len(existing_ids)


def main():
    records = scrape_all()
    save_local(records)
    inserted, existing_count = sync_supabase(records)
    print(f"Saved local data to {OUTPUT_PATH}")
    print(f"Total scraped records: {len(records)}")
    print(f"Supabase existing teachers before sync: {existing_count}")
    print(f"Inserted new teachers: {inserted}")


if __name__ == "__main__":
    main()
