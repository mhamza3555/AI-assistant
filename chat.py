import re
import csv
import requests
from bs4 import BeautifulSoup
import wikipedia
import datetime
import pytz

# === Load synonyms for simplification ===
synonym_dict = {}
try:
    with open('synonyms.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row['difficult'].strip().lower()
            key = re.sub(r'\d+$', '', raw)            # strip any trailing digits
            easy = row.get('easy', row.get('simple', '')).strip()
            if key and easy:
                synonym_dict[key] = easy
except FileNotFoundError:
    print("Warning: 'synonyms.csv' not found. Simplify disabled.")
except Exception as e:
    print(f"Error loading synonyms.csv: {e}")

# === Helper Functions ===
def simplify_text(text):
    def replace(m):
        w = m.group(0)
        k = w.lower()
        s = synonym_dict.get(k)
        if not s:
            return w
        return s.capitalize() if w[0].isupper() else s
    return re.sub(r"\b\w+\b", replace, text)

def search_wikipedia(query, sentences=2):
    try:
        return wikipedia.summary(query, sentences=sentences)
    except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
        return None
    except:
        return None

def search_web(query):
    try:
        r = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        snip = soup.find('a', class_='result__snippet')
        if snip and snip.text.strip():
            return snip.text.strip()
        title = soup.find('a', class_='result__a')
        if title and title.text.strip():
            return title.text.strip()
    except:
        pass
    return None

def get_time(city='UTC'):
    city_key = city.strip().replace(' ', '_').title()
    tz_name = None
    for tz in pytz.all_timezones:
        if tz.endswith('/' + city_key):
            tz_name = tz
            break
    if not tz_name:
        for tz in pytz.all_timezones:
            if '/' + city_key + '/' in tz:
                tz_name = tz
                break
    if not tz_name:
        tz_name = 'UTC'
    try:
        now = datetime.datetime.now(pytz.timezone(tz_name))
        return now.strftime('%Y-%m-%d %H:%M:%S %Z')
    except:
        return None

def get_weather(city='Pakistan'):
    try:
        resp = requests.get(f'https://wttr.in/{city}?format=3&lang=en')
        return resp.text.strip()
    except:
        return None

# === Goal-Based Agent ===
GOALS = {
    'weather':    r"\bweather\b.*\bin\b\s*(?P<city>[\w\s]+)",
    'time':       r"\btime\b.*\bin\b\s*(?P<city>[\w\s]+)",
    'define':     r"\b(?:define|definition)\b.*\bof\b\s*(?P<topic>.+)",
    'simplify':   r"\b(?:simplify|make it easier|easy version)\b",
    'search':     r".+"
}

def interpret_goal(text):
    for goal, pat in GOALS.items():
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return goal, m.groupdict()
    return 'search', {'query': text}

def plan(goal, params):
    if goal == 'weather':
        return [('weather', params.get('city'))]
    if goal == 'time':
        return [('time', params.get('city'))]
    if goal in ('define',):
        return [('wiki', params.get('topic'))]
    if goal == 'simplify':
        return [('simplify', None)]
    return [('wiki', params.get('query')), ('web', params.get('query'))]

def execute(steps, last_resp):
    for action, arg in steps:
        if action == 'weather':
            res = get_weather(arg or 'Pakistan')
        elif action == 'time':
            res = get_time(arg or 'UTC')
        elif action == 'wiki':
            res = search_wikipedia(arg)
        elif action == 'web':
            res = search_web(arg)
        elif action == 'simplify':
            res = simplify_text(last_resp)
        else:
            res = None

        if res:
            return res
    return "Sorry, I couldn't fulfill that request."

# === Main Loop ===
def main():
    print("=== Goal‑Based AI Chatbot ===")
    print("Commands:")
    print("  define <topic>")
    print("  weather in <city>")
    print("  time in <city>")
    print("  simplify        (replaces hard words in last reply)")
    print("  exit")
    last = ""

    while True:
        user = input("\nYou: ").strip()
        if not user:
            continue
        if user.lower() in ('exit', 'quit'):
            print("Assistant: Goodbye!")
            break

        goal, params = interpret_goal(user)
        steps = plan(goal, params)
        reply = execute(steps, last)
        print("Assistant:", reply)
        last = reply

if __name__ == '__main__':
    main()
