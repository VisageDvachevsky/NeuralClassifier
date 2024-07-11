# TGBot/TGmanager.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from ResponseGen.response_generation import ResponseGenerator

class BotAssistantManager:
    def __init__(self, model_dir="../model"):
        self.model_dir = model_dir
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.tokenizer = AutoTokenizer.from_pretrained(model_dir)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_dir)
        self.model.to(self.device)
        self.intent_labels = self.model.config.id2label
        self.response_generator = ResponseGenerator(self.intent_labels)

    def process_input(self, user_input):
        inputs = self.tokenizer(user_input, return_tensors='pt', truncation=True, padding=True).to(self.device)
        with torch.no_grad():
            outputs = self.model(**inputs)
        logits = outputs.logits
        confidence, predicted_class = torch.max(logits, dim=1)
        confidence = torch.softmax(logits, dim=1)[0][predicted_class].item()
        intent_id = predicted_class.item()
        response = self.response_generator.handle_intent(intent_id, confidence)
        intent_label = self.intent_labels[intent_id]
        return response, confidence, intent_label
