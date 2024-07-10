import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3

class DatabaseManager:
    def __init__(self, root):
        self.root = root
        self.root.title("Database Manager")
        self.root.geometry("1000x600")

        self.tree = ttk.Treeview(self.root)
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

        self.load_data_button = tk.Button(self.root, text="Load Data", command=self.load_data)
        self.load_data_button.pack(pady=10)

        self.delete_selected_button = tk.Button(self.root, text="Delete Selected", command=self.delete_selected)
        self.delete_selected_button.pack(pady=10)

        self.tree.bind("<Double-1>", self.display_thought_process)

        self.load_data()

    def load_data(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

        conn = sqlite3.connect('../Dataset/Resources/responses.db')
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

        conn = sqlite3.connect('../Dataset/Resources/responses.db')
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
        confidence = item['values'][6]
        thought_process = f"User Input: {user_input}\nResponse: {response}\nPredicted Intent: {intent}\nConfidence: {confidence:.2f}"

        top = tk.Toplevel(self.root)
        top.title("Thought Process")
        tk.Label(top, text=thought_process, justify=tk.LEFT, padx=10, pady=10).pack()

        top.transient(self.root)
        top.grab_set()
        self.root.wait_window(top)

if __name__ == "__main__":
    root = tk.Tk()
    app = DatabaseManager(root)
    root.mainloop()
