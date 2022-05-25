import json
from tkinter import W
from typing import Dict, NamedTuple

import folium
import pandas as pd
import snowflake.connector
import streamlit as st
from streamlit_folium import folium_static, st_folium

## constants
# How many decimals to round to
ROUND_TO = 1
COLORS = [
    "red",
    "blue",
    "green",
    "purple",
    "orange",
    "darkred",
    "lightred",
    "beige",
    "darkblue",
    "darkgreen",
    "cadetblue",
    "darkpurple",
    "white",
    "pink",
    "lightblue",
    "lightgreen",
    "gray",
    "black",
    "lightgray",
]


## classes
class Coordinates(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float

    @classmethod
    def from_dict(cls, coordinates: dict) -> "Coordinates":
        shift = 10 ** (-ROUND_TO)
        x1 = round(float(coordinates["_southWest"]["lng"]) - shift, ROUND_TO)
        y1 = round(float(coordinates["_southWest"]["lat"]) - shift, ROUND_TO)
        x2 = round(float(coordinates["_northEast"]["lng"]) + shift, ROUND_TO)
        y2 = round(float(coordinates["_northEast"]["lat"]) + shift, ROUND_TO)

        return cls(x1, y1, x2, y2)


## functions
@st.experimental_singleton
def sfconn():
    return snowflake.connector.connect(**st.secrets["sfdevrel"])


@st.experimental_memo(max_entries=128)
def _get_data(query: str) -> pd.DataFrame:
    df = pd.read_sql(
        query,
        conn,
    )
    return df


def get_data(
    coordinates: Coordinates,
    table: str = "POINT",
    column: str = "ACCESS",
    num_rows: int = 1000,
) -> pd.DataFrame:
    x1 = coordinates.x1
    y1 = coordinates.y1
    x2 = coordinates.x2
    y2 = coordinates.y2

    linestring = f"LINESTRING({x1} {y1}, {x2} {y1}, {x2} {y2}, {x1} {y2}, {x1} {y1})"

    polygon = f"st_makepolygon(to_geography('{linestring}'))"

    query = f"""
        select
            *
        from ZWITCH_DEV_WORKSPACE.TESTSCHEMA.PLANET_OSM_{table}
        where NAME is not null
        and {column} is not null
        and st_within(WAY, {polygon})
        limit {num_rows}
        """

    st.expander("Show query").code(query)

    return _get_data(query)


@st.experimental_singleton
def get_flds_in_table(tbl):

    df = pd.read_sql(
        f"show columns in ZWITCH_DEV_WORKSPACE.TESTSCHEMA.planet_osm_{tbl.lower()}",
        conn,
    )

    return df[~df["column_name"].isin(["OSM_ID", "WAY"])]["column_name"]


if "points" not in st.session_state:
    st.session_state["points"] = pd.DataFrame()


## streamlit app code below
conn = sfconn()

tbl = st.sidebar.selectbox(
    "1. Choose a geometry type", ["Point", "Line", "Polygon"], key="tbl"
)

flds = get_flds_in_table(tbl)
col_selected = st.sidebar.selectbox("2. Choose a column", flds)


tags = st.sidebar.multiselect("3. Choose tags to visualize", ["private", "permissive"])

num_rows = st.sidebar.select_slider(
    "How many rows?", [10, 100, 1000, 10_000], value=100
)

m = folium.Map(location=(39.8, -86.1), zoom_start=13)


map_data = st_folium(m, width=1000)

st.expander("Show map data").json(map_data)

coordinates = Coordinates.from_dict(map_data["bounds"])

df = get_data(coordinates, column=col_selected, table=tbl, num_rows=num_rows)

st.expander("Show data").write(df)

st.session_state["points"] = df

m = folium.Map(location=(39.8, -86.1), zoom_start=13)

df = st.session_state["points"]

unique_vals = df[col_selected].unique()

color_map = {val: COLORS[idx % len(COLORS)] for idx, val in enumerate(unique_vals)}

features: list[dict] = []

for _, point in st.session_state["points"].iterrows():
    color = color_map[point[col_selected]]

    features.append(
        {
            "type": "Feature",
            "geometry": json.loads(point.WAY),
            "properties": {
                "color": color,
                "NAME": point["NAME"],
                col_selected: point[col_selected],
            },
        }
    )

feature_collection = {
    "type": "FeatureCollection",
    "features": features,
    "properties": {"color": "purple"},
}


def get_color(feature: dict) -> dict:
    return {
        #'fillColor': '#ffaf00',
        "color": feature["properties"]["color"],
        # "fillColor": feature["properties"]["color"],
        #'weight': 1.5,
        #'dashArray': '5, 5'
    }


st.expander("Show features").json(feature_collection)

gj = folium.GeoJson(data=feature_collection, style_function=get_color)

folium.GeoJsonPopup(fields=["NAME", col_selected], labels=True).add_to(gj)

gj.add_to(m)

x = """
    if tbl == "point":
        gj = folium.GeoJson(
            data=point.WAY, marker=folium.Marker(icon=folium.Icon(color=color))
        )
    else:
        gj = folium.GeoJson(
            data=point.WAY,
        )
    gj.add_child(folium.Popup(f"{point.NAME}\n{col_selected}: {point[col_selected]}"))
    gj.add_to(m)
"""

st_folium(m, width=1000, key="second_map")
