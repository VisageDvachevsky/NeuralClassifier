import json
from googletrans import Translator, LANGUAGES
import langid
import re
import time
import random
from collections import Counter
from tqdm import tqdm

translator = Translator()

def retry_with_exponential_backoff(func, max_retries=5, initial_delay=1, backoff_factor=2, jitter=0.1):
    def wrapper(*args, **kwargs):
        delay = initial_delay
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    time.sleep(delay + random.uniform(0, jitter))
                    delay *= backoff_factor
                else:
                    print("Max retries reached. Skipping this request.")
                    return None
    return wrapper

@retry_with_exponential_backoff
def detect_with_googletrans(text):
    translated = translator.detect(text)
    return translated.lang

def detect_languages(text):
    predictions = []

    # langid
    try:
        langid_code, _ = langid.classify(text)
        predictions.append(langid_code)
    except Exception as e:
        print(f"langid failed: {e}")

    # Google Translator
    googletrans_code = detect_with_googletrans(text)
    if googletrans_code:
        predictions.append(googletrans_code)

    return predictions

def predict_language(text):
    # Handle pure numbers or random character sets as 'unknown'
    if text.isdigit() or re.match(r'^[a-zA-Z0-9]+$', text):
        return 'unknown'

    # Detect languages
    predictions = detect_languages(text)

    # Aggregate predictions
    if predictions:
        common_prediction = Counter(predictions).most_common(1)[0][0]
        lang_map = {
            'en': 'en',
            'es': 'es',
            'fr': 'fr',
            'de': 'de',
            'ru': 'ru'
        }
        return lang_map.get(common_prediction, 'unknown')
    else:
        return 'unknown'

def add_language_prefix(json_file, output_file):
    print(f"Loading phrases from {json_file}")
    with open(json_file, 'r', encoding='utf-8') as file:
        phrases = json.load(file)["phrases"]

    updated_phrases = {}

    print("Processing intents and texts")
    for intent, texts in tqdm(phrases.items(), desc="Intents"):
        updated_texts = []
        for text in tqdm(texts, desc=f"Texts for intent '{intent}'", leave=False):
            language = predict_language(text)
            prefix = f"{language}:"
            updated_texts.append(f"{prefix}{text}")

        updated_phrases[intent] = updated_texts

    print(f"Writing updated phrases to {output_file}")
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump({"phrases": updated_phrases}, file, ensure_ascii=False, indent=4)
    print("Update complete")

if __name__ == "__main__":
    input_json = "./Resources/_dataset.assets/phrase.json"
    output_json = "./Resources/_dataset.assets/updated_phrase.json"
    add_language_prefix(input_json, output_json)
