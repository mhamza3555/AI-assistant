# === Simplified Local AI Chatbot (Wikipedia + Web Search + Local NLP) ===
# Dependencies:
# pip install wikipedia beautifulsoup4 requests nltk sumy

import wikipedia
import requests
from bs4 import BeautifulSoup
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import wordnet

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lex_rank import LexRankSummarizer

# Download NLTK data
nltk.download('punkt')
nltk.download('wordnet')

# Wikipedia Search
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

# Web Search using DuckDuckGo
def search_web(query, max_results=3):
    try:
        params = {"q": query}
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get("https://html.duckduckgo.com/html/", params=params, headers=headers, timeout=10)
        soup = BeautifulSoup(res.text, "html.parser")

        results = soup.find_all("div", class_="result__body", limit=max_results)
        snippets = []
        for r in results:
            snippet = r.find("a", class_="result__snippet")
            title = r.find("a", class_="result__a")
            if snippet and snippet.text.strip():
                snippets.append(f"(From Web) {snippet.text.strip()}")
            elif title and title.text.strip():
                snippets.append(f"(From Web) {title.text.strip()}")
        return snippets if snippets else None
    except Exception as e:
        return [f"Web search error: {e}"]

# Local Rewording
def reword(text):
    try:
        sentences = sent_tokenize(text)
        rewritten = []
        for sent in sentences:
            words = sent.split()
            new_words = []
            for word in words:
                syns = wordnet.synsets(word)
                if syns:
                    synonym = syns[0].lemmas()[0].name().replace('_', ' ')
                    new_words.append(synonym if synonym.lower() != word.lower() else word)
                else:
                    new_words.append(word)
            rewritten.append(" ".join(new_words))
        return " ".join(rewritten)
    except Exception as e:
        return f"Rewording error: {e}"

# Summary (Extractive Bullet Points) with fallback

def summarize_bullets(text, n_sentences=3):
    try:
        parser = PlaintextParser.from_string(text, Tokenizer("english"))
        summarizer = LexRankSummarizer()
        summary = summarizer(parser.document, n_sentences)
        return "\n".join(f"- {str(sentence)}" for sentence in summary)
    except LookupError:
        # Fallback: simple first sentences
        sents = sent_tokenize(text)
        return "\n".join(f"- {sents[i]}" for i in range(min(n_sentences, len(sents))))

# Explanation (longer extractive summary)
def explain_text(text):
    return summarize_bullets(text, n_sentences=5)

# Main Chatbot Loop
def main():
    print("=== Smart AI Chatbot (Local NLP + Wikipedia + Web) ===")
    print("Type 'exit' or 'quit' to stop.")
    last_response = ""

    while True:
        user_input = input("\nYou: ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit"]:
            print("Assistant: Goodbye!")
            break

        cmd = user_input.lower()
        if any(kw in cmd for kw in ["reword"]):
            if last_response:
                response = reword(last_response)
                print("Assistant (Reworded):", response)
                last_response = response
                continue
        if any(kw in cmd for kw in ["explain", "expand", "elaborate"]):
            if last_response:
                response = explain_text(last_response)
                print("Assistant (Explained):", response)
                last_response = response
                continue

        # Regular queries
        wiki_result = search_wikipedia(user_input)
        if wiki_result:
            print("Assistant:", wiki_result)
            last_response = wiki_result
            continue

        web_results = search_web(user_input)
        if web_results:
            for idx, result in enumerate(web_results, 1):
                print(f"Assistant (Web {idx}): {result}")
            last_response = web_results[0]
            continue

        print("Assistant: Sorry, I couldn't find an answer.")
        last_response = ""

if __name__ == "__main__":
    main()
