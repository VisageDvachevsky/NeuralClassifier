import tkinter as tk
from tkinter import ttk, messagebox
from tkinter import simpledialog
import sqlite3
import ttkbootstrap as tb
from ttkbootstrap.constants import *

class DatabaseManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Manager")
        self.root.geometry("1000x600")
        self.style = tb.Style("flatly")

        self.tree = ttk.Treeview(self.root, show='headings', bootstyle="primary")
        self.tree['columns'] = ('ID', 'User Input', 'Response', 'Rating', 'Intent', 'Expected Intent', 'Confidence')
        self.tree.column("#0", width=0, stretch=tk.NO)
        self.tree.column("ID", anchor=tk.W, width=40)
        self.tree.column("User Input", anchor=tk.W, width=140)
        self.tree.column("Response", anchor=tk.W, width=140)
        self.tree.column("Rating", anchor=tk.W, width=60)
        self.tree.column("Intent", anchor=tk.W, width=120)
        self.tree.column("Expected Intent", anchor=tk.W, width=120)
        self.tree.column("Confidence", anchor=tk.W, width=80)

        self.tree.heading("#0", text="", anchor=tk.W)
        self.tree.heading("ID", text="ID", anchor=tk.W)
        self.tree.heading("User Input", text="User Input", anchor=tk.W)
        self.tree.heading("Response", text="Response", anchor=tk.W)
        self.tree.heading("Rating", text="Rating", anchor=tk.W)
        self.tree.heading("Intent", text="Intent", anchor=tk.W)
        self.tree.heading("Expected Intent", text="Expected Intent", anchor=tk.W)
        self.tree.heading("Confidence", text="Confidence", anchor=tk.W)

        self.tree.pack(pady=20, fill=tk.BOTH, expand=True)

        button_frame = ttk.Frame(self.root)
        button_frame.pack(pady=10)

        self.load_data_button = ttk.Button(button_frame, text="Load Data", command=self.load_data, bootstyle="success")
        self.load_data_button.grid(row=0, column=0, padx=10)

        self.delete_selected_button = ttk.Button(button_frame, text="Delete Selected", command=self.delete_selected, bootstyle="danger")
        self.delete_selected_button.grid(row=0, column=1, padx=10)

        self.edit_intent_button = ttk.Button(button_frame, text="Edit Expected Intent", command=self.edit_expected_intent, bootstyle="warning")
        self.edit_intent_button.grid(row=0, column=2, padx=10)

        self.tree.bind("<Double-1>", self.display_thought_process)

        self.load_data()

    def load_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = sqlite3.connect('../TGBot/responses.db')
        c = conn.cursor()
        c.execute("SELECT * FROM responses")
        rows = c.fetchall()
        for row in rows:
            self.tree.insert("", tk.END, values=row)
        conn.close()

    def delete_selected(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No selection", "Please select an item to delete")
            return

        conn = sqlite3.connect('../TGBot/responses.db')
        c = conn.cursor()
        for item in selected_item:
            item_id = self.tree.item(item, 'values')[0]
            c.execute("DELETE FROM responses WHERE id=?", (item_id,))
        conn.commit()
        conn.close()

        self.load_data()
        messagebox.showinfo("Deleted", "Selected item(s) deleted successfully")

    def display_thought_process(self, event):
        selected_item = self.tree.selection()[0]
        item = self.tree.item(selected_item)
        user_input = item['values'][1]
        response = item['values'][2]
        intent = item['values'][4]
        confidence = float(item['values'][6])  
        thought_process = f"User Input: {user_input}\nResponse: {response}\nPredicted Intent: {intent}\nConfidence: {confidence:.2f}"

        top = tb.Toplevel(self.root)
        top.title("Thought Process")
        ttk.Label(top, text=thought_process, justify=tk.LEFT, padding=(10, 10)).pack()

        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)

    def edit_expected_intent(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showwarning("No selection", "Please select an item to edit")
            return

        selected_item = selected_item[0]
        item = self.tree.item(selected_item)
        current_intent = item['values'][5]
        item_id = item['values'][0]

        new_intent = simpledialog.askstring("Edit Expected Intent", "Enter new Expected Intent:", initialvalue=current_intent, parent=self.root)
        if new_intent is not None:
            conn = sqlite3.connect('../TGBot/responses.db')
            c = conn.cursor()
            c.execute("UPDATE responses SET expected_intent=? WHERE id=?", (new_intent, item_id))
            conn.commit()
            conn.close()

            self.load_data()
            messagebox.showinfo("Updated", "Expected Intent updated successfully")

if __name__ == "__main__":
    root = tb.Window(themename="flatly")
    app = DatabaseManager(root)
    root.mainloop()
