import feedparser
import requests
from flask import Flask, render_template
from datetime import datetime
import re

app = Flask(__name__)

# --- 1. THE FILTER KEYWORDS ---
# A job must contain at least one word from BOTH lists to be shown.

INDUSTRY_KEYWORDS = [
    "pharmacy", "pharmacist", "pharmaceutical", "medical", "medicine", 
    "clinic", "health", "healthcare", "wellness", "doctor", "physician", 
    "patient", "hospital", "therapy", "therapist", "dental", "dentist",
    "psychiatry", "psychiatrist", "mental health", "nutrition", "supplement",
    "biotech", "life sciences", "cme", "hipaa", "medtech"
]

ROLE_KEYWORDS = [
    "web", "website", "design", "designer", "developer", "wordpress", "squarespace", "webflow",
    "writer", "writing", "editor", "editing", "copywriter", "content", "blog", 
    "seo", "marketing", "newsletter", "communications", "freelance", "contract"
]

BANNED_KEYWORDS = [
    "senior software engineer", "full stack", "react native", "java", "c++", 
    "crypto", "blockchain", "game", "gaming", "customer service", "receptionist",
    "nurse practitioner", "driver", "warehouse", "sales associate",
    # Filtering out other freelancers looking for work:
    "resume", "looking for work", "seeking", "i am a"
]

# --- 2. THE FEEDS (High Quality Only) ---
RSS_FEEDS = [
    {
        "source": "ProBlogger",
        "url": "https://problogger.com/jobs/feed/",
        "badge_color": "#2c5282" # Dark Blue
    },
    {
        "source": "WeWorkRemotely (Design)",
        "url": "https://weworkremotely.com/categories/remote-design-jobs.rss",
        "badge_color": "#e34c26" # Red
    },
    {
        "source": "WeWorkRemotely (Marketing)",
        "url": "https://weworkremotely.com/categories/remote-marketing-jobs.rss",
        "badge_color": "#e34c26"
    },
    {
        "source": "RemoteOK (Web/Design)",
        # RemoteOK doesn't split RSS nicely, so we grab the main feed and filter heavily
        "url": "https://remoteok.com/rss", 
        "badge_color": "#ff4757" # Bright Red/Pink
    },
    {
        "source": "Craigslist MN (Gigs - Computer)",
        "url": "https://minneapolis.craigslist.org/search/cpg?format=rss",
        "badge_color": "#800080" # Purple
    },
    {
        "source": "Craigslist MN (Gigs - Writing)",
        "url": "https://minneapolis.craigslist.org/search/wrug?format=rss",
        "badge_color": "#800080"
    }
]

def clean_html(raw_html):
    if not raw_html: return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)

def parse_date(date_string):
    try:
        # Standard RSS
        dt = datetime.strptime(date_string, "%a, %d %b %Y %H:%M:%S %z")
        return dt.strftime("%b %d")
    except:
        # RemoteOK often uses ISO format
        try:
            dt = datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S%z")
            return dt.strftime("%b %d")
        except:
            return ""

def is_niche_match(text):
    """
    Returns (True, matching_keywords) if the job is relevant.
    """
    text = text.lower()
    
    # 1. Check Bans
    for bad_word in BANNED_KEYWORDS:
        if bad_word in text:
            return False, []

    # 2. Check Intersection (Industry AND Role)
    found_industry = [w for w in INDUSTRY_KEYWORDS if w in text]
    found_role = [w for w in ROLE_KEYWORDS if w in text]
    
    if found_industry and found_role:
        return True, found_industry + found_role
    
    return False, []

def get_jobs():
    all_jobs = []
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) ClinicRadar/1.0"}
    
    for feed in RSS_FEEDS:
        print(f"Scanning {feed['source']}...")
        try:
            response = requests.get(feed['url'], headers=headers, timeout=10)
            parsed_feed = feedparser.parse(response.content)
            
            for entry in parsed_feed.entries:
                title = entry.title
                summary = clean_html(entry.get("summary", ""))
                full_text = f"{title} {summary}"
                
                # --- THE FILTER ---
                is_match, keywords = is_niche_match(full_text)
                
                if is_match:
                    job = {
                        "source": feed['source'],
                        "badge_color": feed['badge_color'],
                        "title": title,
                        "link": entry.link,
                        "published": parse_date(entry.get("published", "")),
                        "summary": summary[:300] + "...",
                        "matched_keywords": list(set(keywords))[:4]
                    }
                    all_jobs.append(job)
                    
        except Exception as e:
            print(f"Error reading {feed['source']}: {e}")
            
    return all_jobs

@app.route('/')
def index():
    jobs = get_jobs()
    return render_template('index.html', jobs=jobs, count=len(jobs), last_updated=datetime.now().strftime("%I:%M %p"))

if __name__ == '__main__':
    app.run(debug=True, port=5000)