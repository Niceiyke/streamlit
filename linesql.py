import pandas as pd
import sqlite3

# Step 1: Read the Excel file
file_path = 'archive.csv'
df = pd.read_csv(file_path,encoding='latin')
df['Category']=df['Category'].replace({'Minor stops & Speed losses':'Minor stops','Minor Stop':'Minor stops','Break Down':'Breakdown','Breakdown Time':'Breakdown'})
df['FunctionFailure']=df['FunctionFailure'].replace({'Whethered bottles':'weathered bottles','influx of weathered bottles':'weathered bottles'})
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


query = 'SELECT * FROM production_data'
df1 = pd.read_sql_query(query, conn)

print(df1.tail())

# Close the database connection
conn.close()
