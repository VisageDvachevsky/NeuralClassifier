import pandas as pd
from sklearn.model_selection import train_test_split
from transformers import XLMRobertaTokenizer
from langdetect import detect

class DataPreprocessor:
    def __init__(self):
        self.tokenizer = XLMRobertaTokenizer.from_pretrained('xlm-roberta-base')

    def prepare_data(self, file_path='../Dataset/Resources/_dataset/dataset.csv', feedback_data=None):
        if file_path is not None:
            df = pd.read_csv(file_path)
        elif feedback_data is not None:
            df = pd.DataFrame(feedback_data, columns=["text", "intent", "confidence", "rating"])
            df = df[["text", "intent"]]
        else:
            raise ValueError("Either file_path or feedback_data must be provided")

        if feedback_data:
            feedback_df = pd.DataFrame(feedback_data, columns=["text", "intent", "confidence", "rating"])
            feedback_df = feedback_df[["text", "intent"]]
            df = pd.concat([df, feedback_df], ignore_index=True)
        
        df['language'] = df['text'].apply(self.detect_language)
        
        label_to_id = {label: idx for idx, label in enumerate(df['intent'].unique())}
        df['label_id'] = df['intent'].map(label_to_id)

        train_texts, val_texts, train_labels, val_labels = train_test_split(df['text'], df['label_id'], test_size=0.2)

        train_encodings = self.tokenizer(list(train_texts), truncation=True, padding=True)
        val_encodings = self.tokenizer(list(val_texts), truncation=True, padding=True)

        return train_encodings, val_encodings, train_labels, val_labels, label_to_id

    def detect_language(self, text):
        try:
            return detect(text)
        except:
            return 'unknown'

    def sample_data(self, file_path='./Dataset/Resources/_dataset/dataset.csv', sample_size=0.1):
        df = pd.read_csv(file_path)
        sample_df = df.sample(frac=sample_size, random_state=42)
        return sample_df
