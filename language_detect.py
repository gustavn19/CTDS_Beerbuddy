import sqlite3
import pandas as pd
def get_data_from_db(db_name = "beer_data.db"):
    # Create a SQL connection to our SQLite database
    con = sqlite3.connect(db_name)

    cur = con.cursor()

    #cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    #print(f"Table Name : {cur.fetchall()}")

    df = pd.read_sql_query('SELECT * FROM beers', con)
    con.close()
    return df

df = get_data_from_db()





from langdetect import detect, DetectorFactory, LangDetectException


DetectorFactory.seed = 0

def safe_detect(text):
    """
    Detects the language of a given text.
    Returns 'unknown' if detection fails or the text is invalid.
    """
    try:
        return detect(text)
    except LangDetectException:
        return "unknown"
    




def detect_language(df):

    """
    detects the language of the review_texts and returns the english reviews.
    """

    reviews = df['review_text']
    
    # Detect languages for filtered reviews
    filtered_reviews = [review for review in reviews.dropna().unique() if isinstance(review, str) and len(review.strip()) > 3]

    #predict language
    language_predictions = {review: safe_detect(review) for review in filtered_reviews}

    df['language'] = df['review_text'].map(language_predictions)

    eng_df = df[df['language'] == 'en']

    return eng_df



dff = detect_language(df)
print(dff.head())