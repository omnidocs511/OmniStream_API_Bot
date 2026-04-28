import requests
from bs4 import BeautifulSoup
import re

def get_movie_qualities(movie_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(movie_url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        qualities = []

        # Target the content area
        content = soup.find('main', class_='page-body') or soup.find('div', class_='entry-content')
        if not content: return []

        # Context Memory
        curr_episode = ""
        curr_res = ""

        # regex to find resolutions/qualities
        res_regex = r'(\d{3,4}P|4K|2160P|HEVC|10BIT|WEB-DL|BLURAY)'

        # Loop through every tag in order
        for tag in content.find_all(['h3', 'h4', 'p', 'strong', 'a', 'span']):
            text = tag.get_text(" ", strip=True)
            text_up = text.upper()

            # 1. Update Episode Context (e.g., "Episode 1", "Season 1")
            if "EPISODE" in text_up or "SEASON" in text_up:
                ep_match = re.search(r'((?:EPISODE|SEASON)\s+\d+)', text_up)
                if ep_match:
                    curr_episode = ep_match.group(1).title()
                    curr_res = "" # Reset resolution when episode changes

            # 2. Update Resolution Context
            # If the tag is NOT a link and contains a resolution, save it (e.g., "720p -")
            if tag.name != 'a':
                res_match = re.search(res_regex, text_up)
                if res_match:
                    curr_res = res_match.group(1)

            # 3. Process Links
            if tag.name == 'a' and tag.has_attr('href'):
                href = tag['href']
                
                # Skip junk
                if any(x in href.lower() for x in ['telegram', 'discord', 'how-to', 'wp-admin']):
                    continue

                # Get text specifically inside this link
                link_text = text.strip()
                if not link_text: continue

                # Check if this link contains its own resolution (Standard Movie Format)
                own_res = re.search(res_regex, link_text.upper())
                final_res = own_res.group(1) if own_res else curr_res

                # Build a clean label
                label_parts = []
                if curr_episode: label_parts.append(curr_episode)
                if final_res: label_parts.append(f"[{final_res}]")
                
                # If the link text isn't just a repeat of the resolution, add it
                # This keeps "Drive", "Instant", or the file size
                if link_text.upper() != final_res:
                    label_parts.append(link_text)

                quality_string = " - ".join(label_parts)
                
                # Final cleanup of unwanted symbols
                quality_string = quality_string.replace("⚡", "").replace(":-", "").strip()

                qualities.append({
                    'quality': quality_string,
                    'url': href
                })

        # Remove Duplicates
        seen = set()
        unique = []
        for q in qualities:
            if q['url'] not in seen:
                unique.append(q)
                seen.add(q['url'])

        return unique

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
