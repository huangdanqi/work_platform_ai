import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import openai

# 🔐 Set your OpenAI key
openai.api_key = "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"

# 🎓 Rewrite content with markdown and emojis
def rewrite_content(content):
    prompt = (
        f"Rewrite the following newsletter summary to sound like a professor with a professional but engaging tone. "
        f"Limit it to 150 words. Use markdown format and add emojis to make it visually engaging.\n\n"
        f"{content}"
    )
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response['choices'][0]['message']['content'].strip()

# 🌏 Translate to Chinese in fluent markdown
def translate_to_chinese(content):
    prompt = f"请将以下英文内容翻译成简体中文，保留 emoji，使用专业、有趣的语气，输出为 Markdown 格式：\n\n{content}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response['choices'][0]['message']['content'].strip()

# 🏷 Translate title to Chinese
def translate_title_to_chinese(title):
    prompt = f"请将以下英文标题翻译成简体中文：\n\n{title}"
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7
    )
    return response['choices'][0]['message']['content'].strip()

# 🖼️ Get new image by scraping the first image from the linked page
def get_first_image_from_link(link):
    try:
        res = requests.get(link, timeout=10)
        soup = BeautifulSoup(res.content, "html.parser")
        img = soup.find("img")
        return img["src"] if img and "src" in img.attrs else ""
    except:
        return ""

# 📰 Fetch RSS and process topics
url = "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml"
response = requests.get(url)
root = ET.fromstring(response.content)

ns = {'content': 'http://purl.org/rss/1.0/modules/content/'}
os.makedirs("output_json", exist_ok=True)

latest_item = root.find('./channel/item')
topics = []

if latest_item is not None:
    content_encoded = latest_item.find('content:encoded', ns)
    if content_encoded is not None:
        soup = BeautifulSoup(content_encoded.text, 'html.parser')
        topic_divs = soup.find_all("div", style=lambda v: v and "border-style:solid" in v)

        pub_date_raw = latest_item.find('pubDate')
        pub_date = pub_date_raw.text.strip()[:16] if pub_date_raw is not None else datetime.now().strftime("%Y-%m-%d")

        for div in topic_divs:
            topic = {
                "title": "",
                "title_cn": "",
                "link": "",
                "imageUrl": "",
                "content": "",
                "rewrite": "",
                "chinese": "",
                "new_image": "",
                "date": pub_date
            }

            h4 = div.find("h4")
            if h4:
                topic["title"] = h4.get_text(strip=True)
                a_tag = h4.find("a")
                if a_tag and a_tag.get("href"):
                    topic["link"] = a_tag["href"]

            img = div.find("img")
            if img:
                topic["imageUrl"] = img.get("src", "")

            for tag in div.find_all(["h4", "img"]):
                tag.decompose()

            plain_text = div.get_text(separator="\n", strip=True)
            topic["content"] = plain_text

            if topic["title"] and topic["link"]:
                try:
                    topic["rewrite"] = rewrite_content(plain_text)
                    topic["chinese"] = translate_to_chinese(topic["rewrite"])
                    topic["title_cn"] = translate_title_to_chinese(topic["title"])
                    topic["new_image"] = get_first_image_from_link(topic["link"])
                    topics.append(topic)
                except Exception as e:
                    print(f"❌ Error processing topic '{topic['title']}': {e}")

# 💾 Save JSON with markdown
if topics:
    filename = f"output_json/topics_{pub_date.replace(',', '').replace(' ', '_')}_rewritten.json"
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(topics)} rewritten and translated topics to {filename}")
else:
    print("⚠️ No valid topics found.")
