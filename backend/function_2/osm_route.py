
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