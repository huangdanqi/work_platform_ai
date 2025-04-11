import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os

# Fetch RSS feed
url = "https://rss.beehiiv.com/feeds/2R3C6Bt5wj.xml"
response = requests.get(url)
root = ET.fromstring(response.content)

# Namespace map
ns = {
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'atom': 'http://www.w3.org/2005/Atom'
}

# Create output directory
os.makedirs("output_json", exist_ok=True)

# Get the latest <item> (the first one in the feed is typically the latest)
latest_item = root.find('./channel/item')
topics = []

if latest_item is not None:
    content_encoded = latest_item.find('content:encoded', ns)
    if content_encoded is not None:
        soup = BeautifulSoup(content_encoded.text, 'html.parser')
        topic_divs = soup.find_all("div", style=lambda v: v and "border-style:solid" in v)

        # Use latest item's pubDate as the date
        pub_date_raw = latest_item.find('pubDate')
        pub_date = pub_date_raw.text.strip()[:16] if pub_date_raw is not None else datetime.now().strftime("%Y-%m-%d")

        for div in topic_divs:
            topic = {
                "title": "",
                "link": "",
                "imageUrl": "",
                "content": "",
                "date": pub_date
            }

            # Title and link
            h4 = div.find("h4")
            if h4:
                topic["title"] = h4.get_text(strip=True)
                a_tag = h4.find("a")
                if a_tag and a_tag.get("href"):
                    topic["link"] = a_tag["href"]

            # Image
            img = div.find("img")
            if img:
                topic["imageUrl"] = img.get("src", "")

            # Remove title and image tags from div and get text
            for tag in div.find_all(["h4", "img"]):
                tag.decompose()

            plain_text = div.get_text(separator="\n", strip=True)
            topic["content"] = plain_text

            # Filter out incomplete entries
            if topic["title"] and topic["link"]:
                topics.append(topic)

# Save only if topics were found
if topics:
    json_file = f"output_json/topics_{pub_date.replace(',', '').replace(' ', '_')}.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(topics)} topics from the latest day to {json_file}")
else:
    print("⚠️ No valid topics found.")
