# 1️⃣ ส่วน Import Library
import heapq

import osmnx as ox
import networkx as nx

from geopy.distance import geodesic 

from function_2.cbs_alogo import *
from app import * 




def find_route_osm(road, start_latlon, end_latlon, algorithm, exclude_pos=None):
    """
    หาเส้นทางระหว่างสองจุดโดยใช้โครงข่ายถนน OSM
    
    Args:
        road: กราฟโครงข่ายถนน OSM
        start_latlon: จุดเริ่มต้นในรูปแบบ (lat, lon)
        end_latlon: จุดปลายทางในรูปแบบ (lat, lon)
        algorithm: อัลกอริทึมที่ใช้ ('a_star' หรือ 'cbs')
        
    Returns:
        รายการพิกัด [(lat, lon), ...] ที่แสดงเส้นทาง
    """
    # แปลงพิกัด latitude, longitude ให้เป็นโหนดที่ใกล้ที่สุดในกราฟถนน
    start_node = ox.distance.nearest_nodes(road, start_latlon[1], start_latlon[0])
    end_node = ox.distance.nearest_nodes(road, end_latlon[1], end_latlon[0])
    
    # ปัจจุบันคุณใช้ ox.distance.nearest_nodes เพื่อหาโหนดที่ใกล้ที่สุด แต่ไม่ได้ตรวจสอบว่าโหนดเหล่านั้นเชื่อมต่อกันหรือไม่ หากโหนดเริ่มต้นและปลายทางไม่เชื่อมต่อกัน เส้นทางที่ได้อาจจะไม่สมจริง
    if not nx.has_path(road, start_node, end_node):
        print(f"คำเตือน: ไม่พบเส้นทางที่เชื่อมต่อระหว่าง {start_latlon} และ {end_latlon}")
        return [start_latlon, end_latlon]  # ส่งคืนเส้นตรงเป็นทางสำรอง

    # ตรวจสอบว่าพบโหนดที่ถูกต้องหรือไม่
    if start_node is None or end_node is None:
        print(f"คำเตือน: ไม่พบโหนดถนนที่ถูกต้องใกล้ {start_latlon} หรือ {end_latlon}")
        return [start_latlon, end_latlon]  # ส่งคืนเส้นตรงเป็นทางสำรอง
    



    def get_edge_weight(current, neighbor):
        """
        ดึงความยาวของเส้นทางระหว่างโหนด current และ neighbor
        """
        edge_data = road.get_edge_data(current, neighbor)
        if edge_data:
            if isinstance(edge_data, dict):
                return edge_data.get('length', 1)
            elif isinstance(edge_data, list):
                return edge_data[0].get('length', 1)
        return 1  # Default weight if no length found
          

    # เส้นทางที่จะส่งคืน
    route_nodes = []

    # 📌 เลือกอัลกอริธึมที่ใช้
    if algorithm == 'a_star':
        # Use A* algorithm
        try:
            route_nodes = nx.astar_path(road, start_node, end_node, weight='length')
        except nx.NetworkXNoPath:
            print(f"A*: ไม่พบเส้นทางระหว่าง {start_latlon} และ {end_latlon}")
            return [start_latlon, end_latlon]  # ส่งคืนเส้นตรงเป็นทางสำรอง
        except Exception as e:
            print(f"A*: เกิดข้อผิดพลาดในการหาเส้นทาง: {e}")
            return [start_latlon, end_latlon]  # ส่งคืนเส้นตรงเป็นทางสำรอง
            
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
                    route_nodes = path[::-1]
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
                print(f"CBS: ไม่พบเส้นทางระหว่าง {start_latlon} และ {end_latlon}")
                return [start_latlon, end_latlon]  # ส่งคืนเส้นตรงเป็นทางสำรอง
        
        except Exception as e:
            print(f"CBS: เกิดข้อผิดพลาดในการหาเส้นทาง: {e}")
            return [start_latlon, end_latlon]  # ส่งคืนเส้นตรงเป็นทางสำรอง
    
    elif algorithm == 'm_star':
        # ใช้ M* Algorithm
        try:
            # หาเส้นทางโดยใช้ A* เป็นพื้นฐาน
            route_nodes = nx.astar_path(road, start_node, end_node, weight='length') #nx.astar_path: เป็นฟังก์ชันใน networkx ที่ใช้ A*  , weight='length': กำหนดให้ A* ใช้ความยาวของเส้นทาง (edge weight) เป็นค่า cost ในการคำนวณเส้นทาง


            
            # หากมีตำแหน่งที่ต้องหลีกเลี่ยง (exclude_pos) ให้ปรับเส้นทาง
            if exclude_pos:
                # หาโหนดที่ใกล้กับ exclude_pos มากที่สุด
                exclude_node = find_nearest_node_M_Star(road, exclude_pos)
                
                if exclude_node in route_nodes:
                    # หาเส้นทางใหม่โดยหลีกเลี่ยงตำแหน่ง exclude_node
                    new_path = []
                    for node in route_nodes:
                        if node != exclude_node:
                            new_path.append(node)
                        else:
                            # หาเส้นทางอ้อม
                            try:
                                # สร้างกราฟชั่วคราวที่ไม่มีโหนดที่ต้องหลีกเลี่ยง
                                temp_graph = road.copy()
                                temp_graph.remove_node(exclude_node)
                                
                                # หาเส้นทางใหม่
                                bypass_path = nx.astar_path(temp_graph, new_path[-1], end_node, weight='length')
                                new_path.extend(bypass_path[1:])
                                break
                            except nx.NetworkXNoPath:
                                print(f"ไม่สามารถหาเส้นทางอ้อมได้")
                                # ใช้เส้นทางเดิม
                                new_path = route_nodes
                                break
                            except Exception as e:
                                print(f"เกิดข้อผิดพลาดในการหาเส้นทางอ้อม: {e}")
                                new_path = route_nodes
                                break
                    
                    route_nodes = new_path
        except nx.NetworkXNoPath:
            print(f"ไม่พบเส้นทางระหว่าง {start_node} และ {end_node} โดยใช้ M*")
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการหาเส้นทางด้วย M*: {e}")
    
    # ถ้าไม่พบเส้นทาง ส่งคืนเส้นตรง
    if not route_nodes:
        print(f"ไม่พบเส้นทางระหว่าง {start_latlon} และ {end_latlon}")
        return [start_latlon, end_latlon]
    
    # แปลงโหนดกราฟเป็นพิกัด lat, lon
    route_coords = []
    for node in route_nodes:
        # ดึงข้อมูลของโหนด
        node_data = road.nodes[node]
        lat = node_data.get('y')  # latitude
        lon = node_data.get('x')  # longitude
        if lat is not None and lon is not None:
            route_coords.append((lat, lon))
    
    # ถ้าเส้นทางว่างเปล่า (ไม่มีพิกัดถูกดึงออกมา) ให้ส่งคืนเส้นตรง
    if not route_coords:
        print(f"พบเส้นทางแต่ไม่สามารถดึงพิกัดได้ระหว่าง {start_latlon} และ {end_latlon}")
        return [start_latlon, end_latlon]
    
    # เพิ่มจุดเริ่มต้นและปลายทางของเส้นทาง ถ้าไม่ได้อยู่ในเส้นทางอยู่แล้ว
    if geodesic(route_coords[0], start_latlon).meters > 10:  # หากจุดแรกห่างจากจุดเริ่มต้นมากกว่า 10 เมตร
        route_coords.insert(0, start_latlon)
    if geodesic(route_coords[-1], end_latlon).meters > 10:  # หากจุดสุดท้ายห่างจากจุดปลายทางมากกว่า 10 เมตร
        route_coords.append(end_latlon)
    
    return route_coords



def find_nearest_node_M_Star(graph, point):
    """
    หาโหนดในกราฟที่ใกล้กับจุด GPS ที่กำหนดมากที่สุด
    """
    nodes = list(graph.nodes(data=True))
    nearest_node = None
    min_distance = float('inf')
    
    for node_id, data in nodes:
        # ตรวจสอบว่าโหนดมีข้อมูล lat, lon หรือ y, x
        if 'y' in data and 'x' in data:
            node_point = (data['y'], data['x'])
        else:
            # หากเป็นโหนดที่ไม่มีข้อมูลพิกัด ให้ข้าม
            continue
        
        # คำนวณระยะทางระหว่างจุด
        distance = geodesic(point, node_point).kilometers
        
        if distance < min_distance:
            min_distance = distance
            nearest_node = node_id
    
    print(f"ค้นหาโหนดที่ใกล้เคียงที่สุดสำหรับ {point}: พบ {nearest_node} ที่ระยะห่าง {min_distance:.4f} กม.")
    return nearest_node