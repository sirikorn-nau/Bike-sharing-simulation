# 1️⃣ ส่วน Import Library
import folium
import json

import osmnx as ox
import networkx as nx

def is_valid_path(path, road):
    """
    ตรวจสอบว่าเส้นทางเดินตามถนนหรือไม่
    """
    for i in range(len(path) - 1):
        start_node = ox.distance.nearest_nodes(road, path[i][1], path[i][0])
        end_node = ox.distance.nearest_nodes(road, path[i+1][1], path[i+1][0])
        if not nx.has_path(road, start_node, end_node):
            return False
    return True


# 3️⃣ ฟังก์ชัน create_map(...) → สร้างแผนที่และฝัง JavaScript animation
#    ในส่วนนี้ เราจะไม่สร้าง station markers ด้วย Python แต่จะสร้างและอัปเดตใน JavaScript
def create_map(full_paths, agents_positions, station_locations, station_bikes_timeline, destination_positions, road):
    """
    สร้างแผนที่และฝัง JavaScript animation สำหรับจำลองการเคลื่อนที่ของ agent
    """
    print("Building map with", len(agents_positions), "agents")

    # สร้างแผนที่พื้นฐาน
    m = folium.Map(location=[13.728, 100.775], zoom_start=15)

    # วาดเส้นทางของ agent แต่ละคน (full_paths)
    for path in full_paths:
        if is_valid_path(path, road):
            folium.PolyLine(path, color='yellow', weight=2).add_to(m)

    # Marker Destination
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
    
    # สร้างปุ่มควบคุมและเพิ่มสไตล์
    control_html = """
    <div id="mapControls" style="text-align:center; margin-top: 10px; padding: 10px; background-color: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1000; position: relative;">
        <button id="startSimBtn" style="margin: 0 5px; padding: 5px 10px; cursor: pointer; background-color: #4CAF50; color: white; border: none; border-radius: 3px;">Start</button>
        <button id="pauseSimBtn" style="margin: 0 5px; padding: 5px 10px; cursor: pointer; background-color: #ff9800; color: white; border: none; border-radius: 3px;">Pause</button>
        <button id="resetSimBtn" style="margin: 0 5px; padding: 5px 10px; cursor: pointer; background-color: #f44336; color: white; border: none; border-radius: 3px;">Reset</button>
        <div id="timeStepDisplay" style="margin-top: 5px; font-weight: bold;">Time Step: 0</div>
    </div>
    """
    
    # สคริปต์ JavaScript ปรับปรุงใหม่
    custom_js = f"""
    <script>
    (function() {{
        // ตัวแปรกลอบอลสำหรับเก็บข้อมูลสำคัญ
        var agentsPositions = {agents_positions_json};
        var stationLocations = {station_locations_json};
        var stationBikesTimeline = {station_bikes_timeline_json};
        var mapObj = null;
        var agentMarkers = [];
        var stationMarkers = [];
        var timeStep = 0;
        var maxStep = 0;
        var interval = null;
        var mapInitialized = false;
        
        // กำหนดคำสั่งทำงานเมื่อหน้าเว็บโหลดเสร็จ
        document.addEventListener('DOMContentLoaded', function() {{
            console.log("DOM loaded, checking for map...");
            setTimeout(checkForMap, 500);
        }});
        
        // ตรวจสอบว่าแผนที่พร้อมใช้งานหรือยัง
        function checkForMap() {{
            console.log("Checking for map...");
            if (window.{map_var}) {{
                console.log("Map found!");
                initializeSimulation();
            }} else {{
                console.log("Map not ready, waiting...");
                setTimeout(checkForMap, 500);
            }}
        }}
        
        // เริ่มต้นการจำลอง
        function initializeSimulation() {{
            try {{
                console.log("Initializing simulation...");
                
                // หาจำนวน time steps ทั้งหมด
                for (var i = 0; i < agentsPositions.length; i++) {{
                    var steps = Object.keys(agentsPositions[i]).length;
                    maxStep = Math.max(maxStep, steps);
                }}
                console.log("Max time steps:", maxStep);
                
                // รับอ็อบเจ็กต์แผนที่
                mapObj = window.{map_var};
                
                // สร้าง icons
                var agentIcon = L.icon({{
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                }});
                
                var stationIcon = L.icon({{
                    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png',
                    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.4/images/marker-shadow.png',
                    iconSize: [25, 41],
                    iconAnchor: [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize: [41, 41]
                }});
                
                // สร้าง markers สำหรับ agents
                for (var i = 0; i < agentsPositions.length; i++) {{
                    if (agentsPositions[i] && agentsPositions[i][0]) {{
                        var marker = L.marker(agentsPositions[i][0], {{icon: agentIcon}});
                        marker.addTo(mapObj);
                        marker.bindPopup("Agent " + (i+1));
                        agentMarkers.push(marker);
                    }}
                }}
                
                // สร้าง markers สำหรับ stations
                for (var i = 0; i < stationLocations.length; i++) {{
                    var marker = L.marker(stationLocations[i], {{icon: stationIcon}});
                    marker.addTo(mapObj);
                    
                    var bikeCount = 0;
                    if (stationBikesTimeline && stationBikesTimeline[0]) {{
                        bikeCount = stationBikesTimeline[0][i];
                    }}
                    
                    marker.bindPopup("Station " + (i+1) + "<br>Bikes Available: " + bikeCount);
                    stationMarkers.push(marker);
                }}
                
                mapInitialized = true;
                console.log("Map markers initialized");
                
                // ตั้งค่าปุ่มควบคุม
                setupControlButtons();
            }} catch (error) {{
                console.error("Error initializing simulation:", error);
            }}
        }}
        
        // ตั้งค่าปุ่มควบคุม
        function setupControlButtons() {{
            console.log("Setting up control buttons");
            
            var startBtn = document.getElementById("startSimBtn");
            var pauseBtn = document.getElementById("pauseSimBtn");
            var resetBtn = document.getElementById("resetSimBtn");
            
            if (startBtn) {{
                startBtn.addEventListener("click", function() {{
                    console.log("Start button clicked");
                    startAnimation();
                }});
            }} else {{
                console.error("Start button not found");
            }}
            
            if (pauseBtn) {{
                pauseBtn.addEventListener("click", function() {{
                    console.log("Pause button clicked");
                    pauseAnimation();
                }});
            }} else {{
                console.error("Pause button not found");
            }}
            
            if (resetBtn) {{
                resetBtn.addEventListener("click", function() {{
                    console.log("Reset button clicked");
                    resetAnimation();
                }});
            }} else {{
                console.error("Reset button not found");
            }}
        }}
        
        // ฟังก์ชันอัปเดตตำแหน่ง markers
        function updateMarkers() {{
            try {{
                // อัปเดตตัวแสดงเวลา
                var timeDisplay = document.getElementById("timeStepDisplay");
                if (timeDisplay) {{
                    timeDisplay.textContent = "Time Step: " + timeStep;
                }}
                
                // อัปเดตตำแหน่ง agents
                for (var i = 0; i < agentMarkers.length; i++) {{
                    if (agentsPositions[i] && agentsPositions[i][timeStep]) {{
                        agentMarkers[i].setLatLng(agentsPositions[i][timeStep]);
                    }}
                }}
                
                // อัปเดตข้อมูลจักรยานในสถานี
                for (var i = 0; i < stationMarkers.length; i++) {{
                    if (stationBikesTimeline && stationBikesTimeline[timeStep] && i < stationBikesTimeline[timeStep].length) {{
                        var bikeCount = stationBikesTimeline[timeStep][i];
                        stationMarkers[i].setPopupContent("Station " + (i+1) + "<br>Bikes Available: " + bikeCount);
                    }}
                }}
            }} catch (error) {{
                console.error("Error updating markers:", error);
            }}
        }}
        
        // ฟังก์ชันเริ่มการจำลอง
        function startAnimation() {{
            if (!interval && mapInitialized) {{
                console.log("Starting animation at time step:", timeStep);
                interval = setInterval(function() {{
                    if (timeStep < maxStep - 1) {{
                        timeStep++;
                        updateMarkers();
                    }} else {{
                        console.log("Animation complete");
                        clearInterval(interval);
                        interval = null;
                    }}
                }}, 200);
            }}
        }}
        
        // ฟังก์ชันหยุดการจำลองชั่วคราว
        function pauseAnimation() {{
            if (interval) {{
                console.log("Pausing animation at time step:", timeStep);
                clearInterval(interval);
                interval = null;
            }}
        }}
        
        // ฟังก์ชันรีเซ็ตการจำลอง
        function resetAnimation() {{
            console.log("Resetting animation");
            if (interval) {{
                clearInterval(interval);
                interval = null;
            }}
            timeStep = 0;
            updateMarkers();
        }}
    }})();
    </script>
    """
    
    # เพิ่ม HTML และ JavaScript ลงในแผนที่
    html_element = folium.Element(control_html + custom_js)
    m.get_root().html.add_child(html_element)
    
    return m