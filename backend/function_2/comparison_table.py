import pandas as pd
import streamlit as st
def show_comparison_table(agent_grid_steps_a_star, cbs_grid_steps, m_star_grid_steps):
    """
    สร้างตารางเปรียบเทียบระหว่าง A*, CBS, และ M* algorithms
    """
    # ตรวจสอบความยาวของข้อมูล
    len_a_star = len(agent_grid_steps_a_star)
    len_cbs = len(cbs_grid_steps)
    len_m_star = len(m_star_grid_steps)

    # แสดงข้อความแจ้งเตือนหากความยาวไม่เท่ากัน
    if len_a_star != len_cbs or len_a_star != len_m_star:
        st.warning(f"Warning: Data lengths are not equal (A*: {len_a_star}, CBS: {len_cbs}, M*: {len_m_star}). Adjusting data...")

    # ปรับความยาวของข้อมูลให้เท่ากัน
    min_length = min(len_a_star, len_cbs, len_m_star)
    agent_grid_steps_a_star = agent_grid_steps_a_star[:min_length]
    cbs_grid_steps = dict(list(cbs_grid_steps.items())[:min_length])
    m_star_grid_steps = dict(list(m_star_grid_steps.items())[:min_length])

    # สร้าง DataFrame สำหรับเก็บข้อมูล
    comparison_data = {
        'Algorithm': ['A*', 'CBS', 'M*'],  # เพิ่ม M* เข้าไป
        'Total Grid Steps': [
            sum(agent_grid_steps_a_star),
            sum(cbs_grid_steps.values()),
            sum(m_star_grid_steps.values()),
        ],
        'Average Grid Steps per Agent': [
            sum(agent_grid_steps_a_star) / len(agent_grid_steps_a_star),
            sum(cbs_grid_steps.values()) / len(cbs_grid_steps),
            sum(m_star_grid_steps.values()) / len(m_star_grid_steps),
        ],
        'Max Grid Steps': [
            max(agent_grid_steps_a_star),
            max(cbs_grid_steps.values()),
            max(m_star_grid_steps.values()),
        ],
        'Min Grid Steps': [
            min(agent_grid_steps_a_star),
            min(cbs_grid_steps.values()),
            min(m_star_grid_steps.values()),
        ]
    }

    # สร้าง DataFrame
    df = pd.DataFrame(comparison_data)

    # แสดงตารางใน Streamlit
    st.write("### Comparison Table: A* vs CBS vs M*")
    st.table(df)