from typing import NamedTuple

import folium
import pandas as pd
import snowflake.connector
import streamlit as st

# from folium.plugins import FastMarkerCluster
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static, st_folium

## constants
# How many decimals to round to
ROUND_TO = 2


## classes
class Coordinates(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_dict(cls, coordinates: dict) -> "Coordinates":
        shift = 10 ** (-ROUND_TO)
        x1 = round(float(coordinates["_southWest"]["lng"]), ROUND_TO) - shift
        y1 = round(float(coordinates["_southWest"]["lat"]), ROUND_TO) - shift
        x2 = round(float(coordinates["_northEast"]["lng"]), ROUND_TO) + shift
        y2 = round(float(coordinates["_northEast"]["lat"]), ROUND_TO) + shift

        return cls(x1, y1, x2, y2)

## functions
@st.experimental_singleton
def sfconn():
    return snowflake.connector.connect(**st.secrets["sfdevrel"])

@st.experimental_memo(max_entries=128)
def get_data(coordinates: Coordinates, num_rows: int = 1000) -> pd.DataFrame:
    x1 = coordinates.x1
    y1 = coordinates.y1
    x2 = coordinates.x2
    y2 = coordinates.y2

    linestring = f"LINESTRING({x1} {y1}, {x2} {y1}, {x2} {y2}, {x1} {y2}, {x1} {y1})"

    polygon = f"st_makepolygon(to_geography('{linestring}'))"

    df = pd.read_sql(
        f"""
        select * from
        ZWITCH_DEV_WORKSPACE.TESTSCHEMA.PLANET_OSM_POINT
        where NAME is not null
        and st_within(WAY, {polygon})
        limit {num_rows}
        """,
        conn,
    )
    return df


if "points" not in st.session_state:
    st.session_state["points"] = []


## streamlit app code below
conn = sfconn()

tbl = st.sidebar.selectbox("Choose a geometry type", ["Point", "Line", "Polygon"], key = 'tbl')
fld = st.sidebar.selectbox("Choose a column", ["Access"])
tags = st.sidebar.multiselect("Choose tags to visualize", ["private", "permissive"])

m = folium.Map(location=(39.8, -86.1), zoom_start=14)

for point in st.session_state["points"]:
    # marker_cluster = FastMarkerCluster("Points").add_to(m)
    marker_cluster = MarkerCluster().add_to(m)
    gj = folium.GeoJson(data=point.WAY)
    gj.add_child(folium.Popup(point.NAME))
    gj.add_to(marker_cluster)


data = st_folium(m, width=1000)

st.expander("Show map data").json(data)

coordinates = Coordinates.from_dict(data["bounds"])

df = get_data(coordinates, 100)

df

for _, row in df.iterrows():
    st.session_state["points"][:] = [row for _, row in df.iterrows()]
