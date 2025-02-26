
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic 

import plotly.express as px
import pandas as pd





def show_statistics(agent_grid_steps_abs, agent_grid_steps_cbs):
    st.write("### สถิติสรุป")
    
    # คำนวณค่าเฉลี่ย, ค่ามัธยฐาน, และค่าสูงสุด
    avg_abs = np.mean(agent_grid_steps_abs)
    avg_cbs = np.mean(agent_grid_steps_cbs)
    median_abs = np.median(agent_grid_steps_abs)
    median_cbs = np.median(agent_grid_steps_cbs)
    max_abs = np.max(agent_grid_steps_abs)
    max_cbs = np.max(agent_grid_steps_cbs)
    
    # แสดงผล
    st.write(f"**ค่าเฉลี่ย Grid Steps:** ABS = {avg_abs:.2f}, CBS = {avg_cbs:.2f}")
    st.write(f"**ค่ามัธยฐาน Grid Steps:** ABS = {median_abs}, CBS = {median_cbs}")
    st.write(f"**ค่าสูงสุด Grid Steps:** ABS = {max_abs}, CBS = {max_cbs}")
    
    # คำนวณเปอร์เซ็นต์การลดลง
    improvement = (avg_abs - avg_cbs) / avg_abs * 100
    st.write(f"**การลดลงของ Grid Steps เมื่อใช้ CBS:** {improvement:.2f}%")

