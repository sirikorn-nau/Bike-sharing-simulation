# 1️⃣ ส่วน Import Library
import folium
import streamlit as st
import random
import heapq
import json
import time
import math

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
from app import *

from static_var.station_location import station_locations



import functools
import time


import heapq
import networkx as nx


def add_node_to_graph(graph, node, station_locations):
    """
    เพิ่มโหนดลงในกราฟและเชื่อมต่อกับสถานีที่ใกล้ที่สุด
    """
    if node not in graph:
        graph.add_node(node)
        nearest_station = min(station_locations, key=lambda s: heuristic(node, s))
        distance = heuristic(node, nearest_station)
        graph.add_edge(node, nearest_station, weight=distance, length=distance)
    return graph
# def a_star_search(graph, start, goal, exclude_pos=None):
#     """
#     A* search algorithm with option to exclude specific positions
#     """
#     if start not in graph or goal not in graph:
#         print(f"Error: Start or goal node not in graph. Start: {start}, Goal: {goal}")
#         return []
    
#     # Define heuristic function for A* (must accept two arguments: current node and target)
#     def heuristic_func(n, target):
#         # Calculate geodesic distance between coordinates
#         return geodesic(n, target).meters
    
#     # Define custom weight function that penalizes excluded positions
#     def weight_func(u, v, edge_data):
#         weight = edge_data.get('length', edge_data.get('weight', 1))
#         if exclude_pos and (u == exclude_pos or v == exclude_pos):
#             return weight * 1000  # Heavily penalize excluded position
#         return weight
    
#     try:
#         # NetworkX's astar_path expects heuristic function to take two arguments (current, target)
#         path = nx.astar_path(graph, start, goal, heuristic=heuristic_func, weight=weight_func)
#         return path
#     except nx.NetworkXNoPath:
#         print(f"ไม่พบเส้นทางระหว่าง {start} และ {goal}")
#         return []
def m_star_search(graph, start_positions, destination_positions, station_locations, t_per_meter, simulation_time_step, max_time_step, road):
    num_agents = len(start_positions)
    paths = {}
    timelines = {}
    grid_steps = {}
    collision_count = 0  # เพิ่มตัวนับการชนกัน
    
    # เริ่มต้นหาเส้นทางสำหรับแต่ละตัวแทน
    for agent_id in range(num_agents):
        start = start_positions[agent_id]
        goal = destination_positions[agent_id]

        # หาสถานีที่ใกล้ที่สุดจากจุดเริ่มต้นและปลายทาง
        start_station = min(station_locations, key=lambda s: heuristic(start, s))
        end_station = min(station_locations, key=lambda s: heuristic(goal, s))

        # หาเส้นทางจากจุดเริ่มต้นไปยังสถานีเริ่มต้น
        osm_path_start = find_route_osm(road, start, start_station, 'a_star')
        if not osm_path_start:
            print(f"Agent {agent_id}: No path found from start to start station")
            continue

        # หาเส้นทางจากสถานีเริ่มต้นไปยังสถานีปลายทาง
        osm_path_middle = find_route_osm(road, start_station, end_station, 'a_star')
        if not osm_path_middle:
            print(f"Agent {agent_id}: No path found from start station to end station")
            continue

        # หาเส้นทางจากสถานีปลายทางไปยังจุดปลายทาง
        osm_path_end = find_route_osm(road, end_station, goal, 'a_star')
        if not osm_path_end:
            print(f"Agent {agent_id}: No path found from end station to goal")
            continue

        # รวมเส้นทางทั้งหมด
        path = osm_path_start + osm_path_middle[1:] + osm_path_end[1:]
        paths[agent_id] = path
        timelines[agent_id] = compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_step)

        # คำนวณจำนวน time steps ที่ agent ใช้ในการเดินทางทั้งหมด
        boundaries = compute_segment_boundaries(path, t_per_meter, simulation_time_step)
        active_steps = boundaries[-1]
        if active_steps > max_time_step:
            active_steps = max_time_step
        grid_steps[agent_id] = active_steps
    
    # ตรวจสอบการชนกันและปรับปรุงเส้นทาง
    paths_changed = True
    max_iterations = 10  # ป้องกันการวนซ้ำไม่รู้จบ
    iteration = 0
    
    while paths_changed and iteration < max_iterations:
        paths_changed = False
        iteration += 1
        print(f"Iteration {iteration}")
        
        for t in range(max_time_step):
            collisions = detect_collisions(timelines, t)
            if not collisions:
                continue
                
            collision_count += len(collisions)
            print(f"Time {t}: Found {len(collisions)} collisions")
            
            for agent1, agent2 in collisions:
                print(f"Collision between Agent {agent1} and Agent {agent2} at time {t}")
                
                # บันทึกเส้นทางเดิมเพื่อตรวจสอบการเปลี่ยนแปลง
                old_path1 = paths[agent1].copy()
                old_path2 = paths[agent2].copy()
                
                # พยายามหลีกเลี่ยงการชนกัน
                new_path1 = avoid_collision(road, paths[agent1], paths[agent2], t)
                new_path2 = avoid_collision(road, paths[agent2], paths[agent1], t)
                
                # อัพเดทเส้นทางถ้ามีการเปลี่ยนแปลง
                if new_path1 and new_path1 != old_path1:
                    paths[agent1] = new_path1
                    timelines[agent1] = compute_agent_timeline(new_path1, t_per_meter, simulation_time_step, max_time_step)
                    boundaries = compute_segment_boundaries(new_path1, t_per_meter, simulation_time_step)
                    active_steps = boundaries[-1]
                    if active_steps > max_time_step:
                        active_steps = max_time_step
                    grid_steps[agent1] = active_steps
                    paths_changed = True
                    print(f"Updated path for Agent {agent1}: {len(old_path1)} -> {len(new_path1)} steps")
                    
                if new_path2 and new_path2 != old_path2:
                    paths[agent2] = new_path2
                    timelines[agent2] = compute_agent_timeline(new_path2, t_per_meter, simulation_time_step, max_time_step)
                    boundaries = compute_segment_boundaries(new_path2, t_per_meter, simulation_time_step)
                    active_steps = boundaries[-1]
                    if active_steps > max_time_step:
                        active_steps = max_time_step
                    grid_steps[agent2] = active_steps
                    paths_changed = True
                    print(f"Updated path for Agent {agent2}: {len(old_path2)} -> {len(new_path2)} steps")
    
    print(f"Total collisions detected: {collision_count}")
    print(f"Final grid steps:")
    for agent_id, steps in grid_steps.items():
        print(f"Agent {agent_id}: {steps} grid steps")
        
    return paths, timelines, grid_steps



def detect_collisions(timelines, t, collision_threshold=0.0001):
    """
    ตรวจสอบการชนกันระหว่างตัวแทนในเวลา t
    ปัญหา: ฟังก์ชัน detect_collisions ใช้ geodesic เพื่อคำนวณระยะทางระหว่างตำแหน่ง แต่ถ้าตำแหน่งไม่ถูกต้อง (เช่น ไม่ใช่ tuple (lat, lon) หรือมีค่า None) จะเกิดข้อผิดพลาด
    แก้ไข: ตรวจสอบรูปแบบข้อมูลของตำแหน่งก่อนคำนวณระยะทาง
    """

    collisions = []
    agents = list(timelines.keys())
    
    for i in range(len(agents)):
        if t not in timelines[agents[i]]:
            continue
            
        for j in range(i + 1, len(agents)):
            if t not in timelines[agents[j]]:
                continue
                
            pos1 = timelines[agents[i]][t]
            pos2 = timelines[agents[j]][t]
            
            # ตรวจสอบรูปแบบข้อมูลของตำแหน่ง
            if not isinstance(pos1, tuple) or not isinstance(pos2, tuple):
                print(f"Invalid position format: Agent {agents[i]} -> {pos1}, Agent {agents[j]} -> {pos2}")
                continue
                
            try:
                distance = geodesic(pos1, pos2).meters
                print(f"Time {t}: Distance between Agent {agents[i]} and Agent {agents[j]}: {distance} meters")
                if distance < collision_threshold:
                    print(f"COLLISION DETECTED at time {t} between Agent {agents[i]} and Agent {agents[j]}")
                    collisions.append((agents[i], agents[j]))
            except Exception as e:
                print(f"Error calculating distance: {e}")
                
    return collisions





def avoid_collision(road, path1, path2, collision_time):
    """
    ปรับปรุงเส้นทางเพื่อหลีกเลี่ยงการชนกัน
    ปัญหา: ฟังก์ชัน avoid_collision พยายามหาเส้นทางใหม่โดยใช้ a_star_search แต่ถ้าเส้นทางใหม่ไม่พบหรือไม่สั้นกว่าเส้นทางเดิม จะไม่มีการปรับปรุง
    แก้ไข: เพิ่มกลยุทธ์การหลีกเลี่ยงการชนกัน เช่น การรอหรือการเปลี่ยนเส้นทาง
    """

    if collision_time >= len(path1):
        return path1
    

    
    # กลยุทธ์ที่ 1: หาเส้นทางใหม่ที่หลีกเลี่ยงตำแหน่งที่ชนกัน
    collision_pos = path2[min(collision_time, len(path2)-1)]


    # หาเส้นทางใหม่โดยหลีกเลี่ยงตำแหน่งที่ชนกัน
    new_path = find_route_osm(road, path1[0], path1[-1], 'a_star', exclude_pos=collision_pos)
    if new_path and len(new_path) > 0:
        return new_path
    
    


    # ถ้าหาเส้นทางใหม่ไม่ได้ ให้ใช้กลยุทธ์ทีึ่ 2 การรอที่ตำแหน่งปัจจุบัน
    current_pos = path1[min(collision_time-1, len(path1)-1)] if collision_time > 0 else path1[0]
    wait_path = path1[:collision_time] + [current_pos] + path1[collision_time:]
    return wait_path