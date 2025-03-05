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
from function_2.mstar import *
from function_2.create_map_2 import *
from function_2.compare_agent import *

from function_2.comparison_table import *

from function.statistics import *
from function.graph import *

from static_var.station_location import station_locations



import functools
import time







# ดึงข้อมูลถนนจาก OpenStreetMap
# road = ox.graph_from_place("Lat Krabang, Bangkok, Thailand", network_type="all")
# ox.save_graphml(road, "lat_krabang_graph.graphml")

graph_file = "lat_krabang_graph.graphml"
if os.path.exists(graph_file):
    road = ox.load_graphml(graph_file)
else:
    # road = ox.graph_from_place("Lat Krabang, Bangkok, Thailand", network_type="all")
    road = ox.graph_from_place("Lat Krabang, Bangkok", network_type="all")
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
    max_time_step = st.session_state.max_time_step
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

    # วนลูปผ่านทุกคู่ของตำแหน่งเริ่มต้นและปลายทางของ agent
    for start_pos, dest_pos in zip(start_positions, destination_positions):
        print(f"A*: Agent เริ่มที่ {start_pos} และต้องไปที่ {dest_pos}")

        # จัดเรียงสถานีทั้งหมดตามระยะทางจาก agent (ใกล้ไปไกล)
        # เพราะเราต้องการเช็คสถานีที่ใกล้ที่สุดก่อน ถ้าไม่มีจักรยานก็ไปเช็คสถานีที่ใกล้ถัดไป
        sorted_stations = sorted(station_locations, key=lambda s: heuristic(start_pos, s))


        # ค้นหาสถานีที่มีจักรยานเหลืออยู่ โดยเริ่มจากสถานีที่ใกล้ที่สุดก่อน
        start_station = None
        for station in sorted_stations:
            station_index = station_locations.index(station)  # หา index ของสถานีในลิสต์ station_locations
            if initial_station_bikes[station_index] > 0:      # ตรวจสอบว่าสถานีนี้มีจักรยานเหลืออยู่หรือไม่
                start_station = station  # ถ้ามีจักรยาน ใช้สถานีนี้เป็นสถานีเริ่มต้น
                break


        
        # ถ้าไม่มีสถานีไหนมีจักรยานเลย เลือกสถานีที่ใกล้ที่สุดเป็นสถานีเริ่มต้น (อาจจะต้องรอจักรยานมาเพิ่ม )
        # ! แปลกๆ 
        if start_station is None:
            start_station = sorted_stations[0]



        # min จะหาสถานีใน station_locations ที่มีค่า heuristic(dest_pos, s) น้อยที่สุด (คือสถานีที่ใกล้จุดหมายปลายทางที่สุด) สถานีนั้นจะถูกเก็บไว้ในตัวแปร end_station
        end_station = min(station_locations, key=lambda s: heuristic(dest_pos, s))



        # ขั้นตอน สร้างเส้นทาง: จุดเริ่มต้น → สถานีเช่า → (เส้นทาง A* ระหว่างสถานี) → จุดหมายปลายทาง
        # 1. จุดเริ่มต้น → สถานีเช่า
        # complete_path : list ที่เก็บเส้นทางของ agent ตั้งแต่เริ่มต้น จุดแรกคือ ตำแหน่งเริ่มต้นของ agent, จุดที่สองคือ สถานีเช่าจักรยาน (start_station) ที่เลือกไว้
        complete_path = [start_pos]
        # complete_path: เส้นทางสมบูรณ์ของ agent (รวมจุดเริ่มต้น, สถานีเช่า, สถานีคืน, และจุดหมายปลายทาง)



        # 2. สถานีเช่า → สถานีคืน (ด้วย A* algorithm)
         # ใช้เส้นทางจริงจาก OpenStreetMap (หรือแผนที่จำลอง) เพื่อหาเส้นทางระหว่างสถานี
        osm_path = find_route_osm(road, start_station, end_station, 'a_star')  
        complete_path.extend(osm_path)  # เพิ่มเส้นทางระหว่างสถานีเข้าไปในเส้นทางสมบูรณ์



        # 3. สถานีคืน → จุดหมายปลายทาง
        # เพิ่มจุดหมายปลายทางเข้าไปในเส้นทางสมบูรณ์
        complete_path.append(dest_pos)



        # เพิ่มเส้นทางสมบูรณ์ของ agent คนนี้เข้าไปในลิสต์ของเส้นทางทั้งหมด
        full_paths_a_star.append(complete_path)


        # คำนวณเวลาที่ใช้ในแต่ละช่วงของเส้นทาง (segments)
        # boundaries คือลิสต์ของเวลาที่ agent ถึงแต่ละจุดในเส้นทาง (ในหน่วย time step)
        boundaries = compute_segment_boundaries(complete_path, t_per_meter, simulation_time_step)
        # เช่น ถ้า complete_path = [A, B, C, D] และ boundaries = [0, 10, 20, 30] หมายความว่า: ที่เวลา 0: agent อยู่ที่จุด A , ที่เวลา 10: agent ถึงจุด B 



        # active_steps ตัวแปรนี้เก็บจำนวน time steps ที่ agent ใช้ในการเดินทางทั้งหมด (ตั้งแต่เริ่มต้นจนถึงจุดหมายปลายทาง)
        active_steps = boundaries[-1] # boundaries[-1] ดึงค่าสุดท้ายในลิสต์ ซึ่งคือเวลาที่ agent ถึงจุดสุดท้ายของเส้นทาง (จุดหมายปลายทาง)



        # หาก active_steps เกิน max_time_step ให้ถือว่าเดิน max_time_step
        # (คือ agent จะไม่สามารถเดินทางถึงจุดหมายได้ทันในการจำลอง)
        if active_steps > max_time_step:
            active_steps = max_time_step
        agent_grid_steps.append(active_steps) # เก็บจำนวน steps ของ agent คนนี้ ✨


        # กำหนดเวลาเช่าจักรยาน = เวลาที่ agent ถึงสถานีเช่า (boundaries[1])
        # ถ้าเวลาเกิน max_time_step ให้ใช้ max_time_step - 1 แทน
        rental_time = boundaries[1] if boundaries[1] < max_time_step else max_time_step - 1

        # กำหนดเวลาคืนจักรยาน = เวลาที่ agent ถึงสถานีคืน (boundaries[-2])
        # ถ้าเวลาเกิน max_time_step ให้ใช้ max_time_step - 1 แทน
        return_time = boundaries[-2] if boundaries[-2] < max_time_step else max_time_step - 1

        # บันทึกเหตุการณ์การเช่าและคืนจักรยาน
        station_index = station_locations.index(start_station)  # index ของสถานีเช่า
        end_station_index = station_locations.index(end_station)  # index ของสถานีคืน
        rental_events.append((rental_time, station_index))  # เพิ่มเหตุการณ์เช่า (เวลา, สถานี)
        return_events.append((return_time, end_station_index))  # เพิ่มเหตุการณ์คืน (เวลา, สถานี)


        # ปรับจำนวนจักรยานในสถานีทันทีที่มีการเช่าและคืน
        # ลดจำนวนจักรยานที่สถานีเช่า
        initial_station_bikes[station_index] -= 1
        # เพิ่มจำนวนจักรยานที่สถานีคืน
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
                                 destination_positions)
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
            destination_positions
        )
        with st.container():
            components.html(traffic_map_cbs._repr_html_(), height=600)
    else:
        st.write("CBS could not find a valid solution with the given constraints")



    # 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°
    # Run M* algorithm

    # # สร้างกราฟสำหรับ M* โดยเฉพาะ
    # road_graph = nx.Graph()
    
    # # เพิ่มโหนดจาก OSM road network
    # for node, data in road.nodes(data=True):
    #     road_graph.add_node(node)
    
    # # เพิ่ม edges
    # for u, v, data in road.edges(data=True):
    #     # ใช้ weight เป็น length ถ้ามี
    #     if 'length' in data:
    #         road_graph.add_edge(u, v, weight=data['length'], length=data['length'])
    #     else:
    #         # ถ้าไม่มี length ให้คำนวณจากพิกัด
    #         u_coords = (road.nodes[u]['y'], road.nodes[u]['x']) if 'y' in road.nodes[u] else None
    #         v_coords = (road.nodes[v]['y'], road.nodes[v]['x']) if 'y' in road.nodes[v] else None
            
    #         if u_coords and v_coords:
    #             try:
    #                 distance = geodesic(u_coords, v_coords).meters
    #                 road_graph.add_edge(u, v, weight=distance, length=distance)
    #             except:
    #                 road_graph.add_edge(u, v, weight=1, length=1)
    #         else:
    #             road_graph.add_edge(u, v, weight=1, length=1)
    
    # # แปลงตำแหน่งเริ่มต้นและเป้าหมายเป็นโหนดที่มีในกราฟ
    # temp_start_positions = []
    # temp_goal_positions = []

    # for start_pos in start_positions:
    #     try:
    #         start_node = ox.distance.nearest_nodes(road, start_pos[1], start_pos[0])
    #         temp_start_positions.append(start_node)
    #     except Exception as e:
    #         print(f"Error finding nearest node for start position {start_pos}: {e}")
    #         continue
            
    # for goal_pos in destination_positions:
    #     try:
    #         goal_node = ox.distance.nearest_nodes(road, goal_pos[1], goal_pos[0])
    #         temp_goal_positions.append(goal_node)
    #     except Exception as e:
    #         print(f"Error finding nearest node for goal position {goal_pos}: {e}")
    #         continue

    # # ตรวจสอบว่ามีตำแหน่งเริ่มต้นและเป้าหมายที่ถูกต้องหรือไม่
    # if len(temp_start_positions) == 0 or len(temp_goal_positions) == 0:
    #     st.write("ไม่สามารถหาโหนดที่เหมาะสมสำหรับตำแหน่งเริ่มต้นหรือเป้าหมายได้")
    # elif len(temp_start_positions) != len(temp_goal_positions):
    #     st.write("จำนวนตำแหน่งเริ่มต้นและเป้าหมายไม่เท่ากัน")
    # else:
    #     # เรียกใช้ M* algorithm
    #     m_star_paths, m_star_timelines, m_star_grid_steps = find_route_m_star(
    #         road_graph,
    #         temp_start_positions,
    #         temp_goal_positions,
    #         t_per_meter,
    #         simulation_time_step,
    #         max_time_step
    #     )
    
    # print("🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤🍤", m_star_paths)

    # if m_star_paths and len(m_star_paths) > 0:
    #     # Display grid steps for M*
    #     st.write("### M*: จำนวน Grid Steps ที่แต่ละ Agent เดิน")
    #     for agent_id, steps in m_star_grid_steps.items():
    #         st.write(f"Agent {agent_id+1}: {steps} grid steps")

    #     # แปลงเส้นทางจาก node ids เป็นพิกัด lat-lon
    #     full_paths_m_star = []
    #     agents_positions_m_star = []

    #     for agent_id in sorted(m_star_paths.keys()):
    #         path = m_star_paths[agent_id]
    #         full_path = []

    #         for node in path:
    #             try:
    #                 full_path.append((road.nodes[node]['y'], road.nodes[node]['x']))
    #             except:
    #                 # ใช้ node เดิมถ้ามันเป็นพิกัดอยู่แล้ว
    #                 if isinstance(node, tuple):
    #                     full_path.append(node)

    #         full_paths_m_star.append(full_path)
    #         agents_positions_m_star.append(m_star_timelines[agent_id])
        
    #     # Create M* visualization
    #     st.write("### M* Traffic Simulation Map")
    #     traffic_map_m_star = create_map(
    #         full_paths_m_star,
    #         agents_positions_m_star,
    #         station_locations,
    #         [[num_bikes_per_station]*len(station_locations) for _ in range(max_time_step)],
    #         destination_positions
    #     )
    #     with st.container():
    #         components.html(traffic_map_m_star._repr_html_(), height=600)
    # else:
    #     st.write("M* could not find a valid solution with the given constraints")



    # !🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°
    # if cbs_solution:
    #     show_statistics(agent_grid_steps, list(cbs_grid_steps.values()))
    # show_summary_chart_plotly(agent_grid_steps, list(cbs_grid_steps.values()))
    # show_comparison_table(agent_grid_steps, cbs_grid_steps)
    # compare_agent(
    #     agent_grid_steps,  # จำนวน grid steps ของ A*
    #     cbs_grid_steps,    # จำนวน grid steps ของ CBS
    #     start_positions,   # ตำแหน่งเริ่มต้นของ agent
    #     destination_positions,  # ตำแหน่งปลายทางของ agent
    #     station_locations  # ตำแหน่งของสถานีทั้งหมด
    # )

  

# 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°



# สร้าง Sidebar
with st.sidebar:
    st.header("Configuration")
    st.number_input("Max Time Steps:", min_value=1, value=100, key='max_time_step')
    st.number_input("Number of Bicycles in the Station:", min_value=1, value=10, key='num_bikes')
    option = st.radio("Population", ("Total Population", "Random Population Range"))
    with st.container():
        if option == "Total Population":
            value = st.number_input("Total Population:", min_value=1, value=5, key='num_persons')
        else:
            value = st.slider("Random Population Range", 0, 200, 10)

    col1, col2, col3 = st.sidebar.columns([1, 2, 1])
    with col2:
        run_sim_bttn = st.button("Run Simulation")

# 5️⃣ ส่วนอินพุต Streamlit
st.title("Bicycle Sharing Simulation")
st.write("Fill in the simulation details and press Run simulation to view the simulation results.")

if run_sim_bttn:
    run_simulation()



