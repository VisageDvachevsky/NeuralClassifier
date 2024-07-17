import sqlite3
import pandas as pd
from Preprocessing.data_preprocessing import DataPreprocessor
from NeuralNetwork.model import IntentRecognizer, IntentDataset
from torch.utils.data import DataLoader
from DB.database import *
from ResponseGen.response_generation import ResponseGenerator

class AssistantManager:
    def __init__(self, dataset="./Dataset/Resources/_dataset/dataset.csv"):
        self.dataset = dataset
        self.data_preprocessor = DataPreprocessor()
        feedback_data = fetch_feedback()
        self.train_encodings, self.val_encodings, self.train_labels, self.val_labels, self.label_to_id = self.data_preprocessor.prepare_data(feedback_data=feedback_data, file_path=self.dataset)
        
        self.intent_recognizer = IntentRecognizer(num_labels=len(self.label_to_id))
        self.response_generator = ResponseGenerator(intent_labels={v: k for k, v in self.label_to_id.items()})

    def train_model(self, dataset=None, resume_from_checkpoint=None):
        if dataset:
            self.dataset = dataset

        feedback_data = fetch_feedback()
        train_encodings, val_encodings, train_labels, val_labels, label_to_id = self.data_preprocessor.prepare_data(feedback_data=feedback_data, file_path=self.dataset)
        
        train_dataset = IntentDataset(train_encodings, train_labels)
        val_dataset = IntentDataset(val_encodings, val_labels)

        train_loader = DataLoader(train_dataset, batch_size=8, shuffle=True, num_workers=4)
        val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, num_workers=4)

        self.intent_recognizer.train(train_dataset, val_dataset, resume_from_checkpoint=resume_from_checkpoint)

    def load_and_retrain(self, checkpoint_path, new_dataset):
        self.intent_recognizer.load_model(checkpoint_path, tokenizer_name='xlm-roberta-base')
        train_encodings, val_encodings, train_labels, val_labels, label_to_id = self.data_preprocessor.prepare_data(file_path=new_dataset)
        train_dataset = IntentDataset(train_encodings, train_labels)
        val_dataset = IntentDataset(val_encodings, val_labels)
        self.intent_recognizer.train(train_dataset, val_dataset, resume_from_checkpoint=None)
        self.evaluate_model(val_dataset)

        self.intent_recognizer.train(train_dataset, val_dataset, resume_from_checkpoint=None)

    def sample_and_save_data(self, sample_size=0.5, db_path='./DB/responses.db', original_file_path='./Dataset/Resources/_dataset/dataset.csv', output_file_path='./Dataset/Resources/_dataset/new_dataset.csv'):
        sample_df = self.data_preprocessor.sample_data(file_path=original_file_path, sample_size=sample_size)
        conn = sqlite3.connect(db_path)
        all_data_df = pd.read_sql_query("SELECT user_input AS text, expected_intent AS intent FROM responses", conn)
        conn.close()
        combined_df = pd.concat([sample_df, all_data_df], ignore_index=True)
        combined_df.to_csv(output_file_path, index=False)
        print(f"Sampled data saved successfully to {output_file_path}!")
        self.check_data_distribution(combined_df, "Combined Dataset")


    def process_input(self, user_input):
        intent_id, confidence = self.intent_recognizer.recognize_intent(user_input)
        response = self.response_generator.handle_intent(intent_id, confidence)
        intent_label = self.response_generator.intent_labels[intent_id] if intent_id is not None else "unknown"
        return response, confidence, intent_label

    def evaluate_model(self):
        _, val_encodings, _, val_labels, _ = self.data_preprocessor.prepare_data()
        val_dataset = IntentDataset(val_encodings, val_labels)
        val_loader = DataLoader(val_dataset, batch_size=8, shuffle=False, num_workers=4)
        evaluation_results = self.intent_recognizer.evaluate(val_dataset)
        return evaluation_results

    def fetch_misclassified_examples(self, db_path='./DB/responses.db'):
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute('''
            SELECT user_input, expected_intent
            FROM responses
            WHERE intent != expected_intent OR confidence < 0.5
        ''')
        examples = c.fetchall()
        conn.close()
        return examples

    def update_training_data(self, misclassified_examples, label_to_id, tokenizer):
        texts = [example[0] for example in misclassified_examples]
        labels = [label_to_id[example[1]] for example in misclassified_examples]

        encodings = tokenizer(texts, truncation=True, padding=True)
        return encodings, labels

    def check_data_distribution(self, df, title):
        print(f"Data distribution for {title}:")
        print(df['intent'].value_counts(normalize=True))
        print()