import sqlite3

def create_database():
    conn = sqlite3.connect('./Dataset/Resources/responses.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS responses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_input TEXT,
            response TEXT,
            rating INTEGER,
            intent TEXT,
            expected_intent TEXT,
            confidence REAL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def save_rating(user_input, response, rating, intent, expected_intent, confidence):
    conn = sqlite3.connect('./Dataset/Resources/responses.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO responses (user_input, response, rating, intent, expected_intent, confidence)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_input, response, rating, intent, expected_intent, confidence))
    conn.commit()
    conn.close()

def fetch_feedback():
    conn = sqlite3.connect('./Dataset/Resources/responses.db')
    c = conn.cursor()
    c.execute('''
        SELECT user_input, expected_intent, confidence, rating
        FROM responses
        WHERE rating < 3 
    ''')
    feedback_data = c.fetchall()
    conn.close()
    return feedback_data

def save_sample_to_db(sample_df, db_path='./Dataset/Resources/responses.db'):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    sample_df.to_sql('original_dataset', conn, if_exists='replace', index=False)
    conn.commit()
    conn.close()
