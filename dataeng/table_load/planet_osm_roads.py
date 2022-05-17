import pandas as pd
import snowflake.connector
import streamlit as st

conn = snowflake.connector.connect(**st.secrets['sfdevrel'])
conn.cursor().execute("USE WAREHOUSE RZ_S")
conn.cursor().execute("USE DATABASE ZWITCH_DEV_WORKSPACE")
conn.cursor().execute("USE SCHEMA ZWITCH_DEV_WORKSPACE.testschema")


conn.cursor().execute("PUT file:///Users/rzwitch/planet_osm_roads_us.csv.gz @%planet_osm_roads")
conn.cursor().execute("""COPY INTO planet_osm_roads
                       file_format = (TYPE = CSV, 
                                      SKIP_HEADER=1, 
                                      FIELD_OPTIONALLY_ENCLOSED_BY = '"'
                                      )
                        ON_ERROR = CONTINUE
                      """)