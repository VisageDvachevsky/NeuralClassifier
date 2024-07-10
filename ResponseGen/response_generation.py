from datetime import datetime

class ResponseGenerator:
    def __init__(self, intent_labels):
        self.intent_labels = intent_labels

    def handle_intent(self, intent_id, confidence, threshold=0.7):
        if intent_id is None:
            return "I'm not sure what you want. Can you please clarify?"

        intent = self.intent_labels[intent_id]
        response = self.generate_response(intent)
        
        if confidence < threshold:
            response += " I'm not very confident in this answer. Could you please rate the response?"

        return response

    def generate_response(self, intent):
        if intent == 'get_time':
            return self.get_current_time()
        elif intent == 'get_date':
            return self.get_current_date()
        elif intent == 'greet':
            return "Hello! How can I assist you today?"
        elif intent == 'goodbye':
            return "Goodbye! Have a great day!"
        else:
            return "I'm not sure what you want. Can you please clarify?"

    def get_current_time(self):
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        return f"The current time is {current_time}"

    def get_current_date(self):
        now = datetime.now()
        current_date = now.strftime("%Y-%m-%d")
        return f"Today's date is {current_date}"

