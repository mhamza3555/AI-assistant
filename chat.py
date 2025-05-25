'''
Project: Text-based AI Chatbot (Wikipedia + Web Search)
File: web_agent.py

Dependencies:
    pip install wikipedia beautifulsoup4 requests

Run:
    python web_agent.py
'''

import wikipedia
import requests
from bs4 import BeautifulSoup

# Wikipedia search
def search_wikipedia(query):
    try:
        summary = wikipedia.summary(query, sentences=2)
        return f"(From Wikipedia) {summary}"
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Your query was too broad. Try being more specific. Options: {e.options[:5]}..."
    except wikipedia.exceptions.PageError:
        return None
    except Exception as e:
        return f"Wikipedia error: {e}"

# Basic web scraping from DuckDuckGo (no API)
def search_web(query, max_results=3):
    try:
        params = {"q": query}
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://html.duckduckgo.com/html/", params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")
        results = soup.find_all("a", class_="result__a", limit=max_results)
        snippets = []
        for r in results:
            text = r.get_text(strip=True)
            if text:
                snippets.append(f"(From Web) {text}")
        return snippets if snippets else None
    except Exception as e:
        return [f"Web search error: {e}"]

# Main loop: text-based chat
def main():
    print("=== Smart AI Chatbot (Wikipedia + Web Search) ===")
    print("Type 'exit' or 'quit' to stop.")
    while True:
        user_input = input("\nYou: ")
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("Assistant: Goodbye!")
            break

        # First try Wikipedia
        wiki_result = search_wikipedia(user_input)
        if wiki_result:
            print(f"Assistant: {wiki_result}")
            continue

        # Next try Web search
        web_results = search_web(user_input)
        if web_results:
            for result in web_results:
                print(f"Assistant: {result}")
            continue

        print("Assistant: Sorry, I couldn't find an answer.")

if __name__ == "__main__":
    main()
