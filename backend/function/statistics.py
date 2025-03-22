
import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic 

import plotly.express as px
import pandas as pd





def show_statistics(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mStar):
    st.write("### สถิติสรุป")
    # ตัวอย่างการตรวจสอบข้อมูล
    print("ABS Steps:", agent_grid_steps_abs)
    print("CBS Steps:", agent_grid_steps_cbs)
    print("M* Steps:", agent_grid_steps_mStar)
    
    # คำนวณค่าเฉลี่ย, ค่ามัธยฐาน, และค่าสูงสุด
    avg_abs = np.mean(agent_grid_steps_abs)
    avg_cbs = np.mean(agent_grid_steps_cbs)
    avg_mStar = np.mean(agent_grid_steps_mStar)

    median_abs = np.median(agent_grid_steps_abs)
    median_cbs = np.median(agent_grid_steps_cbs)
    median_mStar = np.median(agent_grid_steps_mStar)

    max_abs = np.max(agent_grid_steps_abs)
    max_cbs = np.max(agent_grid_steps_cbs)
    max_mStar = np.max(agent_grid_steps_mStar)

    # คำนวณค่าเบี่ยงเบนมาตรฐาน
    std_abs = np.std(agent_grid_steps_abs)
    std_cbs = np.std(agent_grid_steps_cbs)
    std_mStar = np.std(agent_grid_steps_mStar)

    # คำนวณค่าต่ำสุด
    min_abs = np.min(agent_grid_steps_abs)
    min_cbs = np.min(agent_grid_steps_cbs)
    min_mStar = np.min(agent_grid_steps_mStar)

    # คำนวณค่าพิสัย (Range)
    range_abs = max_abs - min_abs
    range_cbs = max_cbs - min_cbs
    range_mStar = max_mStar - min_mStar

    # คำนวณเปอร์เซ็นไทล์ (เช่น 25th, 75th)
    percentile_25_abs = np.percentile(agent_grid_steps_abs, 25)
    percentile_75_abs = np.percentile(agent_grid_steps_abs, 75)

    percentile_25_cbs = np.percentile(agent_grid_steps_cbs, 25)
    percentile_75_cbs = np.percentile(agent_grid_steps_cbs, 75)

    percentile_25_mStar = np.percentile(agent_grid_steps_mStar, 25)
    percentile_75_mStar = np.percentile(agent_grid_steps_mStar, 75)

    # แสดงผล
    st.write(f"**ค่าเฉลี่ย Grid Steps:** ABS = {avg_abs:.2f}, CBS = {avg_cbs:.2f}, M* = {avg_mStar:.2f}")
    # st.write(f"**ค่ามัธยฐาน Grid Steps:** ABS = {median_abs}, CBS = {median_cbs}, M* = {median_mStar}")
    st.write(f"**ค่าสูงสุด Grid Steps:** ABS = {max_abs}, CBS = {max_cbs}, M* = {max_mStar}")
    st.write(f"**ค่าต่ำสุด Grid Steps:** ABS = {min_abs}, CBS = {min_cbs}, M* = {min_mStar}")
    # st.write(f"**ค่าเบี่ยงเบนมาตรฐาน Grid Steps:** ABS = {std_abs:.2f}, CBS = {std_cbs:.2f}, M* = {std_mStar:.2f}")
    # st.write(f"**ค่าพิสัย Grid Steps:** ABS = {range_abs}, CBS = {range_cbs}, M* = {range_mStar}")
    # st.write(f"**เปอร์เซ็นไทล์ที่ 25:** ABS = {percentile_25_abs}, CBS = {percentile_25_cbs}, M* = {percentile_25_mStar}")
    # st.write(f"**เปอร์เซ็นไทล์ที่ 75:** ABS = {percentile_75_abs}, CBS = {percentile_75_cbs}, M* = {percentile_75_mStar}")

    # คำนวณเปอร์เซ็นต์การลดลง
    improvement_cbs = (avg_abs - avg_cbs) / avg_abs * 100
    improvement_mStar = (avg_abs - avg_mStar) / avg_abs * 100
    st.write(f"**การลดลงของ Grid Steps เมื่อใช้ CBS:** {improvement_cbs:.2f}%")
    st.write(f"**การลดลงของ Grid Steps เมื่อใช้ M*:** {improvement_mStar:.2f}%")