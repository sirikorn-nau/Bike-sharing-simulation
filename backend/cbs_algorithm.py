def heuristic(a, b):
    """คำนวณ heuristic distance ระหว่างสองจุด (ใช้ Manhattan distance หรือ Euclidean distance)"""
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def a_star_search(graph, start, goal):
    """A* algorithm สำหรับหาเส้นทางจาก start ไป goal"""
    open_set = [(0, start)]  # (cost, node)
    came_from = {}
    g_score = {node: float('inf') for node in graph}
    g_score[start] = 0
    f_score = {node: float('inf') for node in graph}
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            return path[::-1]

        for neighbor in graph[current]:
            tentative_g_score = g_score[current] + graph[current][neighbor]
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []  # หากหาเส้นทางไม่ได้

def detect_conflicts(paths):
    """ตรวจสอบว่ามีความขัดแย้ง (conflict) ระหว่าง agent หรือไม่"""
    time_step_dict = {}
    for agent_id, path in paths.items():
        for t, node in enumerate(path):
            if (t, node) in time_step_dict:
                return (agent_id, time_step_dict[(t, node)], t, node)  # (agent, conflicting_agent, timestep, node)
            time_step_dict[(t, node)] = agent_id
    return None

def cbs(agents, graph):
    """Conflict-Based Search (CBS) algorithm"""
    solution = {}
    
    # คำนวณเส้นทางเริ่มต้นของแต่ละ agent โดยใช้ A*
    for agent_id, data in agents.items():
        solution[agent_id] = a_star_search(graph, data['start'], data['goal'])
    
    conflict = detect_conflicts(solution)
    while conflict:
        agent1, agent2, timestep, conflict_node = conflict
        
        # เลือก agent ที่มีระยะทางสั้นกว่าตาม priority
        priority_agent = min([agent1, agent2], key=lambda a: len(solution[a]))
        other_agent = agent1 if priority_agent == agent2 else agent2
        
        # หาเส้นทางใหม่ให้ agent ที่ priority ต่ำกว่า
        constraint_graph = {node: neighbors.copy() for node, neighbors in graph.items()}
        if conflict_node in constraint_graph:
            constraint_graph[conflict_node] = {}  # บล็อก node นี้ชั่วคราว
        
        new_path = a_star_search(constraint_graph, agents[other_agent]['start'], agents[other_agent]['goal'])
        if new_path:
            solution[other_agent] = new_path
        else:
            print(f"Agent {other_agent} ติดขัด ไม่สามารถหาเส้นทางใหม่ได้")
            return None
        
        conflict = detect_conflicts(solution)
    
    return solution