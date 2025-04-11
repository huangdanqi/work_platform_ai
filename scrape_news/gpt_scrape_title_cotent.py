import requests
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os
import openai

# Setup OpenAI API key (replace with your own OpenAI API key)
openai.api_key = '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'

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
                "rewrite": "",  # Add a "rewrite" field to store the rewritten content
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

            # Function to rewrite content using ChatGPT
            # Function to rewrite content using ChatGPT (corrected endpoint)
            def rewrite_content_with_filter(content: str, model="gpt-4"):
                prompt = (
                    "You are a helpful assistant rewriting newsletter summaries.\n\n"
                    "Filter out any image markdown like `![Samsung and Google Partnership](Image source: Samsung)` or similar.\n"
                    "Also, replace the phrase 'The Rundown:' with a more professional and interesting phrase like 'In Summary:' or 'Final Thoughts:'.\n\n"
                    "Keep the tone professor-like but interesting, and stay within ~150 words.\n\n"
                    f"Original content:\n{content}\n\n"
                    "Rewritten content:"
                )

                response = openai.ChatCompletion.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": "You are a professor rewriting newsletter topics professionally."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300
                )

                return response["choices"][0]["message"]["content"].strip()

            # Rewriting content with ChatGPT
            rewritten_content = rewrite_content_with_filter(topic["content"])
            topic["rewrite"] = rewritten_content  # Adding rewritten content to the "rewrite" field

            # Filter out incomplete entries
            if topic["title"] and topic["link"]:
                topics.append(topic)

# Save only if topics were found
if topics:
    json_file = f"output_json/topics_{pub_date.replace(',', '').replace(' ', '_')}_rewritten.json"
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(topics, f, ensure_ascii=False, indent=2)
    print(f"✅ Saved {len(topics)} rewritten topics from the latest day to {json_file}")
else:
    print("⚠️ No valid topics found.")
