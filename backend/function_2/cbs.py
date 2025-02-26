# 1️⃣ ส่วน Import Library
import folium
import streamlit as st
import random
import heapq
import json
import time
import streamlit.components.v1 as components
import math
import osmnx as ox
import networkx as nx
from geopy.distance import geodesic 

from function.distance_real import *
from function_2.cbs import *
from function_2.osm_route import *
from function_2.mstar import *
from function_2.create_map_2 import *


from function.statistics import *
from function.graph import *




# ดึงข้อมูลถนนจาก OpenStreetMap
road = ox.graph_from_place("Lat Krabang, Bangkok, Thailand", network_type="all")

# 💌🧚‍♀️💗🌨🥡🍥 💌🧚 new 🥡🍥 💌🧚‍♀️💗🌨🥡🍥

def add_temporary_node(graph, point):
    """ ⛰🌿🌻☀️☁️
    Add a temporary node to a NetworkX graph and connect it to its nearest neighbor
    
    Args:
        graph (nx.Graph): NetworkX graph object
        point (tuple): Coordinates of the new point (lat, lon)
    
    Returns:
        nx.Graph: Copy of graph with new temporary node added
    ⛰🌿🌻☀️☁️ """

    # Create a copy of the graph
    temp_graph = graph.copy()
    
    # If point already exists as a node, return the graph as is
    if point in temp_graph.nodes():
        return temp_graph

    # หา node ใกล้เคียงที่สุด
    nearest = min(temp_graph.nodes(), key=lambda node: geodesic(point, node).meters)

    # คำนวณระยะทางไป node นั้น
    distance = geodesic(point, nearest).meters

    # Add new node and edge
    temp_graph.add_node(point)
    temp_graph.add_edge(point, nearest, weight=distance, length=distance)

    return temp_graph

# 💌🧚‍♀️💗🌨🥡🍥 💌🧚‍♀️💗🌨🥡🍥 💌🧚‍♀️💗🌨🥡🍥

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

# 2️⃣ ฟังก์ชันช่วยเหลือสำหรับ A* Search
def heuristic(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)


# 💌🧚‍♀️💗🌨🥡🍥 💌🧚 CBS 🥡🍥 💌🧚‍♀️💗🌨🥡🍥

# CBS Node class to represent a node in the constraint tree
class CBSNode:
    def __init__(self, constraints=None, solution=None, cost=0):
        self.constraints = constraints or {}  # Dictionary of agent_id: [(vertex/edge, timestep)]
        self.solution = solution or {}        # Dictionary of agent_id: path
        self.cost = cost                     # Sum of individual path costs
        self.grid_steps = {}                 # Dictionary to store grid steps for each agent

    def __lt__(self, other):
        # เปรียบเทียบโดยใช้ cost
        return self.cost < other.cost
    
# Function to detect conflicts between two agents' paths
def detect_conflicts(path1, path2):
    """
    Detects vertex and edge conflicts between two paths
    Returns list of conflicts: (timestep, type, location)
    """
    conflicts = []
    min_len = min(len(path1), len(path2))
    
    # Check vertex conflicts (agents at same location at same time)
    for t in range(min_len):
        if path1[t] == path2[t]:
            conflicts.append((t, 'vertex', path1[t]))
    
    # Check edge conflicts (agents swap positions)
    for t in range(min_len - 1):
        if path1[t] == path2[t+1] and path1[t+1] == path2[t]:
            conflicts.append((t, 'edge', (path1[t], path1[t+1])))
    
    return conflicts

def calculate_grid_steps(path, t_per_meter, simulation_time_step, max_time_steps):
    """
    Calculate the actual number of grid steps an agent takes along its path
    """
    # Calculate segment boundaries
    boundaries = compute_segment_boundaries(path, t_per_meter, simulation_time_step)
    
    # Get the total number of steps (last boundary)
    total_steps = boundaries[-1]
    
    # If total steps exceeds max_time_steps, cap it
    return min(total_steps, max_time_steps)

def find_path_with_constraints(graph, start, goal, constraints, t_per_meter, simulation_time_step):
    """
    Modified A* search that respects temporal constraints
    """
    open_set = [(0, start, 0)]  # (f_score, node, timestep)
    came_from = {}
    g_score = {(start, 0): 0}
    f_score = {(start, 0): heuristic(start, goal)}
    
    while open_set:
        current_f, current_node, t = heapq.heappop(open_set)
        
        if current_node == goal:
            path = []
            current_state = (current_node, t)
            while current_state in came_from:
                path.append(current_state[0])
                current_state = came_from[current_state]
            path.append(start)
            return path[::-1]
        
        # ⛰🌿🌻☀️☁️Use NetworkX methods to get neighbors⛰🌿🌻☀️☁️
        for neighbor in graph.neighbors(current_node):
            next_t = t + 1
            
            # Check if this move violates any constraints
            violates_constraint = False
            # Check vertex constraints (node, timestep)
            if (neighbor, next_t) in constraints:
                violates_constraint = True
            
            # Check edge constraints (from_node, to_node, timestep)
            if (current_node, neighbor, t) in constraints:
                violates_constraint = True
                
            if not violates_constraint:
                # ⛰🌿🌻☀️☁️ Get edge weight using NetworkX get_edge_data ⛰🌿🌻☀️☁️
                edge_data = graph.get_edge_data(current_node, neighbor)
                edge_weight = edge_data['weight'] if edge_data else 1

                neighbor_state = (neighbor, next_t)
                tentative_g_score = g_score[(current_node, t)] + edge_weight
                
                if neighbor_state not in g_score or tentative_g_score < g_score[neighbor_state]:
                    came_from[neighbor_state] = (current_node, t)
                    g_score[neighbor_state] = tentative_g_score
                    f_score[neighbor_state] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor_state], neighbor, next_t))
    
    return None  # No path found

def cbs_search(graph, start_positions, destination_positions, station_locations, t_per_meter, simulation_time_step, max_time_steps):
    """
    Main CBS algorithm implementation with grid steps tracking
    """
    root = CBSNode()

    # ⛰🌿🌻☀️☁️ สร้าง temporary graph ที่รวมจุดเริ่มต้นและจุดหมายของทุก agent ⛰🌿🌻☀️☁️
    temp_graph = graph.copy()

    # ⛰🌿🌻☀️☁️ เพิ่มจุดเริ่มต้นและจุดหมายของทุก agent เข้าไปในกราฟ ⛰🌿🌻☀️☁️
    for start, goal in zip(start_positions, destination_positions):
        temp_graph = add_temporary_node(temp_graph, start)
        temp_graph = add_temporary_node(temp_graph, goal)
    
    # Find initial paths for all agents ignoring conflicts
    for agent_id, (start, goal) in enumerate(zip(start_positions, destination_positions)):
        # Find nearest stations for pickup and dropoff
        start_station = min(station_locations, key=lambda s: heuristic(start, s))
        end_station = min(station_locations, key=lambda s: heuristic(goal, s))


        # ⛰🌿🌻☀️☁️ Create complete path using OSM ⛰🌿🌻☀️☁️
        # Create complete path using OSM
        path = []
        # 1. Start position to start station
        path.append(start)
        path.append(start_station)
        
        # 2. Route between stations using OSM
        osm_path = find_route_osm(road, start_station, end_station, 'cbs')
        if osm_path:
            path.extend(osm_path[1:])  # Skip first point as it's already added
        
        # 3. End station to goal
        path.append(goal)
        
        root.solution[agent_id] = path
        # Calculate and store grid steps for this agent
        root.grid_steps[agent_id] = calculate_grid_steps(path, t_per_meter, simulation_time_step, max_time_steps)
    
    # Initialize priority queue with root node
    open_list = [root]
    
    while open_list:
        node = heapq.heappop(open_list)
        
        # Convert paths to timelines for conflict detection
        agent_timelines = {}
        for agent_id, path in node.solution.items():
            timeline = compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_steps)
            agent_timelines[agent_id] = timeline
        
        # Find conflicts between all pairs of agents
        conflicts = []
        for i in range(len(agent_timelines)):
            for j in range(i + 1, len(agent_timelines)):
                conflicts.extend(detect_conflicts(agent_timelines[i], agent_timelines[j]))
        
        if not conflicts:
            return node.solution, agent_timelines, node.grid_steps
        
        # Handle first conflict
        conflict = conflicts[0]
        timestep, conflict_type, location = conflict
        
        # Create child nodes with new constraints
        for agent_id in range(2):  # Create two children with alternative constraints
            new_constraints = {k: v.copy() for k, v in node.constraints.items()}
            if agent_id not in new_constraints:
                new_constraints[agent_id] = set()
            
            if conflict_type == 'vertex':
                new_constraints[agent_id].add((tuple(location), timestep))
            else:  # edge conflict
                new_constraints[agent_id].add((tuple(location[0]), tuple(location[1]), timestep))
            
            child = CBSNode(new_constraints)
            
            # Find new path for constrained agent
            new_path = find_path_with_constraints(
                temp_graph,  # ใช้ temp_graph แทน graph
                start_positions[agent_id],
                destination_positions[agent_id],
                new_constraints[agent_id],
                t_per_meter,
                simulation_time_step
            )
            
            if new_path:
                child.solution = node.solution.copy()
                child.solution[agent_id] = new_path
                child.cost = sum(len(path) for path in child.solution.values())
                child.grid_steps = node.grid_steps.copy()
                child.grid_steps[agent_id] = calculate_grid_steps(new_path, t_per_meter, simulation_time_step, max_time_steps)
                heapq.heappush(open_list, child)
    
    return None, None, None  # No solution found

# 💌🧚‍♀️💗🌨🥡🍥 💌🧚‍♀️💗🌨🥡🍥 💌🧚‍♀️💗🌨🥡🍥
