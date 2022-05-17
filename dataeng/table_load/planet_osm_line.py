import pandas as pd
import snowflake.connector
import streamlit as st

from os import listdir

conn = snowflake.connector.connect(**st.secrets['sfdevrel'])
conn.cursor().execute("USE WAREHOUSE RZ_S")
conn.cursor().execute("USE DATABASE ZWITCH_DEV_WORKSPACE")
conn.cursor().execute("USE SCHEMA ZWITCH_DEV_WORKSPACE.testschema")

flist = listdir("/Users/rzwitch/planet_osm_line")
for f in flist:
  conn.cursor().execute(f"PUT file:///Users/rzwitch/planet_osm_line/{f} @%planet_osm_line")
  print(f + " loaded successfully")

conn.cursor().execute("""COPY INTO planet_osm_line
                       file_format = (TYPE = CSV, 
                                      SKIP_HEADER=1, 
                                      FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                                      )
                        ON_ERROR = CONTINUE
                      """)