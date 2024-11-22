import sqlite3
import pandas as pd

# Connect to the database
conn = sqlite3.connect(r'C:\Users\lucas\Documents\GitHub\Comp_tools_project\beer_data.db')

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
