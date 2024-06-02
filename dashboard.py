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
        query = 'SELECT * FROM production_data WHERE Category IN ("Breakdown", "Minor stops")'
        df = pd.read_sql_query(query, conn)
        conn.close()
    except FileNotFoundError:
        st.error("The file 'downtime.xlsx' was not found.")
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
line = st.sidebar.multiselect('Select Line', options=df['Line'].unique(), default=[1])

# Calculate yesterday's date and today's date
yesterday = datetime.now() - timedelta(6)
today = datetime.now()


date_range = st.sidebar.date_input("Select Date Range", value=[yesterday.date(), today.date()])


# Update available options for 'Equipment' based on selected lines
filtered_df = df[df['Line'].isin(line)]
equipment_options = filtered_df['Equipment'].unique()
equipment = st.sidebar.multiselect('Select Equipment', options=equipment_options, default=equipment_options)


# Check if all filters are selected
if not line:
    st.sidebar.error("Please select at least one Line.")
    st.stop()

if not equipment:
    st.sidebar.error("Please select at least one Equipment.")
    st.stop()

if len(date_range) != 2:
    st.sidebar.error("Please select a valid date range.")
    st.stop()

# Convert date input to datetime
start_date = datetime.combine(date_range[0], datetime.min.time())
end_date = datetime.combine(date_range[1], datetime.max.time())

# Query the data based on selections
df = df[(df['Line'].isin(line)) & 
        (df['ProductionDate'] >= start_date) & 
        (df['ProductionDate'] <= end_date) &
        (df['Equipment'].isin(equipment))]

# Check if filtered dataframe is empty
if df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Separate data based on Category
df_bd = df[df['Category'] == "Breakdown"]
df_ms = df[df['Category'] == "Minor stops"]

# Metrics calculation
total_num_breakdown = df_bd['Line'].count()
total_duration_breakdown = df_bd['Duration'].sum()

total_num_minor_stops = df_ms['Line'].count()
total_duration_minor_stops = df_ms['Duration'].sum()

df_bd_analysis = df_bd[(df_bd['Duration'] >= 60) | ((df_bd['Frequency'] >= 2) & (df_bd['Duration'] >= 30))].reset_index().drop("index", axis=1)


# Display metrics
first_column, second_column, third_column = st.columns(3)

with first_column:
    custom_metric(label="Number Of Breakdowns", value=total_num_breakdown)
    custom_metric(label="Duration Of Breakdown", value=f"{total_duration_breakdown} mins")

with second_column:
    custom_metric(label="Number Of Minor Stops", value=total_num_minor_stops)
    custom_metric(label="Duration Of Minor Stops", value=f"{total_duration_minor_stops} mins")

with third_column:
    custom_metric(label="N0.Breakdowns for Analysis", value=df_bd_analysis['Duration'].count())
    custom_metric(label="Breakdowns for Analysis", value=f"{df_bd_analysis['Duration'].sum()} mins")

# Bar chart
bd_by_equipment = df_bd.groupby(by=['Equipment'])[['Frequency', 'Duration']].sum().sort_values(by=['Duration', 'Frequency'], ascending=False)
ms_by_equipment = df_ms.groupby(by=['Equipment'])[['Frequency', 'Duration']].sum().sort_values(by=['Duration', 'Frequency'], ascending=False)

# Group by 'Equipment' and calculate the sum of 'Frequency' and 'Duration'
grouped_data_bd = df_bd.groupby(by=['Equipment'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)
grouped_data_bdf = df_bd.groupby(by=['Equipment', 'FunctionFailure'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)
grouped_data_ms = df_ms.groupby(by=['Equipment'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)
grouped_data_msf = df_ms.groupby(by=['Equipment', 'FunctionFailure'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)

bd_column, ms_column = st.columns(2)


custom_colors = ["#0571ec", "#e4a908"]


fig_bd = px.bar(bd_by_equipment, x=bd_by_equipment.index, y="Duration", 
                title="Breakdown Duration per Machine",
                color_discrete_sequence=["#0571ec"],
                template='simple_white' )
fig_ms = px.bar(ms_by_equipment, 
                x=ms_by_equipment.index, 
                y="Duration", 
                title="Minor Stop Duration per Machine",
                color_discrete_sequence=["#0571ec"],
                template='simple_white' )

# Create a grouped bar chart using Plotly Express
fig_grouped_bar_bd = px.bar(
    grouped_data_bd,
    x='Equipment',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Breakdown Deployment",
    text_auto=True,
     color_discrete_sequence=custom_colors,
    template='simple_white' 
)

fig_grouped_bar_ms = px.bar(
    grouped_data_ms,
    x='Equipment',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Minor Stop Deployment",
    text_auto=True,
    color_discrete_sequence=custom_colors,
    template='simple_white',
)

fig_grouped_bar_bd_failures = px.bar(
    grouped_data_bdf,
    x='FunctionFailure',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Breakdown Function Failures",
    text_auto=True,
    color_discrete_sequence=custom_colors,
    template='simple_white',
)

fig_grouped_bar_ms_failures = px.bar(
    grouped_data_msf,
    x='FunctionFailure',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Minor Stop Function Failures",
    text_auto=True,
    color_discrete_sequence=custom_colors,
    template='simple_white',
)

fig_grouped_bar_bd_failures.update_yaxes(title_text='')
fig_grouped_bar_bd_failures.update_xaxes(tickfont=dict(size=14))
fig_grouped_bar_ms_failures.update_yaxes(title_text='')
fig_grouped_bar_ms_failures.update_xaxes(tickfont=dict(size=14))


with bd_column:
    st.plotly_chart(fig_bd)
with ms_column:
    st.plotly_chart(fig_ms)

st.markdown("##")

with bd_column:
    st.plotly_chart(fig_grouped_bar_bd)
with ms_column:
    st.plotly_chart(fig_grouped_bar_ms)

st.markdown("##")

with bd_column:
    st.plotly_chart(fig_grouped_bar_bd_failures)
with ms_column:
    st.plotly_chart(fig_grouped_bar_ms_failures)

st.dataframe(df_bd_analysis)
