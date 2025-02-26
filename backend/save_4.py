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
    # ✅ ใช้ คำนวณตำแหน่งใหม่ บนเส้นทาง โดยอ้างอิงจาก fraction
    # fraction คือค่าที่บอกว่า agent เดินทางไปแล้วกี่ % ของ segment
    # fraction = 0 → อยู่ที่ start
    # fraction = 0.5 → อยู่ตรงกลางระหว่าง start กับ end
    # fraction = 1 → อยู่ที่ end

    """คำนวณตำแหน่งระหว่าง start กับ end ตาม fraction (0-1)
       คืนค่าเป็น [lat, lon]"""
    return [
        start[0] + (end[0] - start[0]) * fraction, # คำนวณค่า latitude
        start[1] + (end[1] - start[1]) * fraction # คำนวณค่า longitude
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

   
    full_paths = [] 
    rental_events = []  # เป็น list เก็บ เวลาที่เกิดการยืมคืนขึ้น
    return_events = []  # เก็บข้อมูล (เวลาคืน, index ของสถานี)
    
    for start_pos, dest_pos in zip(start_positions, destination_positions):
        print(f"Agent เริ่มที่ {start_pos} และต้องไปที่ {dest_pos}")

        # จัดเรียงสถานีทั้งหมดตามระยะทางจาก agent (ใกล้ -> ไกล) เพราะจะเช็คสถานีที่ใกล้ที่สุดก่อน , ถ้าสถานีนั้น ไม่มีจักรยาน → ให้เลือก สถานีที่ใกล้รองลงมา แต่ถ้ายังไม่มี → เลือกสถานีรองที่เหลือไปเรื่อย ๆ
        sorted_stations = sorted(station_locations, key=lambda s: heuristic(start_pos, s))
       
        # ค้นหาสถานีที่มีจักรยานเหลืออยู่
        start_station = None
        for station in sorted_stations:
            station_index = station_locations.index(station)  # หา index ของสถานีนี้
            if initial_station_bikes[station_index] > 0:  # ตรวจสอบว่ามีจักรยานหรือไม่
                start_station = station
                break  # เจอสถานีที่มีจักรยานแล้ว ออกจากลูป

        # ถ้าทุกสถานีไม่มีจักรยานเลย ให้เลือกสถานีที่ใกล้ที่สุด (แม้ไม่มีจักรยาน)
        if start_station is None:
            start_station = sorted_stations[0]


        # สำหรับ drop-off (สถานีปลายทาง) เราเลือก 𝘀𝘁𝗮𝘁𝗶𝗼𝗻 ที่ใกล้ 𝗱𝗲𝘀𝘁𝗶𝗻𝗮𝘁𝗶𝗼𝗻 มากที่สุด
        end_station = min(station_locations, key=lambda s: heuristic(dest_pos, s))



        # ขั้นตอน สร้างเส้นทาง: จุดเริ่มต้น → สถานีเช่า → (เส้นทาง A* ระหว่างสถานี) → จุดหมายปลายทาง
        # 1. จุดเริ่มต้น → สถานีเช่า
        # complete_path = [start_pos, start_station] # list ที่เก็บเส้นทางของ agent ตั้งแต่เริ่มต้น จุดแรกคือ ตำแหน่งเริ่มต้นของ agent, จุดที่สองคือ สถานีเช่าจักรยาน (start_station) ที่เลือกไว้
        complete_path = [start_pos]
       

        # 2. สถานีเช่า → สถานีคืน (ด้วย a* alogorithm ⛩️)
        #! 🚩 ตรงนี้ไม่ถูก เราต้องใช้ a* algotithm ทั้ง path ไม่ใช่ใช้แค่หาในช่วง station 
        complete_path.extend(a_star_search(graph, start_station, end_station))
    
       

        # 3. สถานีคืน → จุดหมายปลายทาง
        complete_path.append(dest_pos)
        full_paths.append(complete_path) # full_paths เป็น list ที่เก็บเส้นทางของ agent ทุกคน
        
    
        # คำนวณว่า agent ใช้เวลากี่ time step ในการไปถึงสถานีเช่า
        rental_time = int(max_time_step * (1 / (len(complete_path)-1)))
        # แบ่งเวลาอย่างเท่าๆ กัน ตามจำนวนจุดในเส้นทาง 
        #! 🚩 ตรงนี้น่าจะผิด เนื่องจากก เราไม่ได้แบ่งเวลาเท่ากัน แต่แยกการเดินของใครของมัน ถ้าเดินไม่ถึงใน time_stemp ก้คือไม่ถึง

        return_time = int(max_time_step * (len(complete_path) - 2) / (len(complete_path) - 1))  # เวลาเดินทางถึงสถานีคืน


        # หา index ของสถานีเช่า (start_station) จาก station_locations
        station_index = station_locations.index(start_station)
        end_station_index = station_locations.index(end_station)


        # บันทึกว่า มี agent เช่าจักรยานที่สถานีนี้ (station_index) ตอนเวลา rental_time
        rental_events.append((rental_time, station_index)) # rental_events คือ list ของ tuple ที่เก็บ (เวลาเช่า, index ของสถานี)
        return_events.append((return_time, end_station_index))

        
        # ลดจำนวนจักรยานทันที (สำหรับการคำนวณ timeline)
        initial_station_bikes[station_index] -= 1
        # เพิ่มจักรยานในสถานีคืน
        initial_station_bikes[end_station_index] += 1


        



    # คำนวณ ตำแหน่งของ agent ในแต่ละ time step 
    # สร้าง list ของตำแหน่ง เพื่อระบุว่า agent อยู่ตรงไหนในช่วงเวลาแต่ละช่วง

    # List of list: ⁡⁢⁢⁢agents_positions⁡[agent_index][time_step] = [lat, lon]
    agents_positions = []  


    for path in full_paths: # full_paths คือเส้นทางของ agent แต่ละคน
        agent_timeline = [] # agent_timeline → list ที่ใช้เก็บตำแหน่งของ agent ในแต่ละ time step
        segment_count = len(path) - 1 # segment_count → จำนวนช่วงระหว่างจุดที่ agent เคลื่อนที่


        for step in range(max_time_step + 1):

            progress = (step / max_time_step) * segment_count # คำนวณว่า agent เคลื่อนที่ไปกี่ segment แล้ว
            # segment_count = จำนวนช่วง (segment) ของเส้นทางที่ agent ต้องเดินทาง
            # path คือ ลำดับของจุด ที่ agent ต้องเดินทางผ่าน แต่ "ช่วงการเดินทาง" หรือ segment ช่องว่างระหว่างจุด 

            seg_index = int(progress) # เป็นช่วง (segment) ที่ agent อยู่ในตอนนั้น

            local_progress = progress - seg_index

            if seg_index >= segment_count: # ถ้า seg_index เกินจำนวน segment แปลว่า agent ถึงจุดหมายปลายทางแล้ว
                agent_timeline.append(path[-1])
            else: # ถ้ายัง ไม่ถึงจุดหมายปลายทาง
                
                agent_timeline.append(interpolate_position(path[seg_index], path[seg_index+1], local_progress))
                # ใช้ฟังก์ชัน interpolate_position() คำนวณตำแหน่งของ agent
                # คำนวณตำแหน่งระหว่าง path[seg_index] → path[seg_index+1]
                # ใช้ local_progress เป็นตัวบอกว่ายังไปได้กี่ %

        agents_positions.append(agent_timeline)
    
    # 🔹 ปรับค่า bike ตาม rental และ return events , เพื่อให้ marker มันอัพเดตค่า real time เมื่อ agent มาสถานี
    station_bikes_timeline = [[num_bikes_per_station] * len(station_locations) for _ in range(max_time_step + 1)]
    for t in range(max_time_step + 1):
        for rental_time, station_index in rental_events:
            if t >= rental_time:
                station_bikes_timeline[t][station_index] -= 1  # ลดจักรยานเมื่อลูกค้ามาเช่า

        for return_time, station_index in return_events:
            if t >= return_time:
                station_bikes_timeline[t][station_index] += 1  # เพิ่มจักรยานเมื่อลูกค้าคืนจักรยาน




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


#TODO Problem 
# ช่วยอธิบายหน่อยว่าโค้ดนี้มีการเดินทางยังไง เพราะฉันอยากให้มัน เหมือนเดินทีละกริดอะไรอย่างนี้ แต่จากที่ดูโค้ด เหมือนมันจะเดินตามที่คำนวณเพื่อให้สมู้ด แต่ฉันอยากให้ทุก agent มันมีการเคลืื่อนที่ที่เท่ากัน 
# โดยmax_time_step คือจำนวนทีละกริดที่สามารถเดินได้ คือพอถึง max ก้ให้ agent หยุดเดินไปเลย
# คือตอนนี้มันมีปัญหาที่ พอเดินทางไปถึงสถานียืมแล้ว อยู่ดีๆ ตัว agent ก้เคลื่อนที่เร็วขึ้น 



# ปรับการแบ่งเวลาสำหรับแต่ละ segmentให้สัมพันธ์กับความยาวของ segment นั้น ๆ
