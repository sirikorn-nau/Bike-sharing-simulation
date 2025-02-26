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

from function_2.cbs_alogo import *

# 2️⃣ ฟังก์ชันช่วยเหลือสำหรับ A* Search
def heuristic(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)



# 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°
# M* Node class for search
class MStarNode:
    def __init__(self, positions, g_score=0, parent=None):
        self.positions = tuple(positions)  # Current positions of all agents
        self.g_score = g_score            # Cost from start to current
        self.parent = parent              # Parent node
        self.colliding_agents = set()     # Set of agents involved in collision

    def __lt__(self, other):
        return self.g_score < other.g_score

def m_star_search(graph, start_positions, goal_positions, t_per_meter, simulation_time_step, max_time_steps):
    num_agents = len(start_positions)

    # ตรวจสอบว่ามีตำแหน่งเริ่มต้นและเป้าหมายที่ถูกต้อง
    if num_agents == 0 or len(goal_positions) != num_agents:
        print("Invalid number of start/goal positions")
        return None, None, None
    
    # ตรวจสอบว่าตำแหน่งทั้งหมดอยู่ในกราฟ
    for pos in start_positions + goal_positions:
        if pos not in graph.nodes():
            print(f"Position {pos} not in graph")
            try:
                # พยายามหาโหนดที่ใกล้ที่สุด
                nearest = min(graph.nodes(), key=lambda node: heuristic(pos, node))
                print(f"Nearest node is {nearest}")
            except:
                print("Cannot find nearest node")
            return None, None, None
    
    # Helper function to check collisions between agents
    def check_collisions(positions):
        collisions = set()
        for i in range(num_agents):
            for j in range(i + 1, num_agents):
                if positions[i] == positions[j]:
                    collisions.add(i)
                    collisions.add(j)
        return collisions

    # Helper function to get neighbors for a specific agent
    def get_agent_neighbors(pos, agent_id):
        neighbors = list(graph.neighbors(pos))
        neighbors.append(pos)  # Allow waiting at current position
        return neighbors

    # Heuristic function (manhattan distance)
    def h_score(positions):
        return sum(heuristic(pos, goal_positions[i]) for i, pos in enumerate(positions))

    # Initialize start node
    start_node = MStarNode(start_positions)
    start_node.f_score = h_score(start_positions)

    # Priority queue for open set
    open_set = [start_node]
    closed_set = set()
    
    # Initialize path tracking
    came_from = {start_node.positions: None}
    g_score = {start_node.positions: 0}
    f_score = {start_node.positions: h_score(start_positions)}

    while open_set:
        current = heapq.heappop(open_set)
        
        # Check if goal reached
        if all(current.positions[i] == goal_positions[i] for i in range(num_agents)):
            # Reconstruct paths
            paths = {i: [] for i in range(num_agents)}
            node = current
            while node:
                for i in range(num_agents):
                    paths[i].insert(0, node.positions[i])
                node = node.parent

            # Convert paths to timelines and calculate grid steps
            timelines = {}
            grid_steps = {}
            for agent_id, path in paths.items():
                timeline = compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_steps)
                timelines[agent_id] = timeline
                grid_steps[agent_id] = len(timeline)

            return paths, timelines, grid_steps

        if current.positions in closed_set:
            continue

        closed_set.add(current.positions)

        # Generate neighbor states
        for agent_id in range(num_agents):
            if agent_id in current.colliding_agents:
                neighbor_positions = list(current.positions)
                current_pos = current.positions[agent_id]
                
                for next_pos in get_agent_neighbors(current_pos, agent_id):
                    neighbor_positions[agent_id] = next_pos
                    neighbor_tuple = tuple(neighbor_positions)
                    
                    if neighbor_tuple in closed_set:
                        continue

                    # Calculate new g_score
                    tentative_g_score = current.g_score + 1

                    if neighbor_tuple not in g_score or tentative_g_score < g_score[neighbor_tuple]:
                        # Create new node
                        neighbor_node = MStarNode(neighbor_positions, tentative_g_score, current)
                        
                        # Check for collisions
                        collisions = check_collisions(neighbor_positions)
                        neighbor_node.colliding_agents = collisions
                        
                        # Update scores
                        g_score[neighbor_tuple] = tentative_g_score
                        f_score[neighbor_tuple] = tentative_g_score + h_score(neighbor_positions)
                        
                        heapq.heappush(open_set, neighbor_node)

    return None, None, None  # No solution found

# Function to find route using M*
def find_route_m_star(graph, start_positions, goal_positions, t_per_meter, simulation_time_step, max_time_steps):
    try:
        # ตรวจสอบว่าโหนดเริ่มต้นและเป้าหมายอยู่ในกราฟหรือไม่
        valid_start_positions = []
        valid_goal_positions = []
        
        for i, (start, goal) in enumerate(zip(start_positions, goal_positions)):
            if start not in graph.nodes():
                print(f"Start position {start} for agent {i} not in graph. Skipping agent.")
                continue
                
            if goal not in graph.nodes():
                print(f"Goal position {goal} for agent {i} not in graph. Skipping agent.")
                continue
                
            valid_start_positions.append(start)
            valid_goal_positions.append(goal)
        
        if not valid_start_positions or not valid_goal_positions:
            print("No valid agent positions found. Cannot proceed with M* search.")
            return {}, {}, {}
            
        # เรียกใช้ m_star_search เพื่อหาเส้นทาง
        paths, timelines, grid_steps = m_star_search(
            graph, 
            valid_start_positions, 
            valid_goal_positions, 
            t_per_meter, 
            simulation_time_step, 
            max_time_steps
        )
        
        if paths is None:
            print("M* search could not find a solution")
            # ถ้าหาเส้นทางไม่ได้ ลองหาเส้นทางแยกสำหรับแต่ละ agent
            paths = {}
            timelines = {}
            grid_steps = {}
            
            for i, (start, goal) in enumerate(zip(valid_start_positions, valid_goal_positions)):
                try:
                    # ใช้ A* แทนสำหรับแต่ละ agent
                    path = a_star_search(graph, start, goal)
                    
                    if path:
                        paths[i] = path
                        timeline = compute_agent_timeline(path, t_per_meter, simulation_time_step, max_time_steps)
                        timelines[i] = timeline
                        grid_steps[i] = len(timeline)
                    else:
                        print(f"Could not find path for agent {i} from {start} to {goal}")
                        paths[i] = [start, goal]  # เส้นทางเริ่มต้นถึงเป้าหมายโดยตรง
                        timeline = [start] * max_time_steps  # คงตำแหน่งเริ่มต้น
                        timelines[i] = timeline
                        grid_steps[i] = 0
                except Exception as e:
                    print(f"Error finding path for agent {i}: {e}")
                    paths[i] = [start, goal]
                    timelines[i] = [start] * max_time_steps
                    grid_steps[i] = 0
            
            return paths, timelines, grid_steps
                
        # คงเส้นทางไว้ตามที่ได้จาก m_star_search
        return paths, timelines, grid_steps
        
    except Exception as e:
        print(f"Error in find_route_m_star: {e}")
        import traceback
        traceback.print_exc()
        return {}, {}, {}
# 🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°🪩🫧🍸🥂🫧✧˖°


#🍤🍤🍤🍤🍤🍤หาเส้นทางตามถนน osmnx🍤🍤🍤🍤🍤🍤
def find_route_osm(road, start_latlon, end_latlon, algorithm):
    # แปลงพิกัด latitude, longitude ให้เป็นโหนดที่ใกล้ที่สุดในกราฟถนน
    start_node = ox.distance.nearest_nodes(road, start_latlon[1], start_latlon[0])
    end_node = ox.distance.nearest_nodes(road, end_latlon[1], end_latlon[0])


    def get_edge_weight(current, neighbor):
        """Helper function to safely get edge weight"""
        edge_data = road.get_edge_data(current, neighbor)
        
        # Handle different edge data formats
        if isinstance(edge_data, dict):
            return edge_data.get('length', 1)
        elif isinstance(edge_data, set):
            # If it's a set, try to get the first item's length
            if edge_data:
                first_item = next(iter(edge_data))
                if isinstance(first_item, dict):
                    return first_item.get('length', 1)
            return 1
        elif isinstance(edge_data, list):
            # If it's a list, try to get the first item's length
            if edge_data:
                return edge_data[0].get('length', 1)
        return 1  # Default weight if no length found


    # 📌 เลือกอัลกอริธึมที่ใช้
    if algorithm == 'a_star':
        # Use A* algorithm
        try:
            route = nx.astar_path(road, start_node, end_node, weight='length')
        except nx.NetworkXNoPath:
            print(f"A*: No path found between {start_latlon} and {end_latlon}")
            return []
            
    elif algorithm == 'cbs':
        # Use CBS-specific pathfinding
        try:
            # Initialize priority queue with starting node
            open_set = [(0, start_node)]
            came_from = {}
            g_score = {node: float('inf') for node in road.nodes}
            g_score[start_node] = 0
            
            while open_set:
                current_cost, current = heapq.heappop(open_set)
                
                if current == end_node:
                    # Reconstruct path
                    path = []
                    while current in came_from:
                        path.append(current)
                        current = came_from[current]
                    path.append(start_node)
                    route = path[::-1]
                    break
                    
                for neighbor in road.neighbors(current):
                    # Get edge weight using helper function
                    weight = get_edge_weight(current, neighbor)
                    
                    tentative_g_score = g_score[current] + weight
                    if tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score = tentative_g_score + heuristic(
                            (road.nodes[neighbor]['y'], road.nodes[neighbor]['x']),
                            end_latlon
                        )
                        heapq.heappush(open_set, (f_score, neighbor))
            else:
                print(f"CBS: No path found between {start_latlon} and {end_latlon}")
                return []
        
        except Exception as e:
            print(f"CBS: Error finding path: {e}")
            return []
    
    elif algorithm == 'm_star':
        try:
            paths, timelines, grid_steps = find_route_m_star(
                road,
                [start_node],
                [end_node],
                t_per_meter=0.1,
                simulation_time_step=1,
                max_time_steps=100
            )
            if paths:
                route = list(paths.values())[0]  # Get first (and only) path
            else:
                print(f"M*: No path found between {start_latlon} and {end_latlon}")
                return []
        except Exception as e:
            print(f"M*: Error finding path: {e}")
            return []

    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")

    # แปลง route จาก node ID เป็นพิกัด latitude, longitude
    return [(road.nodes[node]["y"], road.nodes[node]["x"]) for node in route]