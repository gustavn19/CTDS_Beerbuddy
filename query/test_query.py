import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect('beer_data_2.db')

# Corrected SQL query
query = """
SELECT
    COUNT(DISTINCT name) AS unique_beers,
    COUNT(DISTINCT brewery) AS unique_breweries,
    COUNT(DISTINCT reviewer) AS unique_reviewers
FROM beers;
"""

# Execute query
df = pd.read_sql_query(query, conn)

# Display the results
print(df)
