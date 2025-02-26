import pandas as pd
import streamlit as st

def show_comparison_table(agent_grid_steps_a_star, cbs_grid_steps):
    """
    สร้างตารางเปรียบเทียบระหว่าง A* และ CBS algorithms
    """
    # ตรวจสอบความยาวของข้อมูล
    len_a_star = len(agent_grid_steps_a_star)
    len_cbs = len(cbs_grid_steps)

    # แสดงข้อความแจ้งเตือนหากความยาวไม่เท่ากัน
    if len_a_star != len_cbs:
        st.warning(f"Warning: Data lengths are not equal (A*: {len_a_star}, CBS: {len_cbs}). Adjusting data...")

    # ปรับความยาวของข้อมูลให้เท่ากัน
    min_length = min(len_a_star, len_cbs)
    agent_grid_steps_a_star = agent_grid_steps_a_star[:min_length]
    cbs_grid_steps = dict(list(cbs_grid_steps.items())[:min_length])

    # สร้าง DataFrame สำหรับเก็บข้อมูล
    comparison_data = {
        'Algorithm': ['A*', 'CBS'],  # เอาออก M*
        'Total Grid Steps': [
            sum(agent_grid_steps_a_star),
            sum(cbs_grid_steps.values()),
        ],
        'Average Grid Steps per Agent': [
            sum(agent_grid_steps_a_star) / len(agent_grid_steps_a_star),
            sum(cbs_grid_steps.values()) / len(cbs_grid_steps),
        ],
        'Max Grid Steps': [
            max(agent_grid_steps_a_star),
            max(cbs_grid_steps.values()),
        ],
        'Min Grid Steps': [
            min(agent_grid_steps_a_star),
            min(cbs_grid_steps.values()),
        ]
    }

    # สร้าง DataFrame
    df = pd.DataFrame(comparison_data)

    # แสดงตารางใน Streamlit
    st.write("### Comparison Table: A* vs CBS")
    st.table(df)