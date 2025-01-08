import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';
import 'leaflet/dist/leaflet.css';

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});

const LeafletMap = () => {
  const mapRef = useRef(null);
  const agentRef = useRef(null);
  const [coordinates, setCoordinates] = useState({ lat: 0, lng: 0 });
  const [isMoving, setIsMoving] = useState(false);
  const wsRef = useRef(null);
  const mapInstanceRef = useRef(null);
  
  // กำหนดเส้นทางแบบ static (เส้นทางตัวอย่างในกรุงเทพฯ)
  const staticPath = [
    { lat: 13.7563, lng: 100.5018 }, // สยาม
    { lat: 13.7469, lng: 100.5349 }, // ทองหล่อ
    { lat: 13.7378, lng: 100.5611 }, // พระโขนง
    { lat: 13.7160, lng: 100.5841 }, // อุดมสุข
    { lat: 13.6959, lng: 100.6044 }, // แบริ่ง
    { lat: 13.6784, lng: 100.6068 }  // สำโรง
  ];

  // ใช้ useEffect เพื่อสร้างและกำหนดค่าต่าง ๆ ของแผนที่ในตอนแรก
  useEffect(() => {
    // Initialize map ตั้งจุดเริ่มต้นที่สยาม
    const map = L.map(mapRef.current).setView([13.7563, 100.5018], 13);
    mapInstanceRef.current = map;
    
    // Add tile layer (OpenStreetMap)
    // เพิ่มเลเยอร์แผนที่พื้นฐานจาก OpenStreetMap
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Create agent marker with custom icon
    const agentIcon = L.icon({
      iconUrl: require('leaflet/dist/images/marker-icon.png'),
      iconSize: [25, 41],
      iconAnchor: [12, 41],
    });

    // ตั้ง marker ที่จุดเริ่มต้น (สยาม)
    agentRef.current = L.marker([13.7563, 100.5018], {
      icon: agentIcon,
      title: 'Agent',
      // draggable: true
    }).addTo(map);

    // วาดเส้นทาง static
    L.polyline(staticPath, {
      color: 'blue',
      weight: 3,
      opacity: 0.7,
      dashArray: '10, 10' // เส้นประ
    }).addTo(map);

    // เพิ่ม markers สำหรับแต่ละสถานี
    staticPath.forEach((point, index) => {
      L.circle([point.lat, point.lng], {
        color: 'red',
        fillColor: '#f03',
        fillOpacity: 0.5,
        radius: 100
      })
      .bindPopup(`Station ${index + 1}`)
      .addTo(map);
    });

    // Initialize WebSocket connection
    wsRef.current = new WebSocket('ws://localhost:8000/ws');
    
    // เมื่อได้รับข้อมูลตำแหน่ง (latitude และ longitude) จาก WebSocket จะเรียกฟังก์ชัน moveAgent เพื่อเคลื่อนที่ agent
    wsRef.current.onmessage = (event) => {
      // onmessage คือ callback function ที่จะถูกเรียกใช้งานทุกครั้งที่เซิร์ฟเวอร์ส่งข้อความมายัง WebSocket.
      const data = JSON.parse(event.data); // event.data คือ ข้อความดิบ (raw data) ที่ส่งมาจากเซิร์ฟเวอร์.
      moveAgent(data.lat, data.lng); //  แปลงข้อความ JSON ที่ส่งมาจากเซิร์ฟเวอร์ให้เป็น วัตถุ (object) เพื่อให้สามารถเข้าถึงข้อมูลภายในได้ง่าย.
    };

    wsRef.current.onopen = () => {
      console.log("WebSocket connection established");
    };
    wsRef.current.onerror = (error) => {
        console.error("WebSocket error:", error);
    };

    // Add mousemove listener
    map.on('mousemove', (e) => {
      setCoordinates({
        lat: e.latlng.lat.toFixed(6),
        lng: e.latlng.lng.toFixed(6)
      });
    });

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      map.remove();
    };
  }, []);

  // Function to move agent with animation
  const moveAgent = (targetLat, targetLng) => {
    if (!agentRef.current) return; //ถ้า agentRef.current ไม่มีค่า

    const start = agentRef.current.getLatLng(); // ตำแหน่งเริ่มต้น (lat, lng)
    const end = L.latLng(targetLat, targetLng); // ตำแหน่งเป้าหมาย (lat, lng)

    
    // แอนิเมชันจะแบ่งการเคลื่อนที่ออกเป็น 50 เฟรม เพื่อให้การเคลื่อนที่ดูนุ่มนวล
    const frames = 50; // จำนวนเฟรมทั้งหมด
    let frame = 0; // ตัวนับเฟรมเริ่มต้นที่ 0
    // ตัวแปร frame ใช้ติดตามจำนวนเฟรมที่เคลื่อนไปแล้ว


    const animate = () => {
      frame++;
      // frame++; // เพิ่มตัวนับเฟรมทีละ 1
      
      const progress = frame / frames; // คำนวณความคืบหน้า (progress) เป็นเปอร์เซ็นต์
      const lat = start.lat + (end.lat - start.lat) * progress; // ตำแหน่ง lat ใหม่
      const lng = start.lng + (end.lng - start.lng) * progress; // ตำแหน่ง lng ใหม่
      
      agentRef.current.setLatLng([lat, lng]);
      
      if (frame < frames) {
        requestAnimationFrame(animate);  // ถ้าเฟรมยังไม่ครบ เรียก animate อีกครั้ง
      }
    };
    
    animate(); // เรียกฟังก์ชัน animate ครั้งแรกเพื่อเริ่มแอนิเมชัน

  };

  // Function to start agent movement along static path
  const startAgentMovement = () => {
    if (isMoving) return;
    
    setIsMoving(true);
    let currentIndex = 0;

    const moveNext = () => {
      if (currentIndex < staticPath.length) {
        const point = staticPath[currentIndex];
        moveAgent(point.lat, point.lng);
        currentIndex++;
        setTimeout(moveNext, 2000); // รอ 2 วินาทีระหว่างแต่ละจุด
      } else {
        setIsMoving(false);
      }
    };

    moveNext();
  };

  // Function to reset agent position
  const resetPosition = () => {
    if (agentRef.current) {
      // ทำหน้าที่ตรวจสอบว่า agentRef.current มีค่าอยู่หรือไม่
      agentRef.current.setLatLng([13.7563, 100.5018]); // กลับไปที่สยาม
    }
  };

  // Styles
  const controlPanelStyle = {
    position: 'absolute',
    top: '20px',
    left: '20px',
    backgroundColor: 'white',
    padding: '15px',
    borderRadius: '5px',
    boxShadow: '0 2px 5px rgba(0,0,0,0.2)',
    zIndex: 1000
  };

  const buttonStyle = {
    padding: '8px 16px',
    margin: '5px',
    borderRadius: '4px',
    border: 'none',
    cursor: 'pointer',
    fontWeight: 'bold',
    color: 'white'
  };

  const startButtonStyle = {
    ...buttonStyle,
    backgroundColor: isMoving ? '#ccc' : '#4CAF50'
  };

  const resetButtonStyle = {
    ...buttonStyle,
    backgroundColor: isMoving ? '#ccc' : '#2196F3'
  };

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
      <div style={controlPanelStyle}>
        <div style={{ marginBottom: '10px' }}>
          <strong>Current Position:</strong><br />
          Lat: {coordinates.lat}, Lng: {coordinates.lng}
        </div>
        <div>
          <button 
            onClick={startAgentMovement}
            disabled={isMoving}
            style={startButtonStyle}
          >
            {isMoving ? 'Moving...' : 'Start Movement'}
          </button>
          <button 
            onClick={resetPosition}
            style={resetButtonStyle}
            disabled={isMoving}
          >
            Reset Position
          </button>
        </div>
      </div>
    </div>
  );
};

export default LeafletMap;