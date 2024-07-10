import pandas as pd
import json

def generate_dataset(json_file, output_csv, num_samples=5000):
    with open(json_file, 'r', encoding='utf-8') as file:
        phrases = json.load(file)["phrases"]

    data = []
    for intent, texts in phrases.items():
        for text in texts:
            if text.startswith("en:"):
                data.append((text[3:], intent, "en"))
            elif text.startswith("es:"):
                data.append((text[3:], intent, "es"))
            elif text.startswith("fr:"):
                data.append((text[3:], intent, "fr"))
            elif text.startswith("de:"):
                data.append((text[3:], intent, "de"))
            elif text.startswith("ru:"):
                data.append((text[3:], intent, "ru"))
            else:
                data.append((text, intent, "unknown"))

    df = pd.DataFrame(data, columns=["text", "intent", "language"])

    if len(df) < num_samples:
        multiplier = (num_samples // len(df)) + 1
        df = pd.concat([df] * multiplier, ignore_index=True)
    
    df = df.sample(n=num_samples).reset_index(drop=True)
    df.to_csv(output_csv, index=False)

if __name__ == "__main__":
    json_file = r"./Resources/_dataset.assets/updated_phrase.json"
    output_csv = "./Resources/_dataset/dataset.csv"
    generate_dataset(json_file, output_csv, num_samples=5000)
