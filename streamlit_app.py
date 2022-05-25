import folium
import pandas as pd
import snowflake.connector
import streamlit as st

# from folium.plugins import FastMarkerCluster
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static, st_folium


@st.experimental_singleton
def sfconn():
    return snowflake.connector.connect(**st.secrets["sfdevrel"])


conn = sfconn()


@st.experimental_memo
def get_data(coordinates: dict, num_rows: int = 1000) -> pd.DataFrame:
    x1 = coordinates["_southWest"]["lng"]
    y1 = coordinates["_southWest"]["lat"]
    x2 = coordinates["_northEast"]["lng"]
    y2 = coordinates["_northEast"]["lat"]

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


m = folium.Map(location=(39.8, -86.1), zoom_start=14)

for point in st.session_state["points"]:
    # marker_cluster = FastMarkerCluster("Points").add_to(m)
    marker_cluster = MarkerCluster().add_to(m)
    gj = folium.GeoJson(data=point.WAY)
    gj.add_child(folium.Popup(point.NAME))
    gj.add_to(marker_cluster)


data = st_folium(m, width=1000)

st.expander("Show map data").json(data)

df = get_data(data["bounds"], 100)

df

for _, row in df.iterrows():
    st.session_state["points"][:] = [row for _, row in df.iterrows()]
