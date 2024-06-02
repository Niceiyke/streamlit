import streamlit as st


def custom_metric(label, value):
    st.markdown(f"""
    <div class="custom-metric">
        <div class="metric-label">{label}</div>
        <div class="metric-value">{value}</div>
       
    </div>
    """, unsafe_allow_html=True)

def custom_title(title):
    st.markdown(f"""
    <div class="custom-metric">
        <h1 class="title-label">{title}</h1>
       
       
    </div>
    """, unsafe_allow_html=True)