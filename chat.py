import re
import csv
import requests
from bs4 import BeautifulSoup
import wikipedia
import datetime
import pytz

# --- Load synonyms for simplification ---
synonym_dict = {}
try:
    with open('synonyms.csv', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw = row['difficult'].strip().lower()
            key = re.sub(r'\d+$', '', raw)
            easy = row.get('easy', row.get('simple', '')).strip()
            if key and easy:
                synonym_dict[key] = easy
except FileNotFoundError:
    print("Warning: 'synonyms.csv' not found. Simplify disabled.")
except Exception as e:
    print(f"Error loading synonyms.csv: {e}")

# --- Helper Functions ---
def simplify_text(text):
    def replace(match):
        word = match.group(0)
        key = word.lower()
        simple = synonym_dict.get(key)
        if not simple:
            return word
        if word[0].isupper(): simple = simple.capitalize()
        return simple
    return re.sub(r"\b\w+\b", replace, text)

def search_wikipedia(query, sentences=2):
    try:
        return wikipedia.summary(query, sentences=sentences)
    except (wikipedia.exceptions.DisambiguationError, wikipedia.exceptions.PageError):
        return None
    except Exception:
        return None

def search_web(query):
    try:
        res = requests.get(
            "https://html.duckduckgo.com/html/",
            params={"q": query},
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        snippet = soup.find('a', class_='result__snippet')
        if snippet and snippet.text.strip(): return snippet.text.strip()
        title = soup.find('a', class_='result__a')
        if title and title.text.strip(): return title.text.strip()
        return None
    except:
        return None

def get_time(city='UTC'):
    # Attempt dynamic timezone lookup using pytz
    city_key = city.strip().replace(' ', '_').title()
    tz_name = None
    # Exact match search
    for tz in pytz.all_timezones:
        if tz.endswith('/' + city_key):
            tz_name = tz
            break
    # Contains match search
    if not tz_name:
        for tz in pytz.all_timezones:
            if '/' + city_key + '/' in tz or tz.endswith('/' + city_key):
                tz_name = tz
                break
    # Default to UTC if not found
    if not tz_name:
        tz_name = 'UTC'
    try:
        tz = pytz.timezone(tz_name)
        now = datetime.datetime.now(tz)
        return now.strftime('%Y-%m-%d %H:%M:%S %Z')
    except Exception:
        return None

# use get_weather as before

def get_weather(city='Pakistan'):
    try:
        resp = requests.get(f'https://wttr.in/{city}?format=3&lang=en')
        return resp.text.strip()
    except:
        return None

# --- Goal-Based Agent Components ---
GOALS = {
    'weather':      r"\bweather\b.*\bin\b\s*(?P<city>\w+)",
    'time':         r"\btime\b.*\bin\b\s*(?P<city>\w+)",
    'definition':   r"\bdefine\b.*(?P<topic>.+)",
    'simplify':     r"\b(simplify|make it easier|easy version)\b" ,
    'search':       r".+"
}

def interpret_goal(text):
    for goal, pattern in GOALS.items():
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            return goal, m.groupdict()
    return 'search', {'query': text}

def plan(goal, params):
    if goal == 'weather': return [('get_weather', params.get('city'))]
    if goal == 'time':    return [('get_time', params.get('city'))]
    if goal == 'definition': return [('wiki', params.get('topic'))]
    if goal == 'simplify': return [('simplify', None)]
    return [('wiki', params.get('query')), ('web', params.get('query'))]

def execute(plan_steps, last_response):
    for action, arg in plan_steps:
        if action == 'get_time':
            result = get_time(arg or 'UTC')
        elif action == 'get_weather':
            result = get_weather(arg or 'Pakistan')
        elif action == 'wiki':
            wiki = search_wikipedia(arg)
            if wiki:
                result = wiki
            else:
                continue
        elif action == 'web':
            web = search_web(arg)
            if web:
                result = web
            else:
                continue
        elif action == 'simplify':
            result = simplify_text(last_response)
        else:
            result = None
        if result:
            return result
    return "Sorry, I couldn't fulfill that request."

# --- Main Loop ---
def main():
    print('=== Goal-Based AI Chatbot ===')
    print('Commands:')
    print('  define <topic>         → get definition')
    print('  weather in <city>      → get weather')
    print('  time in <city>         → get current time')
    print('  simplify               → simplify last answer')
    print('  exit                   → quit')

    last_response = ''
    while True:
        user_input = input('\nYou: ').strip()
        if not user_input: continue
        if user_input.lower() in ('exit','quit'):
            print('Assistant: Goodbye!')
            break

        goal, params = interpret_goal(user_input)
        steps = plan(goal, params)
        answer = execute(steps, last_response)
        print('Assistant:', answer)
        last_response = answer

if __name__ == '__main__':
    main()
