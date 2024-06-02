import pandas as pd


df1=pd.read_csv("line56.csv")
selected_column=['A_Date_','Description_',	'H_Machine_','C_Line_',	'Frequency_',	'E_Duration_','G_Downtime_Type',	]
df=df1[selected_column]
new_column=['ProductionDate','FunctionFailure','Equipment','Line','Frequency','Duration','Category']

df.columns=new_column
df['Category']=df['Category'].replace({'Break Down':'Breakdown','Minor Stop':'Minor stops'})


print("done")
