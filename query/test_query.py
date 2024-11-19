import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('beer_data.db')

# Corrected SQL query
query = """
SELECT
    *
FROM beers;
"""

# Execute query
df = pd.read_sql_query(query, conn)

# Display the results
print(df)
