import pandas as pd
import tkinter as tk
from tkinter import ttk, messagebox
from langdetect import detect, DetectorFactory
from googletrans import Translator
import langid
from collections import Counter
import re
import threading

DetectorFactory.seed = 0

class LanguageUpdater:
    def __init__(self, csv_file):
        self.csv_file = csv_file
        self.df = pd.read_csv(csv_file)
        self.unknown_indices = self.df[(self.df['language'] == 'unknown') & (self.df['intent'] != 'No Intent')].index.tolist()
        self.current_index = 0
        self.languages = self.get_languages()
        self.translator = Translator()
        self.language_cache = {}

        self.root = tk.Tk()
        self.root.title("Language Updater")
        self.root.geometry("800x600")
        self.create_widgets()
        self.update_text()
        self.update_info()

        self.root.mainloop()

    def get_languages(self):
        languages = self.df['language'].unique().tolist()
        if 'unknown' not in languages:
            languages.append('unknown')
        return languages

    def create_widgets(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(pady=10, expand=True)

        self.lang_frame = ttk.Frame(self.notebook)
        self.info_frame = ttk.Frame(self.notebook)

        self.notebook.add(self.lang_frame, text="Update Language")
        self.notebook.add(self.info_frame, text="Info")

        self.create_lang_widgets()
        self.create_info_widgets()

    def create_lang_widgets(self):
        self.text_widget = tk.Text(self.lang_frame, wrap=tk.WORD, height=10, width=80)
        self.text_widget.pack(pady=10)
        self.text_widget.bind('<ButtonRelease-1>', self.translate_selected_text)

        self.translation_label = tk.Label(self.lang_frame, text="", wraplength=500, justify="left", fg="blue")
        self.translation_label.pack(pady=10)

        self.language_var = tk.StringVar(value='unknown')

        self.radio_frame = tk.Frame(self.lang_frame)
        self.radio_frame.pack(pady=10)

        self.radio_buttons = {}
        for lang in self.languages:
            rb = tk.Radiobutton(self.radio_frame, text=lang, variable=self.language_var, value=lang)
            rb.pack(side=tk.LEFT, padx=5)
            self.radio_buttons[lang] = rb

        self.nav_frame = tk.Frame(self.lang_frame)
        self.nav_frame.pack(pady=10)

        self.back_button = tk.Button(self.nav_frame, text="Back", command=self.prev_entry, state=tk.DISABLED)
        self.back_button.pack(side=tk.LEFT, padx=5)

        self.next_button = tk.Button(self.nav_frame, text="Next", command=self.next_entry)
        self.next_button.pack(side=tk.LEFT, padx=5)

        self.auto_button = tk.Button(self.lang_frame, text="Auto-Detect Languages", command=self.start_auto_detect)
        self.auto_button.pack(pady=10)

        self.save_button = tk.Button(self.lang_frame, text="Save & Exit", command=self.save_and_exit)
        self.save_button.pack(pady=10)

    def create_info_widgets(self):
        self.info_label = tk.Label(self.info_frame, text="", wraplength=500, justify="left")
        self.info_label.pack(pady=10)
        self.progress_bar = ttk.Progressbar(self.info_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(pady=10, fill=tk.X)
        self.progress_bar['maximum'] = len(self.unknown_indices)

    def update_text(self):
        if 0 <= self.current_index < len(self.unknown_indices):
            idx = self.unknown_indices[self.current_index]
            text = self.df.at[idx, 'text']
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, text)

            if text in self.language_cache:
                self.language_var.set(self.language_cache[text])
                self.radio_buttons[self.language_cache[text]].select()
                self.progress_bar['value'] = self.current_index + 1
            else:
                threading.Thread(target=self.set_language_prediction, args=(text,)).start()
        else:
            messagebox.showinfo("Info", "All unknown languages have been updated.")
            self.save_and_exit()

    def set_language_prediction(self, text):
        predicted_lang = self.predict_language(text)
        self.language_cache[text] = predicted_lang
        if predicted_lang in self.languages:
            self.language_var.set(predicted_lang)
            self.radio_buttons[predicted_lang].select()
        else:
            self.language_var.set('unknown')
            self.radio_buttons['unknown'].select()
        
        self.progress_bar['value'] = self.current_index + 1

    def update_info(self):
        remaining = len(self.unknown_indices) - self.current_index
        total = len(self.unknown_indices)
        info_text = f"Remaining entries to check: {remaining}\nTotal unknown entries: {total}"
        self.info_label.config(text=info_text)

    def predict_language(self, text):
        def detect_languages(text):
            predictions = []

            try:
                lang_code = detect(text)
                predictions.append(lang_code)
            except:
                pass

            try:
                langid_code, _ = langid.classify(text)
                predictions.append(langid_code)
            except:
                pass

            try:
                translated = self.translator.detect(text)
                googletrans_code = translated.lang
                predictions.append(googletrans_code)
            except:
                pass

            return predictions

        if text.isdigit() or re.match(r'^[a-zA-Z0-9]+$', text):
            return 'unknown'

        words = text.split()
        phrases = [text[i:i+20] for i in range(0, len(text), 20)]

        word_predictions = []
        for word in words:
            word_predictions.extend(detect_languages(word))

        phrase_predictions = []
        for phrase in phrases:
            phrase_predictions.extend(detect_languages(phrase))

        all_predictions = word_predictions + phrase_predictions
        if all_predictions:
            common_prediction = Counter(all_predictions).most_common(1)[0][0]
            lang_map = {
                'en': 'en',
                'es': 'es',
                'fr': 'fr',
                'de': 'de',
                'ru': 'ru'
            }
            return lang_map.get(common_prediction, 'unknown')
        else:
            return 'unknown'

    def translate_selected_text(self, event):
        try:
            selected_text = self.text_widget.selection_get()
            if selected_text:
                translation = self.translator.translate(selected_text, src='auto', dest='ru').text
                self.translation_label.config(text=translation)
        except tk.TclError:
            pass

    def start_auto_detect(self):
        self.auto_button.config(state=tk.DISABLED)
        threading.Thread(target=self.auto_detect_languages).start()

    def auto_detect_languages(self):
        for idx, entry in enumerate(self.unknown_indices):
            text = self.df.at[entry, 'text']
            detected_language = self.predict_language(text)
            self.df.at[entry, 'language'] = detected_language
            self.language_cache[text] = detected_language
            self.progress_bar['value'] = idx + 1
        self.update_text()
        self.update_info()
        self.auto_button.config(state=tk.NORMAL)
        messagebox.showinfo("Info", "Auto-detection completed. Please review the entries manually.")

    def next_entry(self):
        if self.current_index < len(self.unknown_indices):
            idx = self.unknown_indices[self.current_index]
            self.df.at[idx, 'language'] = self.language_var.get()
            self.language_cache[self.df.at[idx, 'text']] = self.language_var.get()
            self.current_index += 1
            if self.current_index < len(self.unknown_indices):
                self.update_text()
                self.back_button.config(state=tk.NORMAL)
                self.update_info()
            else:
                messagebox.showinfo("Info", "All unknown languages have been updated.")
                self.save_and_exit()
        else:
            self.save_and_exit()

    def prev_entry(self):
        if self.current_index > 0:
            idx = self.unknown_indices[self.current_index]
            self.df.at[idx, 'language'] = self.language_var.get()
            self.language_cache[self.df.at[idx, 'text']] = self.language_var.get()
            self.current_index -= 1
            self.update_text()
            self.update_info()
            if self.current_index == 0:
                self.back_button.config(state=tk.DISABLED)

    def save_and_exit(self):
        self.df.to_csv(self.csv_file, index=False)
        self.root.destroy()

if __name__ == "__main__":
    csv_file = "./Resources/_dataset/dataset.csv"
    LanguageUpdater(csv_file)
