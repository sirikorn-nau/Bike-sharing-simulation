import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic 

import plotly.express as px
import pandas as pd

from function.distance_real import *
from function_2.cbs_alogo import *
from function_2.osm_route import *
from function_2.find_route_osm import *
from function_2.create_map_2 import *


from function.statistics import *
from function.graph import *



# สร้างข้อมูลตัวอย่างสำหรับกราฟ
def create_summary_chart(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mstar):
    num_agents = len(agent_grid_steps_abs)  # จำนวน agent
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # สร้างกราฟแท่งสำหรับ ABS, CBS และ M*
    width = 0.3
    x = np.arange(num_agents)

    ax.bar(x - width, agent_grid_steps_abs, width=width, label='ABS', color='blue')
    ax.bar(x, agent_grid_steps_cbs, width=width, label='CBS', color='orange')
    ax.bar(x + width, agent_grid_steps_mstar, width=width, label='M*', color='green')

    # ปรับแต่งกราฟ
    ax.set_xlabel('Agent')
    ax.set_ylabel('Grid Steps')
    ax.set_title('Comparison of Grid Steps: ABS vs CBS vs M*')
    ax.set_xticks(x)
    ax.set_xticklabels([f'Agent {i+1}' for i in range(num_agents)])
    ax.legend()

    return fig

# แสดงกราฟใน Streamlit
def show_summary_chart(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mstar):
    st.write("### Summary Chart: ABS vs CBS vs M*")
    fig = create_summary_chart(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mstar)
    st.pyplot(fig)

# สร้าง DataFrame สำหรับ plotly
def create_summary_dataframe(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mstar):
    num_agents = len(agent_grid_steps_abs)
    data = {
        'Agent': [f'Agent {i+1}' for i in range(num_agents)],
        'ABS': agent_grid_steps_abs,
        'CBS': agent_grid_steps_cbs,
        'M*': agent_grid_steps_mstar
    }
    return pd.DataFrame(data)

# แสดงกราฟสรุปด้วย plotly
def show_summary_chart_plotly(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mstar):

    st.write("### Summary Chart: ABS vs CBS vs M*")
    df = create_summary_dataframe(agent_grid_steps_abs, agent_grid_steps_cbs, agent_grid_steps_mstar)
    fig = px.bar(df, x='Agent', y=['ABS', 'CBS', 'M*'], barmode='group', title='Comparison of Grid Steps: ABS vs CBS vs M*')
    st.plotly_chart(fig)

# Heuristic function (A* / M*)
def heuristic(a, b):
    return geodesic(a, b).meters  # ใช้ระยะทาง geodesic เป็น heuristic