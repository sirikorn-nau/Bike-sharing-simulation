import pandas as pd
# 1️⃣ ส่วน Import Library
import folium
import streamlit as st
import random
import heapq
import json
import time
import streamlit.components.v1 as components
import math

import osmnx as ox
import networkx as nx

from geopy.distance import geodesic 

from function.distance_real import *
from function_2.cbs_alogo import *
from function_2.osm_route import *
from function_2.find_route_osm import *
from function_2.create_map_2 import *
from function_2.compare_agent import *

from function_2.comparison_table import *

from function.statistics import *
from function.graph import *





def compare_agent(agent_grid_steps_a_star, cbs_grid_steps, m_star_grid_steps, start_positions, destination_positions, station_locations):
    """
    สร้างตาราง Simulation Summary สำหรับแต่ละ agent
    """
    # ตรวจสอบความยาวของข้อมูล
    len_a_star = len(agent_grid_steps_a_star)
    len_cbs = len(cbs_grid_steps)
    len_m_star = len(m_star_grid_steps)
    len_start = len(start_positions)
    len_dest = len(destination_positions)

    # แสดงข้อความแจ้งเตือนหากความยาวไม่เท่ากัน
    if len_a_star != len_cbs or len_a_star != len_m_star or len_a_star != len_start or len_a_star != len_dest:
        st.warning(f"Warning: Data lengths are not equal (A*: {len_a_star}, CBS: {len_cbs}, M*: {len_m_star}, Start: {len_start}, Dest: {len_dest}). Adjusting data...")

    # ปรับความยาวของข้อมูลให้เท่ากัน
    min_length = min(len_a_star, len_cbs, len_m_star, len_start, len_dest)
    agent_grid_steps_a_star = agent_grid_steps_a_star[:min_length]
    cbs_grid_steps = dict(list(cbs_grid_steps.items())[:min_length])
    m_star_grid_steps = dict(list(m_star_grid_steps.items())[:min_length])
    start_positions = start_positions[:min_length]
    destination_positions = destination_positions[:min_length]

    # สร้างข้อมูลสำหรับตาราง
    summary_data = []
    for i in range(min_length):
        # หาสถานีเริ่มต้นและสถานีปลายทาง
        start_station = min(station_locations, key=lambda s: geodesic(start_positions[i], s).meters)
        end_station = min(station_locations, key=lambda s: geodesic(destination_positions[i], s).meters)

        # คำนวณเปอร์เซ็นต์การลดลง
        a_star_steps = agent_grid_steps_a_star[i]
        cbs_steps = cbs_grid_steps[i]
        m_star_steps = m_star_grid_steps[i]

        improvement_cbs = (a_star_steps - cbs_steps) / a_star_steps * 100 if a_star_steps != 0 else 0
        improvement_m_star = (a_star_steps - m_star_steps) / a_star_steps * 100 if a_star_steps != 0 else 0

        # เพิ่มข้อมูลของแต่ละ agent
        summary_data.append({
            "Agent": f"Agent {i+1}",
            "A* Steps": a_star_steps,
            "CBS Steps": cbs_steps,
            "M* Steps": m_star_steps,
            "Improvement CBS (%)": f"{improvement_cbs:.2f}%",  # เพิ่มเปอร์เซ็นต์การลดลงของ CBS
            "Improvement M* (%)": f"{improvement_m_star:.2f}%",  # เพิ่มเปอร์เซ็นต์การลดลงของ M*
            "Start Position": start_positions[i],
            "Destination Position": destination_positions[i],
            "Start Station": start_station,
            "End Station": end_station
        })

    # สร้าง DataFrame
    df = pd.DataFrame(summary_data)

    # แสดงตารางใน Streamlit
    st.write("### Simulation Summary")
    st.table(df)