# 1️⃣ ส่วน Import Library
import heapq
import networkx as nx
from geopy.distance import geodesic 

from function.distance_real import *
from function_2.find_route_osm import *
# from function_2.mstar import *
from function_2.create_map_2 import *


# from function.statistics import *
from function.graph import *





# ฟังก์ชันสำหรับเพิ่มโหนดชั่วคราวลงในกราฟ
def add_temporary_node(graph, point):
    """
    เพิ่มโหนดชั่วคราวลงในกราฟ NetworkX และเชื่อมต่อกับโหนดที่ใกล้ที่สุด
    
    Args:
        graph (nx.Graph): กราฟ NetworkX
        point (tuple): พิกัดของจุดใหม่ (lat, lon)
    
    Returns:
        nx.Graph: สำเนาของกราฟที่มีโหนดชั่วคราวใหม่
    """


    # สร้างสำเนาของกราฟ
    temp_graph = graph.copy()
    
    # ถ้าจุดนี้มีอยู่ในกราฟอยู่แล้ว ให้ส่งคืนกราฟตามเดิม
    if point in temp_graph.nodes():
        return temp_graph


    # หาโหนดที่ใกล้เคียงที่สุดโดยใช้ระยะทาง geodesic (ระยะทางบนผิวโลก)
    nearest = min(temp_graph.nodes(), key=lambda node: geodesic(point, node).meters)
    # nearest = min(temp_graph.nodes(), key=lambda node: heuristic(point, node).meters)


    # คำนวณระยะทางไปยังโหนดที่ใกล้ที่สุด
    distance = geodesic(point, nearest).meters


    # เพิ่มโหนดใหม่และเส้นเชื่อม
    temp_graph.add_node(point)
    temp_graph.add_edge(point, nearest, weight=distance, length=distance)

    return temp_graph







# คลาส CBSNode สำหรับแทนโหนดในต้นไม้ constraint
class CBSNode:
# คลาส CBSNode เป็นส่วนสำคัญของอัลกอริทึม Conflict-Based Search (CBS) ซึ่งใช้สำหรับแก้ปัญหาการวางแผนเส้นทางของหลาย agent โดยหลีกเลี่ยงการชนกัน (multi-agent pathfinding)
# คลาสนี้ใช้เพื่อสร้างโหนด (node) ในต้นไม้ค้นหาของอัลกอริทึม CBS แต่ละโหนดจะเก็บข้อมูลต่อไปนี้:
    # ข้อจำกัด (constraints): ข้อจำกัดที่กำหนดให้แต่ละ agent ต้องปฏิบัติตาม (เช่น ห้ามไปที่จุดใดจุดหนึ่งในเวลาที่กำหนด)
    # เส้นทาง (solution): เส้นทางของแต่ละ agent ที่สอดคล้องกับข้อจำกัด
    # ค่าใช้จ่าย (cost): ผลรวมของค่าใช้จ่ายของเส้นทางทุก agent
    # จำนวน grid steps: จำนวน time steps ที่แต่ละ agent ใช้ในการเดินทาง
    
    def __init__(self, constraints=None, solution=None, cost=0):
        self.constraints = constraints or {}  # Dictionary of agent_id: [(vertex/edge, timestep)] = เก็บข้อจำกัดของแต่ละ agent โดยแต่ละข้อจำกัดจะระบุว่า agent นั้นไม่สามารถไปที่จุด (vertex) หรือเส้นเชื่อม (edge) ใดได้ในเวลาที่กำหนด (timestep)
        # เช่น {0: [((1, 2), 3)]} หมายความว่า agent 0 ไม่สามารถอยู่ที่จุด (1, 2) ในเวลา 3
        self.solution = solution or {}        # รูปแบบ: {agent_id: path} เช่น {0: [(0, 0), (1, 1), (2, 2)]} หมายความว่า agent 0 เดินทางจาก (0, 0) ไป (1, 1) และไป (2, 2)
        self.cost = cost                     # Sum of individual path costs = ผลรวมของค่าใช้จ่ายของเส้นทางทุก agent (เช่น ผลรวมของความยาวเส้นทางหรือเวลาที่ใช้)
        self.grid_steps = {}                 # Dictionary to store grid steps for each agent = เก็บจำนวน time steps ที่แต่ละ agent ใช้ในการเดินทาง

    def __lt__(self, other): # พารามิเตอร์: other (โหนดอื่นที่ใช้เปรียบเทียบ) = เปรียบเทียบโหนดปัจจุบัน (self) กับโหนดอื่น (other) โดยใช้ค่าใช้จ่าย (cost) เป็นเกณฑ์
        # ถ้า self.cost < other.cost คืนค่า True (โหนดปัจจุบันดีกว่า) ถ้าไม่ใช่ คืนค่า False (โหนดอื่นดีกว่า)
        return self.cost < other.cost
    # เมธอด __lt__ ช่วยให้สามารถเปรียบเทียบโหนดได้โดยใช้ค่าใช้จ่าย (cost) เป็นเกณฑ์ ทำให้สามารถเลือกโหนดที่ดีที่สุดได้ง่ายขึ้น





# ฟังก์ชันสำหรับตรวจจับการขัดแย้งระหว่างเส้นทางของตัวแทนสองตัว
def detect_conflicts(path1, path2):
    """
    ตรวจจับการขัดแย้งที่จุด (vertex) และขอบ (edge) ระหว่างสองเส้นทาง
    คืนค่าเป็นรายการของการขัดแย้ง: (timestep, type, location)
    """
    conflicts = [] # ลิสต์สำหรับเก็บการขัดแย้งที่พบ
    min_len = min(len(path1), len(path2)) # หาความยาวขั้นต่ำของเส้นทางทั้งสอง เพื่อป้องกันการเข้าถึงตำแหน่งที่เกินความยาวของเส้นทาง


    # การขัดแย้งอาจเกิดขึ้นได้สองรูปแบบ
    # 1. การขัดแย้งที่จุด (Vertex Conflict): ตัวแทนสองตัวอยู่ที่ตำแหน่งเดียวกันในเวลาเดียวกัน
    for t in range(min_len):
        if path1[t] == path2[t]: # ตรวจสอบว่าตัวแทนทั้งสองอยู่ที่ตำแหน่งเดียวกันในเวลาเดียวกันหรือไม่
            conflicts.append((t, 'vertex', path1[t])) # บันทึกการขัดแย้ง: ถ้ามีการขัดแย้งที่จุด ให้เพิ่มข้อมูลการขัดแย้งลงในลิสต์ conflicts ในรูปแบบ (timestep, 'vertex', location) /  (เวลาที่เกิดการขัดแย้ง, ประเภทของการขัดแย้ง (ขัดแย้งที่จุด), ตำแหน่งที่เกิดการขัดแย้ง)
    

    
    # 2. การขัดแย้งที่ขอบ (Edge Conflict): ตัวแทนสองตัวสลับตำแหน่งกัน (เช่น ตัวแทน A ย้ายจากจุด X ไป Y ในขณะที่ตัวแทน B ย้ายจากจุด Y ไป X ในเวลาเดียวกัน)
    for t in range(min_len - 1): # วนลูปผ่านทุก time step (t) จาก 0 ถึง min_len - 2 (เพราะต้องตรวจสอบการย้ายตำแหน่งในขั้นถัดไป)
        if path1[t] == path2[t+1] and path1[t+1] == path2[t]: # ตรวจสอบว่าตัวแทนทั้งสองสลับตำแหน่งกันหรือไม่ (เช่น ตัวแทน A ย้ายจาก X ไป Y ในขณะที่ตัวแทน B ย้ายจาก Y ไป X)
            conflicts.append((t, 'edge', (path1[t], path1[t+1])))
    
    return conflicts



# คำนวณจำนวนก้าวจริงบนตาราง (grid steps) ที่ตัวแทนใช้ในเส้นทาง
def calculate_grid_steps(path, t_per_meter, simulation_time_step, max_time_steps):
    """
    คำนวณจำนวนก้าวจริงบนตารางที่ตัวแทนใช้ตลอดเส้นทาง
    """
    # find_path_with_constraints (ซึ่งเป็นอัลกอริทึม A* ที่ปรับแต่ง) ถูกใช้ภายในอัลกอริทึม CBS: 
        # A* ถูกใช้ภายใน CBS เพื่อหาเส้นทางสำหรับแต่ละตัวแทน
    

    # คำนวณขอบเขตของแต่ละช่วง (segment boundaries)
    boundaries = compute_segment_boundaries(path, t_per_meter, simulation_time_step)
    
    # รับจำนวนก้าวทั้งหมด (ขอบเขตสุดท้าย)
    total_steps = boundaries[-1]
    
    # ถ้าจำนวนก้าวทั้งหมดเกิน max_time_steps ให้จำกัดไว้
    return min(total_steps, max_time_steps)







def find_path_with_constraints(graph, start, goal, constraints, t_per_meter, simulation_time_step):
    """
    หาเส้นทางที่สอดคล้องกับข้อจำกัดโดยใช้ A*
    """
    open_set = [(0, start, 0)]  # (f_score, node, timestep)
    came_from = {}
    g_score = {(start, 0): 0}
    f_score = {(start, 0): heuristic(start, goal)}

    while open_set:
        current_f, current_node, t = heapq.heappop(open_set)

        # ถ้าถึงเป้าหมาย
        if current_node == goal:
            path = []
            current_state = (current_node, t)
            while current_state in came_from:
                path.append(current_state[0])
                current_state = came_from[current_state]
            path.append(start)
            return path[::-1]

        # ตรวจสอบโหนดข้างเคียง
        for neighbor in graph.neighbors(current_node):
            next_t = t + 1

            # ตรวจสอบข้อจำกัด
            violates_constraint = False
            if (neighbor, next_t) in constraints:  # Vertex constraint
                violates_constraint = True
            if (current_node, neighbor, t) in constraints:  # Edge constraint
                violates_constraint = True

            if not violates_constraint:
                edge_data = graph.get_edge_data(current_node, neighbor)
                edge_weight = edge_data['weight'] if edge_data else 1

                neighbor_state = (neighbor, next_t)
                tentative_g_score = g_score[(current_node, t)] + edge_weight

                if neighbor_state not in g_score or tentative_g_score < g_score[neighbor_state]:
                    came_from[neighbor_state] = (current_node, t)
                    g_score[neighbor_state] = tentative_g_score
                    f_score[neighbor_state] = tentative_g_score + heuristic(neighbor, goal)
                    heapq.heappush(open_set, (f_score[neighbor_state], neighbor, next_t))

    return None  # ไม่พบเส้นทาง



    
def cbs_search(graph, start_positions, destination_positions, station_locations, t_per_meter, simulation_time_step, max_time_steps, road, max_iterations=300):
    """
    Comprehensive Conflict-Based Search (CBS) algorithm for multi-agent pathfinding
    
    Args:
        graph: NetworkX graph of the road network
        start_positions: List of starting coordinates for agents
        destination_positions: List of destination coordinates for agents
        station_locations: List of bicycle station locations
        t_per_meter: Time taken per meter
        simulation_time_step: Size of time step in simulation
        max_time_steps: Maximum number of time steps allowed
        road: OpenStreetMap road graph
        max_iterations: Maximum iterations for CBS algorithm
    
    Returns:
        Tuple of (solution, agent_timelines, grid_steps)
    """
    print("🚀 Starting Robust CBS Search")
    
    # Preprocessing and filtering of agents
    valid_agents = []
    initial_paths = {}
    grid_steps = {}
    
    # Temporary graph for modifications
    temp_graph = graph.copy()
    
    # Preprocess agents to ensure routability
    for agent_id, (start, goal) in enumerate(zip(start_positions, destination_positions)):
        print(f"🔍 Checking Agent {agent_id}: {start} → {goal}")
        
        try:
            # ในส่วนของการเพิ่มโหนดชั่วคราว
            temp_graph = add_temporary_node(temp_graph, start)
            temp_graph = add_temporary_node(temp_graph, goal)

            # ตรวจสอบการเชื่อมต่อ
            try:
                # โค้ดที่อาจเกิดข้อผิดพลาด
                if not nx.has_path(temp_graph, start, goal):
                    print(f"❌ ไม่พบเส้นทางระหว่าง {start} และ {goal}")
                    continue
            finally:
                # ทำความสะอาดหรือดำเนินการบางอย่าง
                print("ดำเนินการเสร็จสิ้น")
            
            # Find nearest stations
            start_station = min(station_locations, key=lambda s: heuristic(start, s))
            end_station = min(station_locations, key=lambda s: heuristic(goal, s))
            
            # Construct path through stations
            # Try this instead:
            osm_path_start = find_route_osm(road, start, start_station, 'cbs')
            osm_path_middle = find_route_osm(road, start_station, end_station, 'cbs')
            osm_path_end = find_route_osm(road, end_station, goal, 'cbs')
            path = osm_path_start + osm_path_middle[1:] + osm_path_end[1:]
            
            # Validate path
            if len(path) < 2:
                print(f"❌ Agent {agent_id} - Invalid path")
                continue
            
            # Calculate grid steps
            agent_grid_steps = calculate_grid_steps(
                path, 
                t_per_meter, 
                simulation_time_step, 
                max_time_steps
            )
            
            # Store valid agent information
            valid_agents.append(agent_id)
            initial_paths[agent_id] = path
            grid_steps[agent_id] = agent_grid_steps
            
            print(f"✅ Agent {agent_id} - Path validated (Length: {len(path)}, Grid Steps: {agent_grid_steps})")
        
        except Exception as e:
            print(f"❌ Agent {agent_id} - Preprocessing Error: {e}")
    
    # If no valid agents, return failure
    if not valid_agents:
        print("❌ No valid agents found!")
        return None, None, None
    
    # Single agent scenario - immediate return
    if len(valid_agents) == 1:
        print("🚲 Single Agent Scenario")
        
        # Compute timeline for the single agent
        single_agent_id = valid_agents[0]
        single_path = initial_paths[single_agent_id]
        single_timeline = compute_agent_timeline(
            single_path, 
            t_per_meter, 
            simulation_time_step, 
            max_time_steps
        )
        
        return (
            {single_agent_id: single_path}, 
            {single_agent_id: single_timeline}, 
            {single_agent_id: grid_steps[single_agent_id]}
        )
    
    # Multi-agent CBS search
    # Initialize root node
    root = CBSNode()
    root.solution = initial_paths.copy()
    root.grid_steps = grid_steps.copy()
    
    # Priority queue for CBS search
    open_list = [root] # เริ่มต้นด้วยโหนดราก (root node)
    # Iteration tracking
    iteration_count = 0
    problem_agents = set() # เก็บ agent ที่มีปัญหา


    # จัดลำดับความสำคัญของตัวแทน (Prioritized Planning) : ไม่ได้ใช้ เพราะจะจัดเรียงคิวก็ต่อเมื่อมันเกิดปัญหา เนื่องจากทำการสร้างคิวขึ้นมาก็เพราะเกิดerrorขึ้นในตอนขัด
    priorities = sorted(
        valid_agents,
        key=lambda agent_id: heuristic(start_positions[agent_id], destination_positions[agent_id])
    )

    while open_list and iteration_count < max_iterations:
        iteration_count += 1
        # Get node with lowest cost
        current_node = heapq.heappop(open_list) # ดึงโหนดที่มี cost ต่ำสุดออกจาก heap
        
        # Compute agent timelines
        agent_timelines = {}
        for agent_id, path in current_node.solution.items():
            timeline = compute_agent_timeline(
                path, 
                t_per_meter, 
                simulation_time_step, 
                max_time_steps
            )
            agent_timelines[agent_id] = timeline
        
        # Detect conflicts between agents
        conflicts = []
        agent_ids = list(agent_timelines.keys())
        for i in range(len(agent_ids)):
            for j in range(i + 1, len(agent_ids)):
                agent1_id = agent_ids[i]
                agent2_id = agent_ids[j]
                conflicts.extend(
                    detect_conflicts(
                        agent_timelines[agent1_id], 
                        agent_timelines[agent2_id]
                    )
                )
        
        # No conflicts - solution found
        if not conflicts:
            print(f"🎉 Solution found in {iteration_count} iterations")
            return current_node.solution, agent_timelines, current_node.grid_steps

        
        # Resolve first conflict
        conflict = conflicts[0]
        timestep, conflict_type, location = conflict
        
        # Try resolving conflict for both agents
        child_created = False
        for agent_idx in range(2):
            new_constraints = current_node.constraints.copy()
            current_agent_id = list(current_node.solution.keys())[agent_idx]
            
            if current_agent_id not in new_constraints:
                new_constraints[current_agent_id] = set()
            
            # ในส่วนของ CBS ที่เพิ่มข้อจำกัด
            if conflict_type == 'vertex':
                new_constraints[current_agent_id].add((tuple(location), timestep))
            else:  # edge conflict
                new_constraints[current_agent_id].add(
                    (tuple(location[0]), tuple(location[1]), timestep)
                )
            
            # Create child node
            child = CBSNode(new_constraints)
            
            # Find new path with constraints
            new_path = find_path_with_constraints(
                temp_graph,
                start_positions[current_agent_id],
                destination_positions[current_agent_id],
                new_constraints[current_agent_id],
                t_per_meter,
                simulation_time_step
            )
            
            # ✨ **แก้ไขตรงนี้: ถ้าไม่มีเส้นทาง ให้ agent หยุดนิ่ง** ✨
            if new_path is None:
                print(f"⛔ Agent {current_agent_id} ไม่มีเส้นทาง -> หยุดนิ่ง (เพิ่มเข้า problem_agents)")
                problem_agents.add(current_agent_id)
                new_path = [start_positions[current_agent_id]] * max_time_steps  # อยู่กับที่
            
            # Update child node
            child.solution = current_node.solution.copy()
            child.solution[current_agent_id] = new_path
            child.cost = sum(len(path) for path in child.solution.values())
            child.grid_steps = current_node.grid_steps.copy()
            child.grid_steps[current_agent_id] = calculate_grid_steps(
                new_path, 
                t_per_meter, 
                simulation_time_step, 
                max_time_steps
            )
            
            # Add to open list
            heapq.heappush(open_list, child)
            child_created = True
        
        # Terminate if no child nodes created
        if not child_created:
            print("❌ Cannot create new paths due to constraints")
            return None, None, None
    
    if iteration_count >= max_iterations:
        print(f"⚠️ Reached max iterations ({max_iterations}). Returning best found solution.")

        print("problem_agents", problem_agents)

        # เอาเฉพาะ agent ปกติ
        final_solution = {k: v for k, v in current_node.solution.items() if k not in problem_agents}
        final_agent_timelines = {k: v for k, v in agent_timelines.items() if k not in problem_agents}
        final_grid_steps = {k: v for k, v in current_node.grid_steps.items() if k not in problem_agents}

        # สร้าง dummy solution สำหรับ agent ที่มีปัญหา (ให้อยู่กับที่)
        for agent_id in problem_agents:
            final_solution[agent_id] = [start_positions[agent_id]] * max_time_steps
            final_agent_timelines[agent_id] = [start_positions[agent_id]] * max_time_steps
            final_grid_steps[agent_id] = [start_positions[agent_id]] * max_time_steps

        return final_solution, final_agent_timelines, final_grid_steps

    print(f"❌ No solution found after {iteration_count} iterations")
    return None, None, None














