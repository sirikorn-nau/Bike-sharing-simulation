import folium
import streamlit as st
import random
import heapq
import time
import streamlit.components.v1 as components
from folium.plugins import TimestampedGeoJson

def interpolate_position(start, end, fraction):
    return (
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction
    )

def heuristic(a, b):
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2) ** 0.5

def a_star_search(graph, start, goal):
    open_set = []
    heapq.heappush(open_set, (0, start))
    came_from = {}
    g_score = {node: float('inf') for node in graph}
    g_score[start] = 0
    f_score = {node: float('inf') for node in graph}
    f_score[start] = heuristic(start, goal)

    while open_set:
        _, current = heapq.heappop(open_set)
        if current == goal:
            return reconstruct_path(came_from, current)

        for neighbor, cost in graph[current].items():
            tentative_g_score = g_score[current] + cost
            if tentative_g_score < g_score[neighbor]:
                came_from[neighbor] = current
                g_score[neighbor] = tentative_g_score
                f_score[neighbor] = g_score[neighbor] + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

def create_map(station_locations, full_paths, positions_over_time):
    m = folium.Map(location=[13.728, 100.775], zoom_start=15)

    for station in station_locations:
        folium.Marker(location=station, icon=folium.Icon(color='blue')).add_to(m)
    
    for path in full_paths:
        folium.PolyLine(path, color='green', weight=2).add_to(m)
    
    # ใช้ TimestampedGeoJson เพื่อทำให้ Marker เคลื่อนที่แบบ Real-time
    features = []
    for i, positions in enumerate(zip(*positions_over_time)):
        for pos in positions:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [pos[1], pos[0]]
                },
                "properties": {
                    "time": i * 1000,
                    "style": {"color": "red", "radius": 5}
                }
            })

    TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="PT1S",
        add_last_point=True
    ).add_to(m)

    return m

def run_simulation():
    num_persons = st.session_state.num_persons
    max_time_step = st.session_state.max_time_step
    station_locations = [
        (13.7279, 100.7707),
        (13.7277, 100.7644),
        (13.7295, 100.7750),
        (13.7296, 100.7800),
        (13.7307, 100.7809),
        (13.7265, 100.7752),
        (13.7292, 100.7774)
    ]

    min_lat, max_lat = min(x[0] for x in station_locations), max(x[0] for x in station_locations)
    min_lon, max_lon = min(x[1] for x in station_locations), max(x[1] for x in station_locations)

    start_positions = [(random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon)) for _ in range(num_persons)]
    destination_positions = [(random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon)) for _ in range(num_persons)]

    graph = {s: {t: heuristic(s, t) for t in station_locations if s != t} for s in station_locations}
    full_paths = []

    for person_pos, dest_pos in zip(start_positions, destination_positions):
        start_station = min(station_locations, key=lambda s: heuristic(person_pos, s))
        end_station = min(station_locations, key=lambda s: heuristic(dest_pos, s))
        complete_path = [person_pos, start_station] + a_star_search(graph, start_station, end_station) + [dest_pos]
        full_paths.append(complete_path)
    
    positions_over_time = [[] for _ in range(num_persons)]
    for step in range(max_time_step + 1):
        for i, path in enumerate(full_paths):
            segment_length = len(path) - 1
            segment_index = int(step / max_time_step * segment_length)
            start_point = path[segment_index]
            end_point = path[segment_index + 1] if segment_index + 1 < len(path) else start_point
            local_progress = (step / max_time_step * segment_length) - segment_index
            positions_over_time[i].append(interpolate_position(start_point, end_point, local_progress))

    traffic_map = create_map(station_locations, full_paths, positions_over_time)
    st.write("### Traffic Map")
    components.html(folium.Figure().add_child(traffic_map)._repr_html_(), height=500)

st.title("Traffic Simulation with Folium Map")
st.number_input("Number of Persons:", min_value=1, value=5, key='num_persons')
st.number_input("Max Time Steps:", min_value=1, value=100, key='max_time_step')
if st.button("Run Simulation"):
    run_simulation()
