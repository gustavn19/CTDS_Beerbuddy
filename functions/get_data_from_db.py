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