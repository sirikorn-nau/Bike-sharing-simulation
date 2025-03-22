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

    print("agents_positions", agents_positions)

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
    <div style="text-align:center; margin-top: 10px; padding: 10px; background-color: white; border-radius: 5px; box-shadow: 0 2px 5px rgba(0,0,0,0.2); z-index: 1000; position: relative;">
        <button id="startBtn" class="map-control-btn" style="margin: 0 5px; padding: 5px 10px; cursor: pointer; background-color: #4CAF50; color: white; border: none; border-radius: 3px;">Start</button>
        <button id="pauseBtn" class="map-control-btn" style="margin: 0 5px; padding: 5px 10px; cursor: pointer; background-color: #ff9800; color: white; border: none; border-radius: 3px;">Pause</button>
        <button id="resetBtn" class="map-control-btn" style="margin: 0 5px; padding: 5px 10px; cursor: pointer; background-color: #f44336; color: white; border: none; border-radius: 3px;">Reset</button>
        <p id="timeStepDisplay" style="margin-top: 5px; font-weight: bold;">Time Step: 0</p>
    </div>
    """
    
    # สคริปต์ JavaScript ที่ปรับปรุงใหม่เพื่อให้ทำงานกับ Streamlit
    custom_js = f"""
    <script>
    // ตัวแปรกลอบอลสำหรับเก็บข้อมูลสำคัญ
    var agentsPositions = {agents_positions_json};
    var stationLocations = {station_locations_json};
    var stationBikesTimeline = {station_bikes_timeline_json};
    var mapObj = null;
    var agentMarkers = [];
    var stationMarkers = [];
    var timeStep = 0;
    var maxStep = agentsPositions[0].length;
    var interval = null;
    var mapInitialized = false;
    
    // ฟังก์ชันเริ่มต้นแผนที่และตั้งค่าตัวแปรต่างๆ
    function initializeMapAndControls() {{
        console.log("Initializing map and controls...");
        
        // ตรวจสอบว่าแผนที่พร้อมใช้งานหรือไม่
        if (typeof window["{map_var}"] !== 'undefined') {{
            mapObj = window["{map_var}"];
            
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
            
            // สร้าง marker สำหรับ agent
            for (var i = 0; i < agentsPositions.length; i++) {{
                try {{
                    var marker = L.marker(agentsPositions[i][0], {{icon: redIcon}});
                    marker.addTo(mapObj);
                    marker.bindPopup("Agent " + (i+1));
                    agentMarkers.push(marker);
                }} catch (e) {{
                    console.error("Error creating agent marker:", e);
                }}
            }}
            
            // สร้าง marker สำหรับ station
            for (var i = 0; i < stationLocations.length; i++) {{
                try {{
                    var marker = L.marker(stationLocations[i], {{icon: greenIcon}});
                    marker.addTo(mapObj);
                    marker.bindPopup("Station " + (i+1) + "<br>Bikes Available: " + stationBikesTimeline[0][i]);
                    stationMarkers.push(marker);
                }} catch (e) {{
                    console.error("Error creating station marker:", e);
                }}
            }}
            
            // อัปเดต markers ครั้งแรก
            updateMarkers();
            
            // เพิ่ม event listeners ให้กับปุ่มต่างๆ
            var startBtn = document.getElementById("startBtn");
            var pauseBtn = document.getElementById("pauseBtn");
            var resetBtn = document.getElementById("resetBtn");
            
            if (startBtn) {{
                startBtn.addEventListener("click", startAnimation);
                console.log("Start button event listener added");
            }}
            
            if (pauseBtn) {{
                pauseBtn.addEventListener("click", pauseAnimation);
                console.log("Pause button event listener added");
            }}
            
            if (resetBtn) {{
                resetBtn.addEventListener("click", resetAnimation);
                console.log("Reset button event listener added");
            }}
            
            mapInitialized = true;
            console.log("Map fully initialized");
        }} else {{
            console.log("Map not yet available");
        }}
    }}

    // ฟังก์ชันอัปเดตตำแหน่ง markers
    function updateMarkers() {{
        if (!mapInitialized || !mapObj) return;
        
        try {{
            // อัปเดตตำแหน่งของ agent
            for (var i = 0; i < agentMarkers.length; i++) {{
                if (i < agentsPositions.length && timeStep < agentsPositions[i].length) {{
                    agentMarkers[i].setLatLng(agentsPositions[i][timeStep]);
                }}
            }}
            
            // อัปเดต popup ของ station
            for (var i = 0; i < stationMarkers.length; i++) {{
                if (i < stationLocations.length && timeStep < stationBikesTimeline.length) {{
                    stationMarkers[i].setPopupContent("Station " + (i+1) + "<br>Bikes Available: " + stationBikesTimeline[timeStep][i]);
                }}
            }}
            
            // อัปเดตตัวแสดงเวลา
            var timeDisplay = document.getElementById("timeStepDisplay");
            if (timeDisplay) {{
                timeDisplay.innerText = "Time Step: " + timeStep;
            }}
        }} catch (e) {{
            console.error("Error updating markers:", e);
        }}
    }}

    // ฟังก์ชันเริ่มการจำลอง
    function startAnimation() {{
        console.log("Start animation clicked");
        if (!interval && mapInitialized) {{
            interval = setInterval(function() {{
                if (timeStep < maxStep - 1) {{
                    timeStep++;
                    updateMarkers();
                }} else {{
                    clearInterval(interval);
                    interval = null;
                }}
            }}, 200); // ปรับความเร็วการจำลองให้ช้าลงเล็กน้อย
        }}
    }}

    // ฟังก์ชันหยุดชั่วคราว
    function pauseAnimation() {{
        console.log("Pause animation clicked");
        clearInterval(interval);
        interval = null;
    }}

    // ฟังก์ชันรีเซ็ต
    function resetAnimation() {{
        console.log("Reset animation clicked");
        pauseAnimation();
        timeStep = 0;
        updateMarkers();
    }}
    
    // ตรวจสอบการโหลดแบบต่อเนื่องเพื่อรอให้ทุกส่วนโหลดเสร็จ
    function checkAndInitialize() {{
        if (document.getElementById("startBtn") && 
            document.getElementById("pauseBtn") && 
            document.getElementById("resetBtn") && 
            typeof window["{map_var}"] !== 'undefined') {{
            
            // หน่วงเวลาเล็กน้อยก่อนเริ่มการทำงาน
            setTimeout(initializeMapAndControls, 500);
            return true;
        }}
        return false;
    }}
    
    // ตรวจสอบเป็นระยะเพื่อให้แน่ใจว่าทุกองค์ประกอบถูกโหลดเสร็จ
    var initCheckInterval = setInterval(function() {{
        if (checkAndInitialize()) {{
            clearInterval(initCheckInterval);
        }}
    }}, 300);
    
    // สำรองไว้ - ตรวจสอบอีกครั้งหลังจาก DOM โหลดเสร็จ
    document.addEventListener("DOMContentLoaded", function() {{
        setTimeout(function() {{
            if (!mapInitialized) {{
                checkAndInitialize();
            }}
        }}, 1000);
    }});
    
    // เพิ่ม event listener เมื่อหน้าเว็บโหลดเสร็จ
    window.addEventListener("load", function() {{
        setTimeout(function() {{
            if (!mapInitialized) {{
                checkAndInitialize();
            }}
        }}, 1000);
    }});
    </script>
    """
    
    # เพิ่ม HTML และ JavaScript ลงในแผนที่
    html_element = folium.Element(control_html + custom_js)
    m.get_root().html.add_child(html_element)
    
    return m