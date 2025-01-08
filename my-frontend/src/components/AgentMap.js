import React, { useEffect, useRef, useState } from 'react';
import L from 'leaflet';
import '@geoman-io/leaflet-geoman-free';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';
import 'leaflet/dist/leaflet.css';

const AgentMap = () => {
  const mapRef = useRef(null);
  // const agentMarkerRef = useRef(null);
  // const [coordinates, setCoordinates] = useState({ lat: 0, lng: 0 });
  // const wsRef = useRef(null);

  const [agentMarker, setAgentMarker] = useState(null);
  
  useEffect(() => {
    // Initialize map
    const map = L.map(mapRef.current).setView([13.753804, 100.498519], 13);
    
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '© OpenStreetMap contributors'
    }).addTo(map);

    // Create agent marker
    // agentMarkerRef.current = L.marker([13.753804, 100.498519], {
    //   icon: L.icon({
    //     iconUrl: 'agent-icon.png',  // ใส่ icon ของ agent
    //     iconSize: [32, 32]
    //   })
    // }).addTo(map);


    const marker = L.marker([13.753804, 100.498519]).addTo(map);
    setAgentMarker(marker);
    console.log("",agentMarker);
    
    // Connect to WebSocket
    const ws = new WebSocket('ws://127.0.0.1:8000/ws');

    ws.onmessage = (event) => {
      const position = JSON.parse(event.data);
      marker.setLatLng([position.lat, position.lng]);
    };

    return () => {
      ws.close();
      map.remove();
    };



    // // Connect to WebSocket
    // wsRef.current = new WebSocket('ws://localhost:8000/ws');
    
    // wsRef.current.onmessage = (event) => {
    //   const data = JSON.parse(event.data);
      
    //   // Update agent position
    //   if (agentMarkerRef.current) {
    //     const newLatLng = [data.lat, data.lng];
    //     agentMarkerRef.current.setLatLng(newLatLng);
        
    //     // Optional: Smooth movement animation
    //     agentMarkerRef.current.slideTo(newLatLng, {
    //       duration: 1000,
    //       keepAtCenter: true
    //     });
    //   }
    // };

    // // Cleanup
    // return () => {
    //   if (wsRef.current) {
    //     wsRef.current.close();
    //   }
    //   map.remove();
    // };
  }, []);

  return (
    <div style={{ position: 'relative', width: '100%', height: '100vh' }}>
      <div ref={mapRef} style={{ width: '100%', height: '100%' }} />
      <div 
        style={{
          position: 'absolute',
          top: '10px',
          left: '10px',
          background: 'white',
          padding: '5px',
          borderRadius: '5px',
          fontSize: '14px',
          zIndex: 1000
        }}
      >
        {/* Agent Position: {coordinates.lat}, {coordinates.lng} */}
      </div>
    </div>
  );
};

export default AgentMap;