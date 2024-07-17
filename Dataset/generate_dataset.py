import pandas as pd
import json
import random
import string

def generate_random_noise():
    noise_types = [
        random_lorem_ipsum,
        random_gibberish,
        random_common_phrases,
        # random_special_characters,
        random_numbers
    ]
    return random.choice(noise_types)()

def random_lorem_ipsum():
    lorem_ipsum_texts = [
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit.",
        "Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.",
        "Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat.",
        "Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur.",
        "Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum."
    ]
    return random.choice(lorem_ipsum_texts)

def random_gibberish():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(20, 100)))

def random_common_phrases():
    common_phrases = [
        "The quick brown fox jumps over the lazy dog.",
        "How much wood would a woodchuck chuck if a woodchuck could chuck wood?",
        "She sells seashells by the seashore.",
        "To be or not to be, that is the question.",
        "All work and no play makes Jack a dull boy."
    ]
    return random.choice(common_phrases)

def random_special_characters():
    special_chars = ''.join(random.choices(string.punctuation + string.whitespace, k=random.randint(20, 100)))
    return special_chars.strip()

def random_numbers():
    return ''.join(random.choices(string.digits, k=random.randint(5, 20)))

def generate_dataset(json_file, output_csv, num_samples=5000, noise_fraction=0.1):
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

    intent_counts = df['intent'].value_counts()
    max_count = intent_counts.max()
    
    balanced_data = []
    for intent in intent_counts.index:
        intent_df = df[df['intent'] == intent]
        if len(intent_df) < max_count:
            intent_df = pd.concat([intent_df] * (max_count // len(intent_df)) + [intent_df.sample(max_count % len(intent_df))], ignore_index=True)
        balanced_data.append(intent_df)

    df = pd.concat(balanced_data).sample(frac=1).reset_index(drop=True)

    noise_samples = []
    noise_intents = ["No Intent"] * int(num_samples * noise_fraction)
    for _ in noise_intents:
        noise_text = generate_random_noise()
        noise_samples.append((noise_text, "No Intent", "unknown"))

    noise_df = pd.DataFrame(noise_samples, columns=["text", "intent", "language"])
    df = pd.concat([df, noise_df]).sample(frac=1).reset_index(drop=True)

    if len(df) < num_samples:
        multiplier = (num_samples // len(df)) + 1
        df = pd.concat([df] * multiplier, ignore_index=True)
    
    df = df.sample(n=num_samples).reset_index(drop=True)
    df.to_csv(output_csv, index=False)

if __name__ == "__main__":
    json_file = r"./Resources/_dataset.assets/updated_phrase.json"
    output_csv = "./Resources/_dataset/dataset.csv"
    generate_dataset(json_file, output_csv, num_samples=5000)
