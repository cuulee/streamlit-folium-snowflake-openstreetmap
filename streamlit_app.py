import streamlit as st
import pandas as pd
import snowflake.connector

@st.experimental_singleton
def sfconn():
    return snowflake.connector.connect(**st.secrets['sfdevrel'])

# make single connection to snowflake
conn = sfconn()

# # use convenience method in pandas to avoid cursors
df = pd.read_sql("select * from ZWITCH_DEV_WORKSPACE.INFORMATION_SCHEMA.DATABASES limit 100", conn)

df