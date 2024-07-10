from Preprocessing.data_preprocessing import DataPreprocessor
from NeuralNetwork.model import IntentRecognizer
from ResponseGen.response_generation import ResponseGenerator
from DB.database import save_rating, fetch_feedback

class TelegramAssistantManager:
    def __init__(self, model_dir, dataset_path="Dataset/Resources/_dataset/dataset.csv"):
        self.data_preprocessor = DataPreprocessor()
        feedback_data = fetch_feedback()
        _, _, _, _, label_to_id = self.data_preprocessor.prepare_data(feedback_data=feedback_data, file_path=dataset_path)
        self.intent_recognizer = IntentRecognizer(num_labels=len(label_to_id))
        self.intent_recognizer.load_model(model_dir)
        self.response_generator = ResponseGenerator(intent_labels={v: k for k, v in label_to_id.items()})

    def process_input(self, user_input):
        intent_id, confidence = self.intent_recognizer.recognize_intent(user_input)
        response = self.response_generator.handle_intent(intent_id, confidence)
        intent_label = self.response_generator.intent_labels[intent_id] if intent_id is not None else "unknown"
        return response, confidence, intent_label

    def save_interaction(self, user_input, response, rating, intent, expected_intent, confidence):
        save_rating(user_input, response, rating, intent, expected_intent, confidence)
