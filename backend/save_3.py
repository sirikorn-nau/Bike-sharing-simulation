# 1️⃣ ส่วน Import Library
import folium
import streamlit as st
import random
import heapq
import json
import time
import streamlit.components.v1 as components
import math

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

# 2️⃣ ฟังก์ชันช่วยเหลือสำหรับ A* Search
def heuristic(a, b):
    return math.sqrt((a[0]-b[0])**2 + (a[1]-b[1])**2)

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
                f_score[neighbor] = tentative_g_score + heuristic(neighbor, goal)
                heapq.heappush(open_set, (f_score[neighbor], neighbor))
    return []

# 3️⃣ ฟังก์ชัน create_map(...) → สร้างแผนที่และฝัง JavaScript animation
#    ในส่วนนี้ เราจะไม่สร้าง station markers ด้วย Python แต่จะสร้างและอัปเดตใน JavaScript
def create_map(full_paths, agents_positions, station_locations, station_bikes_timeline, destination_positions):
    # สร้างแผนที่พื้นฐาน
    m = folium.Map(location=[13.728, 100.775], zoom_start=15)

    # วาดเส้นทางของ agent แต่ละคน (full_paths)
    for path in full_paths:
        folium.PolyLine(path, color='yellow', weight=2).add_to(m)


    # Marker Destination
    # destination_positions
    for i, dest in enumerate(destination_positions):
        folium.Marker(
            location=[dest[0], dest[1]],
            popup=f"Destination {i + 1}",
            icon=folium.Icon(color="gray", icon="flag"),
        ).add_to(m)



    # แปลงตัวแปร Python ให้เป็น JSON สำหรับ JavaScript
    agents_positions_json = json.dumps(agents_positions)
    station_locations_json = json.dumps(station_locations)
    station_bikes_timeline_json = json.dumps(station_bikes_timeline)

    map_var = m.get_name()


   
    
    custom_js = f"""
    <script>
    window.addEventListener('load', function() {{
        // ข้อมูล timeline ของตำแหน่ง agent และจำนวนจักรยานในแต่ละสถานี
        var agentsPositions = {agents_positions_json};
        var stationLocations = {station_locations_json};
        var stationBikesTimeline = {station_bikes_timeline_json};
        var mapObj = window["{map_var}"];
        
        // สร้าง icon สำหรับ agent และ station
        var redIcon = L.icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});
        var greenIcon = L.icon({{
            iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
            shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        }});
        
        // สร้าง marker สำหรับ agent โดยเริ่มต้นจากตำแหน่งแรกใน agentsPositions
        var agentMarkers = [];
        for (var i = 0; i < agentsPositions.length; i++) {{
            var marker = L.marker(agentsPositions[i][0], {{icon: redIcon}}).addTo(mapObj);
            marker.bindPopup("Agent " + (i+1));
            agentMarkers.push(marker);
        }}
        
        // สร้าง marker สำหรับ station โดยอิงจาก stationLocations และ stationBikesTimeline[0]
        var stationMarkers = [];
        for (var i = 0; i < stationLocations.length; i++) {{
            var marker = L.marker(stationLocations[i], {{icon: greenIcon}}).addTo(mapObj);
            marker.bindPopup("Station: " + stationLocations[i] + "<br>Bikes Available: " + stationBikesTimeline[0][i]);
            stationMarkers.push(marker);
        }}

        var timeStep = 0;
        var maxStep = agentsPositions[0].length;
        var interval = null;

        function updateMarkers() {{
            // อัปเดตตำแหน่งของ agent
            for (var i = 0; i < agentMarkers.length; i++) {{
                agentMarkers[i].setLatLng(agentsPositions[i][timeStep]);
            }}
            // อัปเดต popup ของ station ให้แสดงจำนวนจักรยานใน time step ปัจจุบัน
            for (var i = 0; i < stationMarkers.length; i++) {{
                stationMarkers[i].setPopupContent("Station: " + stationLocations[i] + "<br>Bikes Available: " + stationBikesTimeline[timeStep][i]);
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

    # กำหนดสถานีจักรยาน
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

    # สุ่มตำแหน่งเริ่มต้นและปลายทางของ agent
    start_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]
    destination_positions = [
        (random.uniform(min_lat, max_lat), random.uniform(min_lon, max_lon))
        for _ in range(num_persons)
    ]

    # สร้างกราฟสำหรับ A* Search ระหว่างสถานี
    graph = {}
    for i, station in enumerate(station_locations):
        graph[station] = {}
        for j, neighbor in enumerate(station_locations):
            if i != j:
                graph[station][neighbor] = heuristic(station, neighbor)

    # กำหนดจำนวนจักรยานเริ่มต้นในแต่ละสถานี
    initial_station_bikes = [num_bikes_per_station] * len(station_locations)

    # สร้างเส้นทาง (full_paths) สำหรับ agent แต่ละคน
    # โดยสมมติว่า full_path[1] คือสถานีที่ agent ไปเช่า
    full_paths = []
    rental_events = []  # เก็บ tuple (rental_time, station_index) สำหรับแต่ละ agent
    for person_pos, dest_pos in zip(start_positions, destination_positions):
        # ค้นหาสถานีสำหรับเช่าจักรยาน โดยตรวจสอบว่ามีจักรยานเหลืออยู่
        available_stations = [station for station, bikes in zip(station_locations, initial_station_bikes) if bikes > 0]
        if not available_stations:
            start_station = min(station_locations, key=lambda s: heuristic(person_pos, s))
        else:
            start_station = min(available_stations, key=lambda s: heuristic(person_pos, s))
        # สำหรับ drop-off (สถานีปลายทาง) เราเลือก station ที่ใกล้ destination มากที่สุด
        end_station = min(station_locations, key=lambda s: heuristic(dest_pos, s))
        # สร้างเส้นทาง: จุดเริ่มต้น → สถานีเช่า → (เส้นทาง A* ระหว่างสถานี) → จุดหมายปลายทาง
        complete_path = [person_pos, start_station]
        complete_path.extend(a_star_search(graph, start_station, end_station))
        complete_path.append(dest_pos)
        full_paths.append(complete_path)
        
        # คำนวณ time step ที่ agent มาถึงสถานีเช่า (full_path[1])
        # สมมติว่า agent ใช้เวลาสัดส่วน 1/(len(path)-1) ของ max_time_step ในการไปถึงสถานีที่ 1
        rental_time = int(max_time_step * (1 / (len(complete_path)-1)))
        station_index = station_locations.index(start_station)
        rental_events.append((rental_time, station_index))
        # ลดจำนวนจักรยานทันที (สำหรับการคำนวณ timeline)
        initial_station_bikes[station_index] -= 1

    # คำนวณ agents_positions สำหรับแต่ละ agent ในทุก time step
    agents_positions = []  # List of list: agents_positions[agent_index][time_step] = [lat, lon]
    for path in full_paths:
        agent_timeline = []
        segment_count = len(path) - 1
        for step in range(max_time_step + 1):
            progress = (step / max_time_step) * segment_count
            seg_index = int(progress)
            local_progress = progress - seg_index
            if seg_index >= segment_count:
                agent_timeline.append(path[-1])
            else:
                agent_timeline.append(interpolate_position(path[seg_index], path[seg_index+1], local_progress))
        agents_positions.append(agent_timeline)
    
    # สร้าง timeline ของ station bikes
    # เริ่มต้นที่ time step 0 มีจำนวนจักรยานตาม initial (ก่อน event rental)
    station_bikes_timeline = []
    # สมมติว่าเรามีค่าเริ่มต้นตามที่กำหนดไว้ในแต่ละ station (num_bikes_per_station)
    for t in range(max_time_step + 1):
        bikes_at_t = [st for st in [st for st in initial_station_bikes]]  # copy ค่า (จะปรับใหม่ด้านล่าง)
        station_bikes_timeline.append([num_bikes_per_station] * len(station_locations))
    
    # ปรับ station_bikes_timeline โดยลดจำนวนจักรยานเมื่อ event เกิดขึ้น
    # สำหรับแต่ละ time step t, ถ้ามี eventที่ rental_time <= t ให้ลดลง
    for t in range(max_time_step + 1):
        bikes = [num_bikes_per_station] * len(station_locations)
        for event_time, station_index in rental_events:
            if t >= event_time:
                bikes[station_index] -= 1
        station_bikes_timeline[t] = bikes

    # Debug: แสดง station_bikes_timeline (ตัวอย่าง time step แรก)
    print("Station bikes at time 0:", station_bikes_timeline[0])
    print("Station bikes at final time:", station_bikes_timeline[-1])

    map_style = """
    <style>
        .stVerticalBlock {
            width: 100% !important;
        }
        .st-emotion-cache-17vd2cm {
            width: 100% !important;
        }
        [data-testid="stAppViewContainer"] {
        
        }
        [data-testid="stIFrame"] {
            width: 100% !important;
            height: 650px !important
        }
        [data-testid="stMainBlockContainer"] {
            width: 100% !important;
            max-width: 100% !important
        }
    </style>
    """
    st.markdown(map_style, unsafe_allow_html=True)

    # สร้างแผนที่พร้อม animation โดยส่ง agents_positions และ station_bikes_timeline ไปยัง JavaScript
    traffic_map = create_map(full_paths, agents_positions, station_locations, station_bikes_timeline, destination_positions)
    st.write("### Traffic Simulation Map")
    
    with st.container():
        components.html(traffic_map._repr_html_(), height=600)


  


# 5️⃣ ส่วนอินพุต Streamlit
st.title("Traffic Simulation with Real-time Station Updates")
st.number_input("Number of Agents:", min_value=1, value=5, key='num_persons')
st.number_input("Max Time Steps:", min_value=1, value=100, key='max_time_step')
st.number_input("Number of Bikes per Station:", min_value=1, value=10, key='num_bikes')

if st.button("Run Simulation"):
    run_simulation()
