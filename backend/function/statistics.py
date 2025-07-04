
import streamlit as st
import numpy as np





def show_statistics(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mStar):
    st.write("### Summary Statistics")

    # ตัวอย่างการตรวจสอบข้อมูล
    print("ABS Steps:", agent_grid_steps_abs)
    print("CBS Steps:", agent_grid_steps_cbs)
    print("M* Steps:", agent_grid_steps_mStar)
    
    # คำนวณค่าเฉลี่ย, ค่ามัธยฐาน, และค่าสูงสุด
    avg_abs = np.mean(agent_grid_steps_abs)
    avg_cbs = np.mean(agent_grid_steps_cbs)
    avg_mStar = np.mean(agent_grid_steps_mStar)

    max_abs = np.max(agent_grid_steps_abs)
    max_cbs = np.max(agent_grid_steps_cbs)
    max_mStar = np.max(agent_grid_steps_mStar)

    # คำนวณค่าต่ำสุด
    min_abs = np.min(agent_grid_steps_abs)
    min_cbs = np.min(agent_grid_steps_cbs)
    min_mStar = np.min(agent_grid_steps_mStar)

    # Display results
    st.write(f"**Average Grid Steps:** A* = {avg_abs:.2f}, CBS = {avg_cbs:.2f}, M* = {avg_mStar:.2f}")
    st.write(f"**Maximum Grid Steps:** A* = {max_abs}, CBS = {max_cbs}, M* = {max_mStar}")
    st.write(f"**Minimum Grid Steps:** A* = {min_abs}, CBS = {min_cbs}, M* = {min_mStar}")

    # Calculate percentage improvement
    improvement_cbs = (avg_abs - avg_cbs) / avg_abs * 100
    improvement_mStar = (avg_abs - avg_mStar) / avg_abs * 100
    st.write(f"**Reduction in Grid Steps when using CBS:** {improvement_cbs:.2f}%")
    st.write(f"**Reduction in Grid Steps when using M*:** {improvement_mStar:.2f}%")