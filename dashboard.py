import pandas as pd
import streamlit as st 
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="PM Dashboard", page_icon=':bar_chart:', layout='wide')

@st.cache_data
def get_data_from_excel():
    try:
        df = pd.read_excel(io="downtime.xlsx", sheet_name="Line14archive", engine="openpyxl")
    except FileNotFoundError:
        st.error("The file 'downtime.xlsx' was not found.")
        st.stop()
    except Exception as e:
        st.error(f"An error occurred: {e}")
        st.stop()
    return df

df1 = get_data_from_excel()

if df1.empty:
    st.warning("The dataframe is empty. Please check the Excel file and the sheet name.")
    st.stop()

# Filter data
df = df1[(df1['Category'] == "Breakdown Time") | (df1['Category'] == "Minor stops & Speed losses")]

st.title(":bar_chart: PM TEAM AMA DASHBOARD")

# Convert 'ProductionDate' to datetime
df['ProductionDate'] = pd.to_datetime(df['ProductionDate'], errors='coerce')

# Ensure these columns exist before filtering
required_columns = ['ProductionDate', 'Line', 'Category', 'SubCategory', 'Frequency', 'Duration', 'FailureDesc']
for col in required_columns:
    if col not in df.columns:
        st.error(f"Column '{col}' is missing in the dataframe.")
        st.stop()

df = df[required_columns]

# Sidebar filters
st.sidebar.header("Data Filters")
line = st.sidebar.multiselect('Select Line', options=df['Line'].unique(), default=[1])

# Calculate yesterday's date and today's date
yesterday = datetime.now() - timedelta(1)
today = datetime.now()

date_range = st.sidebar.date_input("Select Date Range", value=[yesterday.date(), today.date()])
equipment = st.sidebar.multiselect('Select Equipment', options=df['SubCategory'].unique(), default=df['SubCategory'].unique())

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
         (df['SubCategory'].isin(equipment))]

# Check if filtered dataframe is empty
if df.empty:
    st.warning("No data available for the selected filters.")
    st.stop()

# Separate data based on Category
df_bd = df[df['Category'] == "Breakdown Time"]
df_ms = df[df['Category'] == "Minor stops & Speed losses"]

# Metrics calculation
total_num_breakdown = df_bd['Line'].count()
total_duration_breakdown = df_bd['Duration'].sum()

total_num_minor_stops = df_ms['Line'].count()
total_duration_minor_stops = df_ms['Duration'].sum()

# Calculate number of breakdowns >= 60 mins
num_breakdown_60mins = df_bd[df_bd['Duration'] >= 60]['Line'].count()

# Display metrics
first_column, second_column, third_column = st.columns(3)

with first_column:

    st.caption("Total Number Of Breakdowns")
    st.caption(total_num_breakdown,)

    st.caption("Total Duration Of Breakdowns")
    st.caption(total_duration_breakdown)

with second_column:
    st.caption("Total Number Of Minor Stops")
    st.caption(total_num_minor_stops)

    st.caption("Total Duration Of Minor Stops")
    st.caption(total_duration_minor_stops)

with third_column:
    st.caption("No. Of Breakdowns >= 60 mins")
    st.caption(num_breakdown_60mins)

    st.caption("Additional Metric Here")
    st.caption("Additional Value Here")  # Placeholder for another metric

# Bar chart
bd_by_equipment = df_bd.groupby(by=['SubCategory'])[['Frequency', 'Duration']].sum().sort_values(by=['Duration', 'Frequency'], ascending=False)
ms_by_equipment = df_ms.groupby(by=['SubCategory'])[['Frequency', 'Duration']].sum().sort_values(by=['Duration', 'Frequency'], ascending=False)

# Group by 'SubCategory' and calculate the sum of 'Frequency' and 'Duration'
grouped_data_bd = df_bd.groupby(by=['SubCategory'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)
grouped_data_bdf = df_bd.groupby(by=['SubCategory', 'FailureDesc'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)
grouped_data_ms = df_ms.groupby(by=['SubCategory'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)
grouped_data_msf = df_ms.groupby(by=['SubCategory', 'FailureDesc'])[['Frequency', 'Duration']].sum().reset_index().sort_values(by=['Duration', 'Frequency'], ascending=False)

bd_column, ms_column = st.columns(2)

fig_bd = px.bar(bd_by_equipment, x=bd_by_equipment.index, y="Duration", title="Breakdown Duration per Machine")
fig_ms = px.bar(ms_by_equipment, x=ms_by_equipment.index, y="Duration", title="Minor Stop Duration per Machine")

# Create a grouped bar chart using Plotly Express
fig_grouped_bar_bd = px.bar(
    grouped_data_bd,
    x='SubCategory',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Breakdown Failure Modes",
    text_auto=True
)

fig_grouped_bar_ms = px.bar(
    grouped_data_ms,
    x='SubCategory',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Minor Stop Failure Modes",
    text_auto=True
)

fig_grouped_bar_bd_failures = px.bar(
    grouped_data_bdf,
    x='FailureDesc',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Breakdown Failure Modes",
    text_auto=True
)

fig_grouped_bar_ms_failures = px.bar(
    grouped_data_msf,
    x='FailureDesc',
    y=['Frequency', 'Duration'],
    barmode='group',
    title="Minor Stop Failure Modes",
    text_auto=True
)

df_bd_analysis = df_bd[(df_bd['Duration'] >= 60) | ((df_bd['Frequency'] >= 2) & (df_bd['Duration'] >= 30))].reset_index().drop("index", axis=1)

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
