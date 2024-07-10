import json
from langdetect import detect, DetectorFactory
from langdetect.lang_detect_exception import LangDetectException
DetectorFactory.seed = 0

def add_language_prefix(json_file, output_file):
    with open(json_file, 'r', encoding='utf-8') as file:
        phrases = json.load(file)["phrases"]

    updated_phrases = {}

    for intent, texts in phrases.items():
        updated_texts = []
        for text in texts:
            try:
                language = detect(text)
                if language == "en":
                    prefix = "en:"
                elif language == "ru":
                    prefix = "ru:"
                elif language == "de":
                    prefix = "de:"
                elif language == "fr":
                    prefix = "fr:"
                elif language == "es":
                    prefix = "es:"
                else:
                    prefix = "unknown:"
                updated_texts.append(f"{prefix}{text}")
            except LangDetectException:
                updated_texts.append(f"unknown:{text}")

        updated_phrases[intent] = updated_texts

    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump({"phrases": updated_phrases}, file, ensure_ascii=False, indent=4)

if __name__ == "__main__":
    input_json = "./Resources/_dataset.assets/phrase.json"
    output_json = "./Resources/_dataset.assets/updated_phrase.json"
    add_language_prefix(input_json, output_json)
