# 1️⃣ ส่วน Import Library
import folium
import streamlit as st
import random
import heapq
import json
import time
import streamlit.components.v1 as components
import math
import streamlit as st

import osmnx as ox
import os

import networkx as nx

from geopy.distance import geodesic 

from function.distance_real import *
from function_2.cbs_alogo import *
from function_2.osm_route import *
from function_2.create_map_2 import *
from function_2.compare_agent import *

from function_2.comparison_table import *

from function.statistics import *
from function.graph import *

from static_var.station_location import station_locations



import functools
import time



from function_2.m_star_Fame import *




# ดึงข้อมูลถนนจาก OpenStreetMap
# road = ox.graph_from_place("Lat Krabang, Bangkok, Thailand", network_type="all")
# ox.save_graphml(road, "lat_krabang_graph.graphml")

graph_file = "lat_krabang_graph.graphml"
if os.path.exists(graph_file):
    road = ox.load_graphml(graph_file)
else:
    # road = ox.graph_from_place("Lat Krabang, Bangkok, Thailand", network_type="all")
    road = ox.graph_from_place("Lat Krabang, Bangkok, Thailand", network_type="walk")
    ox.save_graphml(road, graph_file)







# def heuristic(a, b):
#     return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

def heuristic(a, b):
    return geodesic(a, b).meters  # ใช้ระยะทาง geodesic เป็น heuristic

# def heuristic(a, b):
#     return geodesic(a, b).meters


# 💌🧚‍♀️💗🌨🥡🍥 💌🧚 new 🥡🍥 💌🧚‍♀️💗🌨🥡🍥
def create_station_graph(station_locations):
    """
    ⛰🌿🌻☀️☁️
    สร้าง NetworkX graph object สำหรับเชื่อมต่อระหว่างสถานี
    
    Args:
        station_locations (list): List of station coordinates (lat, lon)
    
    Returns:
        nx.Graph: Complete graph connecting all stations
        
    ⛰🌿🌻☀️☁️
    """
    G = nx.Graph()

   
    
    # เพิ่ม nodes (สถานี)
    for station in station_locations:
        G.add_node(station)
    
    # เพิ่ม edges (เส้นทางระหว่างสถานี)
    for i, station1 in enumerate(station_locations):
        for station2 in station_locations[i+1:]:  # Avoid duplicate edges
            distance = geodesic(station1, station2).meters
            G.add_edge(station1, station2, weight=distance, length=distance)
    
    return G
# 💌🧚‍♀️💗🌨🥡🍥 💌🧚‍♀️💗🌨🥡🍥 💌🧚‍♀️💗🌨🥡🍥


# 🧪🧪🧪 ใช้ astar_path ของ networkX 🧪🧪🧪
def a_star_search(graph, start, goal):
    """
    ค้นหาเส้นทางด้วย A* algorithm โดยใช้ NetworkX
    """
    try:
        # ใช้ astar_path จาก NetworkX
        path = nx.astar_path(graph, start, goal, weight='length')
        return path
    except nx.NetworkXNoPath:
        print(f"ไม่พบเส้นทางระหว่าง {start} และ {goal}")
        return []






# 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°
# 4️⃣ ฟังก์ชัน run_simulation() → รันการจำลอง
def run_simulation():
    num_persons = st.session_state.num_persons
    max_time_step = st.session_state.max_time_step_input
    num_bikes_per_station = st.session_state.num_bikes


    # ตั้งค่าความเร็วเดิน (เวลาต่อเมตร) และ simulation time step (วินาที)
    t_per_meter = 0.1           # กำหนดเวลา (วินาที) ที่ใช้เดิน 1 เมตร
    simulation_time_step = 1    # 1 วินาทีต่อ time step


    # map boundaries
    min_lat = min(x[0] for x in station_locations)
    max_lat = max(x[0] for x in station_locations)
    min_lon = min(x[1] for x in station_locations)
    max_lon = max(x[1] for x in station_locations)

    

    # สุ่มตำแหน่งเริ่มต้นและปลายทางของ agent
    # ! ต้องมาเช็กตรงนี้ว่า การเกิด ไม่ควรตรงกับพื้นที่ที่เดินไม่ได้
    start_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]
    destination_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]

    # สร้างกราฟสำหรับ A* Search ระหว่างสถานี
    graph = create_station_graph(station_locations)

    # กำหนดจำนวนจักรยานเริ่มต้นในแต่ละสถานี
    initial_station_bikes = [num_bikes_per_station] * len(station_locations)

    # 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°
    #! ส่วน A* Alogorithm
    full_paths_a_star = []  # เก็บเส้นทางทั้งหมดของทุก agent ที่คำนวณด้วยอัลกอริทึม A*
    rental_events = []      # เก็บเหตุการณ์การเช่าจักรยาน (เวลาที่เช่า, สถานีที่เช่า)
    return_events = []      # เก็บเหตุการณ์การคืนจักรยาน (เวลาที่คืน, สถานีที่คืน)
    agent_grid_steps = []   # เก็บจำนวน grid steps ที่แต่ละ agent เดินจริง 

    for start_pos, dest_pos in zip(start_positions, destination_positions):
        print(f"A*: Agent เริ่มที่ {start_pos} และต้องไปที่ {dest_pos}")

        # จัดเรียงสถานีทั้งหมดตามระยะทางจาก agent (ใกล้ไปไกล)
        sorted_stations = sorted(station_locations, key=lambda s: heuristic(start_pos, s))

        # ค้นหาสถานีที่มีจักรยานเหลืออยู่ โดยเริ่มจากสถานีที่ใกล้ที่สุดก่อน
        start_station = None
        for station in sorted_stations:
            station_index = station_locations.index(station)
            if initial_station_bikes[station_index] > 0:
                start_station = station
                break

        # ถ้าไม่มีสถานีไหนมีจักรยานเลย เลือกสถานีที่ใกล้ที่สุดเป็นสถานีเริ่มต้น
        if start_station is None:
            start_station = sorted_stations[0]

        # หาสถานีที่ใกล้จุดหมายปลายทางที่สุด
        end_station = min(station_locations, key=lambda s: heuristic(dest_pos, s))

        # สร้างเส้นทาง: จุดเริ่มต้น → สถานีเช่า → สถานีคืน → จุดหมายปลายทาง
        complete_path = [start_pos]

        # หาเส้นทางจากจุดเริ่มต้นไปยังสถานีเช่าจักรยาน
        osm_path_start = find_route_osm(road, start_pos, start_station, 'a_star')
        if osm_path_start:
            complete_path.extend(osm_path_start[1:])  # เพิ่มเส้นทางระหว่างจุดเริ่มต้นและสถานีเช่า

        # หาเส้นทางจากสถานีเช่าจักรยานไปยังสถานีคืนจักรยาน
        osm_path_end = find_route_osm(road, start_station, end_station, 'a_star')
        if osm_path_end:
            complete_path.extend(osm_path_end[1:])  # เพิ่มเส้นทางระหว่างสถานีเช่าและสถานีคืน

        # หาเส้นทางจากสถานีคืนจักรยานไปยังจุดปลายทาง
        osm_path_dest = find_route_osm(road, end_station, dest_pos, 'a_star')
        if osm_path_dest:
            complete_path.extend(osm_path_dest[1:])  # เพิ่มเส้นทางระหว่างสถานีคืนและจุดปลายทาง

        # เพิ่มเส้นทางสมบูรณ์ของ agent คนนี้เข้าไปในลิสต์ของเส้นทางทั้งหมด
        full_paths_a_star.append(complete_path)

        # คำนวณเวลาที่ใช้ในแต่ละช่วงของเส้นทาง (segments)
        boundaries = compute_segment_boundaries(complete_path, t_per_meter, simulation_time_step)

        # คำนวณจำนวน time steps ที่ agent ใช้ในการเดินทางทั้งหมด
        active_steps = boundaries[-1]
        if active_steps > max_time_step:
            active_steps = max_time_step
        agent_grid_steps.append(active_steps)

        # บันทึกเหตุการณ์การเช่าและคืนจักรยาน
        station_index = station_locations.index(start_station)
        end_station_index = station_locations.index(end_station)
        rental_events.append((boundaries[1], station_index))
        return_events.append((boundaries[-2], end_station_index))

        # ปรับจำนวนจักรยานในสถานี
        initial_station_bikes[station_index] -= 1
        initial_station_bikes[end_station_index] += 1



    st.write("### a_star: จำนวน Grid Steps ที่แต่ละ Agent เดิน")
    for idx, steps in enumerate(agent_grid_steps):
        st.write(f"Agent {idx+1}: {steps} grid steps")


    # คำนวณตำแหน่งของ agent ในแต่ละ time step โดยใช้ compute_agent_timeline
    agents_positions_a_star = []
    for path in full_paths_a_star:
        timeline = compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_step)
        agents_positions_a_star.append(timeline)


    # ปรับปรุงจำนวนจักรยานในแต่ละสถานีตลอด timeline
    station_bikes_timeline = [[num_bikes_per_station] * len(station_locations) for _ in range(max_time_step)]
    for t in range(max_time_step):
        for rental_time, station_index in rental_events:
            if t >= rental_time:
                station_bikes_timeline[t][station_index] -= 1
        for return_time, station_index in return_events:
            if t >= return_time:
                station_bikes_timeline[t][station_index] += 1

    print("Station bikes at time 0:", station_bikes_timeline[0])
    print("Station bikes at final time:", station_bikes_timeline[-1])


    # กำหนด CSS
    map_style = """
    <style>
        .stVerticalBlock { width: 80% !important; }
        .st-emotion-cache-17vd2cm { width: 80% !important; }
        [data-testid="stAppViewContainer"] { }
        [data-testid="stIFrame"] { width: 80% !important; height: 650px !important; }
        [data-testid="stMainBlockContainer"] { width: 80% !important; max-width: 80% !important; }
    </style>
    """
    st.markdown(map_style, unsafe_allow_html=True)
    

    # ส่งข้อมูล A* ไปสร้าง map
    st.write("### A* Traffic Simulation Map")
    traffic_map_a_star = create_map(full_paths_a_star, agents_positions_a_star, station_locations, 
                                 [[num_bikes_per_station]*len(station_locations) for _ in range(max_time_step)],
                                 destination_positions, road)
    with st.container():
        components.html(traffic_map_a_star._repr_html_(), height=600)



    # 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°
    print("🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°")
    # Run CBS algorithm
    print("Starting CBS...")
    cbs_solution, cbs_timelines, cbs_grid_steps = cbs_search(
        graph,
        start_positions,
        destination_positions,
        station_locations,
        t_per_meter,
        simulation_time_step,
        max_time_step,
        road
    )
    print("CBS finished!")

    # if cbs_solution:
    # Display grid steps for CBS
    st.write("### CBS: จำนวน Grid Steps ที่แต่ละ Agent เดิน")
    
    if cbs_solution:
        for agent_id, steps in cbs_grid_steps.items():
            st.write(f"Agent {agent_id+1}: {steps} grid steps")
        
        # Convert CBS solution to format needed for visualization
        full_paths_cbs = list(cbs_solution.values())
        agents_positions_cbs = list(cbs_timelines.values())
        
        # Create CBS visualization
        st.write("### CBS Traffic Simulation Map")
        traffic_map_cbs = create_map(
            full_paths_cbs,
            agents_positions_cbs,
            station_locations,
            [[num_bikes_per_station]*len(station_locations) for _ in range(max_time_step)],
            destination_positions, road
        )
        with st.container():
            components.html(traffic_map_cbs._repr_html_(), height=600)
    else:
        st.write("CBS could not find a valid solution with the given constraints")




    print("🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°")
    m_star_solution, m_star_timelines, m_star_grid_steps = m_star_search(
        graph,
        start_positions,
        destination_positions,
        station_locations,
        t_per_meter,
        simulation_time_step,
        max_time_step,
        road
    )
    print("M* finished!")

    # Display M* results
    st.write("### M*: จำนวน Grid Steps ที่แต่ละ Agent เดิน")
    for agent_id, steps in m_star_grid_steps.items():
        st.write(f"Agent {agent_id+1}: {steps} grid steps")

    # Visualize M* results
    st.write("### M* Traffic Simulation Map")
    traffic_map_m_star = create_map(
        list(m_star_solution.values()),
        list(m_star_timelines.values()),
        station_locations,
        [[num_bikes_per_station]*len(station_locations) for _ in range(max_time_step)],
        destination_positions, road
    )
    with st.container():
        components.html(traffic_map_m_star._repr_html_(), height=600)





    # def show_statistics(agent_grid_steps_abs, agent_grid_steps_cbs):
    # print("list(m_star_grid_steps.values())", list(cbs_grid_steps.values()))
    # print("list(m_star_grid_steps.values())", list(m_star_grid_steps.values()))
    show_statistics(agent_grid_steps, list(cbs_grid_steps.values()),  list(m_star_grid_steps.values()))

    # def show_summary_chart_plotly(agent_grid_steps_abs, agent_grid_steps_cbs):
    show_summary_chart_plotly(agent_grid_steps, list(cbs_grid_steps.values()), list(m_star_grid_steps.values()))

    # # def show_comparison_table(agent_grid_steps_a_star, cbs_grid_steps):
    show_comparison_table(agent_grid_steps, cbs_grid_steps, m_star_grid_steps)


    # # def compare_agent(agent_grid_steps_a_star, cbs_grid_steps, start_positions, destination_positions, station_locations):
    compare_agent(agent_grid_steps, cbs_grid_steps, m_star_grid_steps, start_positions, destination_positions, station_locations)












# 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°
if "rerun_done" not in st.session_state:
    if "max_time_step_input" in st.session_state:
        del st.session_state["max_time_step_input"]
        st.session_state["rerun_done"] = True  # ป้องกันไม่ให้ rerun ซ้ำเรื่อยๆ
        st.rerun()


# สร้าง Sidebar
with st.sidebar:
    st.header("Configuration")
    st.number_input("Max Time Steps:", min_value=1, value=500, key='max_time_step_input')
    st.number_input("Number of Bicycles in the Station:", min_value=1, value=10, key='num_bikes')
    option = st.radio("Population", ("Total Population", "Random Population Range"))
    # with st.container():
    #     if option == "Total Population":
    #         # ใช้จำนวนประชากรที่กำหนดไว้แน่นอน
    #         total_population = st.number_input("Total Population:", min_value=1, value=5, key='num_persons')
    #         if 'population' not in st.session_state:
    #             st.session_state.population = total_population
    #         else:
    #             st.session_state.population = total_population
    #     else:
    #         # เลือกช่วงประชากรและสุ่มค่า
    #         min_pop = st.number_input("Minimum Population:", min_value=1, value=5, key='min_pop')
    #         max_pop = st.number_input("Maximum Population:", min_value=min_pop, value=50, key='max_pop')
            
    #         if st.button("Generate Random Population", key='gen_random_pop'):
    #             random_pop = random.randint(min_pop, max_pop)
    #             st.session_state.population = random_pop
    #             st.success(f"Random population generated: {random_pop}")

    # แสดง UI ตามตัวเลือกที่เลือก
    if option == "Total Population":
        # แบบกำหนดจำนวนแน่นอน
        st.session_state.population = st.number_input("Total Population:", min_value=1, value=5, key='num_persons')
    else:
        # แบบสุ่มในช่วงที่กำหนด
        min_pop = st.number_input("Minimum Population:", min_value=1, value=5, key='min_pop')
        max_pop = st.number_input("Maximum Population:", min_value=min_pop, value=50, key='max_pop')
        
        if st.button("Generate Random Population", key='gen_random_pop'):
            random_pop = random.randint(min_pop, max_pop)
            st.session_state.population = random_pop
            st.success(f"Random population generated: {random_pop}")
            
        # แสดงค่าประชากรปัจจุบัน (กรณีที่เคยสุ่มแล้ว)
        if option == "Random Population Range":
            st.write(f"Current population: {st.session_state.population}")

    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:  
        run_sim_bttn = st.button("Run Simulation")

# 5️⃣ ส่วนอินพุต Streamlit
st.title("Bicycle Sharing Simulation")
st.write("Fill in the simulation details and press Run simulation to view the simulation results.")

if run_sim_bttn:
    run_simulation()



