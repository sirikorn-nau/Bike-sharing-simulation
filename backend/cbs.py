import folium
import streamlit as st
import random
import heapq
import json
import time
import streamlit.components.v1 as components
import math

from geopy.distance import geodesic 


# โครงสร้างข้อมูลเบื้องต้นสำหรับ CBS
class CBSTreeNode:
    def __init__(self, solution, constraints, cost):
        self.solution = solution         # dict: agent -> path (list of grid steps)
        self.constraints = constraints   # list of constraints (ตัวอย่าง: (agent, grid_cell, time))
        self.cost = cost                 # รวม cost ของ solution

def find_conflict(solution):
    """
    ตรวจสอบว่า solution (dict: agent -> path) มี conflict กันหรือไม่
    เช่น ถ้า agent A และ agent B อยู่ใน grid เดียวกันใน time เดียวกัน
    คืนค่าข้อมูล conflict (เช่น (agent_A, agent_B, grid_cell, time))
    หากไม่มี conflictคืนค่า None
    """
    # ตัวอย่างตรวจสอบ conflict แบบง่าย ๆ
    max_time = max(len(path) for path in solution.values())
    for t in range(max_time):
        occupied = {}
        for agent, path in solution.items():
            pos = path[t] if t < len(path) else path[-1]
            if pos in occupied:
                return (occupied[pos], agent, pos, t)
            else:
                occupied[pos] = agent
    return None

def low_level_search(agent, start, goal, constraints, map_data):
    """
    ใช้ A* หรือวิธีการอื่นในการหาเส้นทางสำหรับ agent โดยคำนึงถึง constraints
    constraints คือรายการข้อจำกัดสำหรับ agent นี้ (เช่น ห้ามเข้า grid cell ในเวลาที่กำหนด)
    คืนค่าเส้นทาง (list ของ grid steps)
    """
    # ตัวอย่าง: ใช้ A* ปกติแล้วค่อยตรวจสอบ constraint ใน cost function
    # คุณสามารถปรับปรุงให้ตรวจสอบ constraint ระหว่างการค้นหา
    return a_star_search(map_data, start, goal)

def compute_solution(agents, map_data, constraints):
    """
    สำหรับแต่ละ agent ให้คำนวณเส้นทางโดยใช้ low_level_search โดยคำนึง constraints
    คืนค่า solution เป็น dict: agent -> path
    """
    solution = {}
    for agent, data in agents.items():
        start = data["start"]
        goal = data["goal"]
        path = low_level_search(agent, start, goal, constraints, map_data)
        solution[agent] = path
    return solution

def cbs(agents, map_data):
    # initial solution (ไม่คำนึง constraint)
    root_solution = compute_solution(agents, map_data, constraints=[])
    root_cost = sum(len(path) for path in root_solution.values())
    root = CBSTreeNode(root_solution, constraints=[], cost=root_cost)
    
    open_list = [root]
    
    while open_list:
        # เลือก node ที่มี cost ต่ำสุด
        node = min(open_list, key=lambda n: n.cost)
        open_list.remove(node)
        
        conflict = find_conflict(node.solution)
        if conflict is None:
            # ไม่มี conflict แล้ว
            return node.solution
        
        # conflict: (agent1, agent2, grid_cell, time)
        agent1, agent2, cell, time = conflict
        
        for agent in [agent1, agent2]:
            # สร้าง constraint ใหม่สำหรับ agent ที่มี conflict
            new_constraints = node.constraints.copy()
            new_constraints.append((agent, cell, time))
            
            # สร้าง solution ใหม่โดย re-plan สำหรับ agent ที่ถูกจำกัด
            new_solution = node.solution.copy()
            data = agents[agent]
            new_path = low_level_search(agent, data["start"], data["goal"], new_constraints, map_data)
            if new_path is None:
                continue  # ไม่พบ solution ใหม่ให้ constraint นี้
            new_solution[agent] = new_path
            new_cost = sum(len(path) for path in new_solution.values())
            new_node = CBSTreeNode(new_solution, new_constraints, new_cost)
            open_list.append(new_node)
    
    return None  # ไม่มี solution ที่ไม่มี conflict