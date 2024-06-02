import sqlite3
import pandas as pd
import streamlit as st
import plotly.express as px
from datetime import datetime, timedelta
from components import custom_metric,custom_title

st.set_page_config(page_title="PM Dashboard", page_icon=':bar_chart:', layout='wide')

@st.cache_data
def get_data_from_excel():
    try:
        conn = sqlite3.connect('line_database.db')
        cursor = conn.cursor()
        query = 'SELECT * FROM production_data '
        df = pd.read_sql_query(query, conn)
        conn.close()
    except FileNotFoundError:
        st.error("Database was not found.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.stop()
    return df

df = get_data_from_excel()

if df.empty:
    st.warning("The dataframe is empty. Please check the Excel file and the sheet name.")
    st.stop()

with open('style.css') as f:
    st.markdown(f'<style> {f.read()} </style>', unsafe_allow_html=True)

st.title(":bar_chart: PM TEAM AMA DASHBOARD")

# Convert 'ProductionDate' to datetime
df['ProductionDate'] = pd.to_datetime(df['ProductionDate'], errors='coerce')

# Ensure these columns exist before filtering
required_columns = ['ProductionDate', 'Line', 'Category', 'Equipment', 'Frequency', 'Duration', 'FunctionFailure']
for col in required_columns:
    if col not in df.columns:
        st.error(f"Column '{col}' is missing in the dataframe.")
        st.stop()

df = df[required_columns]

# Sidebar filters
st.sidebar.header("Data Filters")

# Initialize filters with the complete dataset
line = st.sidebar.multiselect('Select Line', options=df['Line'].unique(), default=df['Line'].unique())

# Calculate yesterday's date and today's date
yesterday = datetime.now() - timedelta(days=6)
today = datetime.now()

date_range = st.sidebar.date_input("Select Date Range", value=[yesterday.date(), today.date()])

# Check if all filters are selected
if not line:
    st.sidebar.error("Please select at least one Line.")
    st.stop()

if len(date_range) != 2:
    st.sidebar.error("Please select a valid date range.")
    st.stop()

# Convert date input to datetime
start_date = datetime.combine(date_range[0], datetime.min.time())
end_date = datetime.combine(date_range[1], datetime.max.time())

# Query the data based on selections
df_filtered = df[(df['Line'].isin(line)) & 
                 (df['ProductionDate'] >= start_date) & 
                 (df['ProductionDate'] <= end_date) 
                ]

# Check if filtered dataframe is empty
if df_filtered.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Separate data based on Category
df_bd = df_filtered[df_filtered['Category'] == "Breakdown"]
df_ms = df_filtered[df_filtered['Category'] == "Minor stops"]

# Metrics calculation
total_num_breakdown = df_bd['Line'].count()
total_duration_breakdown = df_bd['Duration'].sum()

total_num_minor_stops = df_ms['Line'].count()
total_duration_minor_stops = df_ms['Duration'].sum()

df_category = df_filtered.groupby(by=["Category"])['Duration'].sum().reset_index()

fig_pie = px.pie(df_category,
                 names='Category',
                 values='Duration',
                 template='simple_white',
                 title='Packaging Stops Classification')

# Calculate the number of days between the two dates, inclusive
number_of_days = (end_date - start_date).days + 1
total_production_hour = number_of_days * 24 * len(line)  # Total production hours for all selected lines
total_stops_hours = df_category['Duration'].sum() / 60  # Convert minutes to hours

available_production_time = total_production_hour - total_stops_hours

breakdown=df_category.loc[df_category['Category']=='Breakdown','Duration'].values[0]/60
minorstops=df_category.loc[df_category['Category']=='Minor stops','Duration'].values[0]/60

unplaned=breakdown+minorstops

unplaned_stopages=unplaned/total_stops_hours

total_stopages=total_stops_hours/(total_stops_hours+total_production_hour)


unplaned_downtime_production=(unplaned_stopages*total_stopages)*100



# Check to avoid division by zero
if total_num_breakdown > 0:
    mtbf = (available_production_time ) / total_num_breakdown
else:
    mtbf = 0

if total_num_minor_stops > 0:
    mtba = available_production_time / total_num_minor_stops
else:
    mtba = 0

# Prepare data for the pie chart
data = {
    'Category': ['Production Time', 'Stopages'],
    'Values': [total_production_hour, total_stops_hours ]
}

# Convert the data to a DataFrame
df_pie = pd.DataFrame(data)

# Create the pie chart
production_fig = px.pie(df_pie, names='Category', values='Values', title='Production Time vs Stopages')

# Display the chart in Streamlit
col1, col2 = st.columns(2)

st.subheader("Line Performance")

col1.plotly_chart(production_fig)
col2.plotly_chart(fig_pie)

# Display metrics
first_column, second_column,third_column = st.columns(3)

with first_column:
    custom_metric(label="MTBF", value=f"{mtbf:.2f} Hr")
    custom_metric(label="Duration Of Breakdown", value=f"{total_duration_breakdown} mins")

with second_column:
    custom_metric(label="MTBA", value=f"{mtba:.2f} Hr")
    custom_metric(label="Duration Of Minor Stops", value=f"{total_duration_minor_stops} mins")

with third_column:
    custom_metric(label="% Unplanned Downtime", value=f"{unplaned_downtime_production:.2f} %")
