from manager import AssistantManager
from DB.database import create_database, save_rating
from DB.database_gui import DatabaseManager
import tkinter as tk

def main():
    create_database()

    print("Do you want to start training from scratch, from a checkpoint, or retrain a loaded model with a new dataset?")
    print("1. Start from scratch")
    print("2. Start from checkpoint")
    print("3. Sample and save data for retraining")
    print("4. Load model from checkpoint and retrain with a new dataset")
    choice = input("Enter your choice (1, 2, 3, 4): ")

    if choice == '1':
        dataset = input("Enter the dataset path: ")
        assistant = AssistantManager(dataset=dataset)
        assistant.train_model(dataset=dataset)
    elif choice == '2':
        checkpoint_path = input("Enter the checkpoint path: ")
        assistant = AssistantManager()
        assistant.train_model(resume_from_checkpoint=checkpoint_path)
    elif choice == '3':
        assistant = AssistantManager()
        assistant.sample_and_save_data()
    elif choice == '4':
        checkpoint_path = input("Enter the checkpoint path: ")
        new_dataset = input("Enter the new dataset path: ")
        assistant = AssistantManager()
        assistant.load_and_retrain(checkpoint_path, new_dataset)
    else:
        print("Invalid choice. Exiting.")

    print("Chatbot is ready! Type 'exit' to end the conversation. Type 'gui' to launch the database manager.")

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        elif user_input.lower() == 'gui':
            root = tk.Tk()
            app = DatabaseManager(root)
            root.mainloop()
            continue

        response, confidence, intent = assistant.process_input(user_input)
        print(f"Bot: {response}")

        rating = input("Rate the response (1-5): ")
        while not rating.isdigit() or not (1 <= int(rating) <= 5):
            rating = input("Please enter a valid rating (1-5): ")

        expected_intent = input("What was the intent you expected? ")

        save_rating(user_input, response, int(rating), intent, expected_intent, confidence)

    evaluation_results = assistant.evaluate_model()
    print("Evaluation results:", evaluation_results)

if __name__ == "__main__":
    main()
