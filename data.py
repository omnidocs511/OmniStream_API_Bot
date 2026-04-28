import requests
from bs4 import BeautifulSoup
import re

def get_movie_qualities(movie_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "en-US,en;q=0.9"
    }
    
    try:
        response = requests.get(movie_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        qualities = []

        # Target the main content area
        content_area = soup.find('main', class_='page-body') or soup.find('div', class_='entry-content')
        if not content_area:
            return []

        # Context trackers for Series/Episodes
        current_episode = ""
        current_res = ""

        # We iterate through all elements in order to maintain context
        for element in content_area.find_all(['h3', 'h4', 'p', 'hr', 'strong', 'a']):
            text = element.get_text(" ", strip=True)
            text_upper = text.upper()

            # 1. Detect Episode/Season Header
            if "EPISODE" in text_upper or "SEASON" in text_upper:
                # Extract 'Episode 1' from strings like 'EPISODE 1' or 'Episode 01'
                match = re.search(r'(EPISODE\s+\d+|SEASON\s+\d+)', text_upper)
                if match:
                    current_episode = match.group(1).title()
                    current_res = "" # Reset resolution for new episode block

            # 2. Detect Resolution (if it's in a header or strong tag but NOT a link)
            res_match = re.search(r'(\d{3,4}P|4K|2160P|HEVC|10BIT)', text_upper)
            if res_match and element.name != 'a':
                current_res = res_match.group(1)

            # 3. Process Links
            if element.name == 'a' and element.has_attr('href'):
                href = element['href']
                
                # Filter social/junk
                if any(x in href.lower() for x in ['telegram', 'discord', 'how-to', 'wp-admin', 'contact']):
                    continue

                # Detect if the link itself contains the resolution (e.g., '720p x264 [3.3GB]')
                inner_res_match = re.search(r'(\d{3,4}P|4K|2160P|HEVC|10BIT)', text_upper)
                link_res = inner_res_match.group(1) if inner_res_match else current_res
                
                # Build the quality label
                label_parts = []
                if current_episode: label_parts.append(current_episode)
                if link_res: label_parts.append(f"[{link_res}]")
                
                # Add the actual link text (e.g., 'Drive', 'Instant', or the full size string)
                clean_text = text.replace("⚡", "").strip()
                if clean_text:
                    label_parts.append(clean_text)

                final_label = " - ".join(label_parts) if label_parts else clean_text
                
                # Fallback check: if it's a Download button and has no info, use context
                if not final_label or final_label.lower() in ['drive', 'instant', 'watch']:
                   final_label = f"{current_episode} {link_res} {clean_text}".strip()

                qualities.append({
                    'quality': final_label,
                    'url': href
                })

        # Remove duplicates and cleanup
        unique_qualities = []
        seen_urls = set()
        for item in qualities:
            if item['url'] not in seen_urls:
                # Final polish on text
                item['quality'] = re.sub(' +', ' ', item['quality']).replace(" - - ", " - ").strip()
                unique_qualities.append(item)
                seen_urls.add(item['url'])

        return unique_qualities

    except Exception as e:
        print(f"Scraper Error: {e}")
        return []
    
def search_hdhub(query):
    url = "https://search.pingora.fyi/collections/post/documents/search"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Origin": "https://new6.hdhub4u.fo",
        "Referer": "https://new6.hdhub4u.fo/",
        "Accept": "application/json, text/plain, */*",
    }
    params = {'q': query, 'query_by': 'post_title', 'sort_by': 'sort_by_date:desc', 'per_page': 25}

    try:
        response = requests.get(url, params=params, headers=headers, timeout=10)
        if response.status_code != 200: return {"error": f"API Error: {response.status_code}"}
        
        data = response.json()
        results = []
        base_site_url = "https://new6.hdhub4u.fo"

        for hit in data.get('hits', []):
            doc = hit.get('document', {})
            raw_link = doc.get('permalink', '')
            full_link = raw_link if raw_link.startswith('http') else f"{base_site_url}{raw_link}"
            results.append({"title": doc.get('post_title', 'Unknown Title'), "link": full_link})
        return results
    except Exception as e:
        return {"error": str(e)}
