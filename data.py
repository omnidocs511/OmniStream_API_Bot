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

        # 1. Locate the main content area (HDHub uses 'page-body' or 'entry-content')
        content_area = soup.find('main', class_='page-body') or soup.find('div', class_='entry-content')
        
        if not content_area:
            return []

        # 2. Extract Title for context
        page_title = soup.find('h1', class_='page-title')
        movie_name = page_title.get_text(strip=True) if page_title else "Movie"

        # 3. Targeted Link Extraction
        # We look for all <a> tags that contain resolution keywords or sizes
        res_pattern = re.compile(r'(\d{3,4}p|4K|2160p|HEVC|10bit|Dual Audio|MB|GB)', re.IGNORECASE)

        for link in content_area.find_all('a', href=True):
            href = link['href']
            
            # Get text from the link AND its children (like <span> or <strong>)
            # This is key for HDHub as the text is often inside <a><span>...</span></a>
            link_text = link.get_text(" ", strip=True) 

            # If the link text is empty, check if it's an image link or social link
            if not link_text or any(x in href.lower() for x in ['telegram', 'discord', 'how-to', 'wp-admin', 'contact']):
                continue

            # Validation: Only keep links that look like download buttons
            if res_pattern.search(link_text) or "WATCH" in link_text.upper():
                
                # Clean up the label
                clean_label = link_text.replace("⚡", "").replace(":-", "").strip()
                
                # If it's a "WATCH" link, give it a better name
                if "WATCH" in clean_label.upper():
                    clean_label = f"✨ Online Player - {clean_label}"

                qualities.append({
                    'quality': clean_label,
                    'url': href
                })

        # 4. Handle Redirection / Final Cleaning
        unique_qualities = []
        seen_urls = set()
        for item in qualities:
            if item['url'] not in seen_urls:
                unique_qualities.append(item)
                seen_urls.add(item['url'])

        return unique_qualities

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
