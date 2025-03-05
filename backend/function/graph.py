import streamlit as st
import matplotlib.pyplot as plt
import numpy as np
from geopy.distance import geodesic 

import plotly.express as px
import pandas as pd

from function.distance_real import *
from function_2.cbs_alogo import *
from function_2.osm_route import *
from function_2.mstar import *
from function_2.create_map_2 import *


from function.statistics import *
from function.graph import *

# สร้างข้อมูลตัวอย่างสำหรับกราฟ
def create_summary_chart(agent_grid_steps_abs, agent_grid_steps_cbs):
    # จำนวน agent
    num_agents = len(agent_grid_steps_abs)
    
    # สร้างกราฟแท่งเปรียบเทียบ ABS และ CBS
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # แท่งสำหรับ ABS
    ax.bar(np.arange(num_agents) - 0.2, agent_grid_steps_abs, width=0.4, label='ABS', color='blue')
    
    # แท่งสำหรับ CBS
    ax.bar(np.arange(num_agents) + 0.2, agent_grid_steps_cbs, width=0.4, label='CBS', color='orange')
    
    # ปรับแต่งกราฟ
    ax.set_xlabel('Agent')
    ax.set_ylabel('Grid Steps')
    ax.set_title('Comparison of Grid Steps: ABS vs CBS')
    ax.set_xticks(np.arange(num_agents))
    ax.set_xticklabels([f'Agent {i+1}' for i in range(num_agents)])
    ax.legend()
    
    return fig

# แสดงกราฟใน Streamlit
def show_summary_chart(agent_grid_steps_abs, agent_grid_steps_cbs):
    st.write("### Summary Chart: ABS vs CBS")
    fig = create_summary_chart(agent_grid_steps_abs, agent_grid_steps_cbs)
    st.pyplot(fig)


# สร้าง DataFrame สำหรับ plotly
def create_summary_dataframe(agent_grid_steps_abs, agent_grid_steps_cbs):
    num_agents = len(agent_grid_steps_abs)
    data = {
        'Agent': [f'Agent {i+1}' for i in range(num_agents)],
        'ABS': agent_grid_steps_abs,
        'CBS': agent_grid_steps_cbs
    }
    return pd.DataFrame(data)

# แสดงกราฟสรุปด้วย plotly
def show_summary_chart_plotly(agent_grid_steps_abs, agent_grid_steps_cbs):
    st.write("### Summary Chart: ABS vs CBS")
    df = create_summary_dataframe(agent_grid_steps_abs, agent_grid_steps_cbs)
    fig = px.bar(df, x='Agent', y=['ABS', 'CBS'], barmode='group', title='Comparison of Grid Steps: ABS vs CBS')
    st.plotly_chart(fig)




# def heuristic(a, b):
#     return geodesic(a, b).meters


# def heuristic(a, b):
#     return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


def heuristic(a, b):
    return geodesic(a, b).meters  # ใช้ระยะทาง geodesic เป็น heuristic
