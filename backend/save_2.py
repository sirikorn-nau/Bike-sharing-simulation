# 1️⃣ ส่วน Import Library
import folium
import streamlit as st
import random
import heapq
import json
import streamlit.components.v1 as components

def interpolate_position(start, end, fraction):
    """คำนวณตำแหน่งระหว่าง start กับ end ตาม fraction (0-1)
       คืนค่าเป็น [lat, lon]"""
    return [
        start[0] + (end[0] - start[0]) * fraction,
        start[1] + (end[1] - start[1]) * fraction
    ]

def reconstruct_path(came_from, current):
    path = [current]
    while current in came_from:
        current = came_from[current]
        path.append(current)
    return path[::-1]

# 2️⃣ ฟังก์ชันช่วยเหลือ
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


# 3️⃣ ฟังก์ชัน create_map(...) → สร้างแผนที่
def create_map(station_locations, full_paths, positions_over_time, station_bikes):
    m = folium.Map(location=[13.728, 100.775], zoom_start=15) # กำหนดจุดศูนย์กลางแผนที่

    # for station in station_locations:
    #     folium.Marker(
    #         location=station,
    #         icon=folium.Icon(color='green', icon="info-sign"),
    #         popup="Station"
    #     ).add_to(m)


    #! เพิ่มใหม่ 
    for station, bikes in zip(station_locations, station_bikes):
        folium.Marker(
            location=station,
            icon=folium.Icon(color='green', icon="info-sign"),
            popup=f"Station: {station}<br>Bikes Available: {bikes}"
        ).add_to(m)

    for path in full_paths:
        folium.PolyLine(path, color='yellow', weight=2).add_to(m)

    agents_positions_json = json.dumps(positions_over_time) # ตัวแปร agents_positions_json เก็บ ลำดับพิกัดของ agent ในแต่ละเวลา
    map_var = m.get_name()

    custom_js = f"""
    <script>
    window.addEventListener('load', function() {{
        console.log("Agents positions:", {agents_positions_json});

        var redIcon = L.icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});

        var agentsPositions = {agents_positions_json};
        var markers = [];
        var mapObj = window["{map_var}"];

        var timeStep = 0;
        var maxStep = agentsPositions[0].length;
        var interval = null;

        function updateMarkers() {{
            for (var i = 0; i < markers.length; i++) {{
                markers[i].setLatLng(agentsPositions[i][timeStep]);
            }}
            document.getElementById("timeStepDisplay").innerText = "Time Step: " + timeStep;
        }}

        function startAnimation() {{
            if (!interval) {{
                interval = setInterval(function() {{
                    if (timeStep < maxStep - 1) {{
                        timeStep++;
                        updateMarkers();
                    }} else {{
                        clearInterval(interval);
                        interval = null;
                    }}
                }}, 100);
            }}
        }}

        function pauseAnimation() {{
            clearInterval(interval);
            interval = null;
        }}

        function resetAnimation() {{
            pauseAnimation();
            timeStep = 0;
            updateMarkers();
        }}

        for (var i = 0; i < agentsPositions.length; i++) {{
            var marker = L.marker(agentsPositions[i][0], {{icon: redIcon}}).addTo(mapObj);
            markers.push(marker);
        }}

        document.getElementById("startBtn").addEventListener("click", startAnimation);
        document.getElementById("pauseBtn").addEventListener("click", pauseAnimation);
        document.getElementById("resetBtn").addEventListener("click", resetAnimation);

        updateMarkers();
    }});
    </script>
    """

    control_html = """
    <div style="text-align:center; margin-top: 10px;">
        <button id="startBtn">Start</button>
        <button id="pauseBtn">Pause</button>
        <button id="resetBtn">Reset</button>
        <p id="timeStepDisplay">Time Step: 0</p>
    </div>
    """

    m.get_root().html.add_child(folium.Element(control_html + custom_js))
    return m



# 4️⃣ ฟังก์ชัน run_simulation() → รันการจำลอง
def run_simulation():
    num_persons = st.session_state.num_persons
    max_time_step = st.session_state.max_time_step
    num_bikes_per_station = st.session_state.num_bikes


    # 🔹 กำหนดสถานีจักรยาน
    station_locations = [
        (13.7279, 100.7707),
        (13.7277, 100.7644),
        (13.7295, 100.7750),
        (13.7296, 100.7800),
        (13.7307, 100.7809),
        (13.7265, 100.7752),
        (13.7292, 100.7774)
    ]

    min_lat = min(x[0] for x in station_locations)
    max_lat = max(x[0] for x in station_locations)
    min_lon = min(x[1] for x in station_locations)
    max_lon = max(x[1] for x in station_locations)


    # 🔹 สร้างตำแหน่งเริ่มต้นและปลายทาง
    start_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]
    destination_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]

    #! เพิ่มใหม่ 
    graph = {}
    for i, station in enumerate(station_locations):  # วนลูปทุกสถานี
        graph[station] = {}  # กำหนดให้สถานีเป็นโหนดในกราฟ
        for j, neighbor in enumerate(station_locations):  # วนลูปอีกครั้งเพื่อตรวจสอบสถานีอื่น
            if i != j:  # หลีกเลี่ยงการเชื่อมโยงตัวเอง (self-loop)
                dist = heuristic(station, neighbor)  # คำนวณระยะทางระหว่างสองสถานี
                graph[station][neighbor] = dist  # เก็บค่าเป็น edges ในกราฟ


    station_bikes = [num_bikes_per_station] * len(station_locations)

    # 🔹 สร้างเส้นทางเดิน 
    full_paths = []
    for person_pos, dest_pos in zip(start_positions, destination_positions):
        # Find paths for person
        # หา สถานีต้นทางที่มีจักรยาน และใกล้ผู้เดินทางที่สุด
        # route = [person_pos, dest_pos]
        # full_paths.append(route)


        #! เพิ่มใหม่ 
        # หา station ที่จะเดินทางไปเช่า และ เพิ่มการดักเงื่อนไขที่ว่า ถ้า station_bikes น้อยกว่า 0 ให้ไปเลือก station อื่น
        available_stations = [
            station for station, bikes in zip(station_locations, station_bikes) if bikes > 0
        ] # available_stations: ใช้ list comprehension เพื่อสร้างรายชื่อสถานีที่ยังมีจักรยาน (bikes > 0) อยู่

        if not available_stations:
            # กรณีที่ไม่มีสถานีใดที่มีจักรยาน (available_stations ว่าง)
            # สามารถเลือกได้ว่าจะให้เลือกสถานีใกล้จุดเริ่มต้นของ agent
            # หรือแสดงข้อความแจ้งเตือน เช่น "จักรยานหมดแล้ว"
            # ในที่นี้ผมเลือกให้เลือกสถานีที่ใกล้กับ person_pos โดยไม่คำนึงจักรยาน
            start_station = min(station_locations, key=lambda station: heuristic(person_pos, station))
            end_station = min(station_locations, key=lambda station: heuristic(dest_pos, station))
        else:
            start_station = min(available_stations, key=lambda station: heuristic(person_pos, station))
            end_station = min(available_stations, key=lambda station: heuristic(dest_pos, station))

        # # หา station ใกล้ des
        # end_station = min(station_locations, key=lambda station: heuristic(dest_pos, station))
        

        
        # รวมเส้นทาง: จุดเริ่มต้น → สถานีเช่า → (เส้นทางระหว่างสถานีด้วย A* Search) → จุดหมายปลายทาง
        complete_path = [person_pos]  # จุดเกิด
        complete_path.append(start_station)  # ไป sta ใกล้สุด
        complete_path.extend(a_star_search(graph, start_station, end_station))  # เส้นทางระหว่างสถานีเช่าและสถานีปลายทาง
        complete_path.append(dest_pos)  # ไป des
        
        full_paths.append(complete_path)

        # ลดจำนวนจักรยานในสถานีที่เลือก (ถ้ามีจักรยานเหลืออยู่)
        station_index = station_locations.index(start_station)
        if station_bikes[station_index] > 0:
            station_bikes[station_index] -= 1


    print(f"station_bikes : {station_bikes}") # station_bikes : [8, 10, 9, 8, 10, 10, 10]


    # 🔹 คำนวณตำแหน่งของ agent ในแต่ละเฟรม
    positions_over_time = [[] for _ in range(num_persons)]
    for step in range(max_time_step + 1):
        for i, path in enumerate(full_paths):
            positions_over_time[i].append(interpolate_position(path[0], path[1], step / max_time_step))

    # 🔹 สร้างแผนที่และแสดงใน Streamlit
    traffic_map = create_map(station_locations, full_paths, positions_over_time, station_bikes)
    st.write("### Traffic Simulation Map")
    components.html(traffic_map._repr_html_(), height=600)


# 5️⃣ ส่วนอินพุต Streamlit
st.title("Traffic Simulation with Start/Pause/Reset")
st.number_input("Number of Agents:", min_value=1, value=5, key='num_persons')
st.number_input("Max Time Steps:", min_value=1, value=100, key='max_time_step')
st.number_input("Number of Bikes per Station:", min_value=1, value=10, key='num_bikes')

if st.button("Run Simulation"):
    run_simulation()
