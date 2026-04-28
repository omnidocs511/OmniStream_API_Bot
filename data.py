import requests
from bs4 import BeautifulSoup
import re

def get_movie_qualities(movie_url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    try:
        response = requests.get(movie_url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        qualities = []

        # Target the specific content area
        main_content = soup.find('div', class_='entry-content') or soup.find('article')
        if not main_content:
            return []

        current_res = ""
        current_section = "Movie"

        # Find all tags that could contain headers or links
        for element in main_content.find_all(['h1', 'h2', 'h3', 'h4', 'p', 'a', 'span', 'strong']):
            # Get full text including hidden spans
            text_raw = element.get_text(strip=True)
            text_upper = text_raw.upper()

            if not text_raw: continue

            # 1. Update Section (Series/Episode detection)
            if "SEASON" in text_upper or "EPISODE" in text_upper:
                match_ep = re.search(r'(EPISODE\s+\d+|SEASON\s+\d+)', text_upper)
                if match_ep:
                    current_section = match_ep.group(1).title()
                    current_res = "" # Reset resolution for new episode block

            # 2. Update Resolution (Only if NOT inside a link)
            res_match = re.search(r'(\d{3,4}P|HEVC|10BIT|4K|2160P)', text_upper)
            if res_match and element.name != 'a':
                current_res = res_match.group(1)

            # 3. Extract Links
            if element.name == 'a' and element.has_attr('href'):
                href = element['href']
                
                # Filter out junk links
                if any(x in href.lower() for x in ['telegram', 'how-to', 'wp-admin', 'join']):
                    continue

                # Clean up the link label
                label = text_raw
                # If HDHub has an empty link text but has a span inside, BeautifulSoup handles it,
                # but we should ensure we have the resolution.
                if current_res and current_res not in label.upper():
                    final_label = f"{current_section} [{current_res}] - {label}"
                else:
                    final_label = f"{current_section} - {label}"

                # Final cleaning
                final_label = final_label.replace("–", "").replace("|", "").strip()
                final_label = re.sub(' +', ' ', final_label)

                qualities.append({
                    'quality': final_label,
                    'url': href
                })

        # Remove duplicates
        seen_urls = set()
        unique_list = []
        for q in qualities:
            if q['url'] not in seen_urls:
                unique_list.append(q)
                seen_urls.add(q['url'])

        return unique_list

    except Exception as e:
        print(f"Scraping error: {e}")
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
