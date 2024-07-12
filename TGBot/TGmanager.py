# TGmanager.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from safetensors.torch import load_file as load_safetensors
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import os
from Preprocessing.data_preprocessing import DataPreprocessor
from NeuralNetwork.model import IntentRecognizer
from ResponseGen.response_generation import ResponseGenerator
from DB.database import fetch_feedback, save_rating, create_database

class BotAssistantManager:
    def __init__(self, model_dir="../model"):
        self.model_dir = model_dir
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)

        create_database()
        
        self.load_model(model_dir)
        self.model.to(self.device)
        self.model.eval()

        self.data_preprocessor = DataPreprocessor()
        feedback_data = fetch_feedback()
        self.train_encodings, self.val_encodings, self.train_labels, self.val_labels, self.label_to_id = self.data_preprocessor.prepare_data(feedback_data=feedback_data)

        self.intent_recognizer = IntentRecognizer(num_labels=len(self.label_to_id))
        self.response_generator = ResponseGenerator(intent_labels={v: k for k, v in self.label_to_id.items()})

    def load_model(self, checkpoint_path):
        model_safetensors_path = os.path.join(checkpoint_path, 'model.safetensors')
        if not os.path.exists(model_safetensors_path):
            raise FileNotFoundError(f"The specified model file '{model_safetensors_path}' does not exist.")

        state_dict = load_safetensors(model_safetensors_path, device='cpu')
        self.model.load_state_dict(state_dict, strict=False)  

    def process_input(self, user_input):
        inputs = self.tokenizer(user_input, return_tensors='pt', truncation=True, padding=True).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits
        confidence, predicted_class = torch.max(logits, dim=1)
        confidence = torch.softmax(logits, dim=1)[0][predicted_class].item()
        intent_id = predicted_class.item()
        response = self.response_generator.handle_intent(intent_id, confidence)
        intent_label = self.response_generator.intent_labels[intent_id] if intent_id is not None else "unknown"
        return response, confidence, intent_label, intent_id, inputs

    def save_user_feedback(self, user_input, response, rating, intent, expected_intent, confidence):
        save_rating(user_input, response, int(rating), intent, expected_intent, confidence)
