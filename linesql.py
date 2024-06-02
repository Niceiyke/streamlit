import pandas as pd
import sqlite3

# Step 1: Read the Excel file
excel_file_path = 'archive.xlsx'
df = pd.read_excel(io=excel_file_path,sheet_name='Sheet1',engine='openpyxl')
print("done readinf excel file")

# Step 2: Create a SQLite database connection
conn = sqlite3.connect('line_database.db')
cursor = conn.cursor()

# Step 3: Create a table in the SQLite database
create_table_query = '''
CREATE TABLE IF NOT EXISTS production_data (
    ProductionDate TEXT,
    FunctionFailure TEXT,
    Equipment TEXT,
    Line Integer,
    Frequency INTEGER,
    Duration INTEGER,
    Category TEXT
)
'''
cursor.execute(create_table_query)
conn.commit()

# Step 4: Insert the data into the table
df.to_sql('production_data', conn, if_exists='append', index=False)

# Close the database connection
conn.close()
