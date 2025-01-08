import React, { useEffect, useState } from 'react';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';
import '@geoman-io/leaflet-geoman-free/dist/leaflet-geoman.css';

delete L.Icon.Default.prototype._getIconUrl;

L.Icon.Default.mergeOptions({
    iconRetinaUrl: require('leaflet/dist/images/marker-icon-2x.png'),
    iconUrl: require('leaflet/dist/images/marker-icon.png'),
    shadowUrl: require('leaflet/dist/images/marker-shadow.png'),
});


const MapComponent = () => {
    const [latLngList, setLatLngList] = useState([]);

    useEffect(() => {
        // Import Leaflet และ Geoman libraries
        const L = require('leaflet');
        require('@geoman-io/leaflet-geoman-free');

        // สร้างแผนที่
        const map = L.map('map').setView([13.736717, 100.523186], 13); // Bangkok

        // เพิ่ม Tile Layer (แผนที่พื้นฐาน)
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap contributors',
        }).addTo(map);

        // เปิดใช้งาน Geoman
        map.pm.addControls({
            position: 'topleft', // ตำแหน่งของปุ่มเครื่องมือ
            drawMarker: true,
            drawPolygon: true,
            drawPolyline: true,
            editMode: true,
            dragMode: true,
            cutPolygon: true,
            removalMode: true,
        });

        // Event: เมื่อผู้ใช้สร้างรูปร่าง
        map.on('pm:create', (e) => {
            // if (e.layer instanceof L.Polygon || e.layer instanceof L.Polyline) {
            //     const latlngs = e.layer.getLatLngs();
            //     const formattedLatLngs = latlngs[0].map((point) => ({
            //         lat: point.lat,
            //         lng: point.lng,
            //     }));
            //     console.log('LatLng List:', formattedLatLngs);
            //     setLatLngList(formattedLatLngs);
            //     sendCoordinatesToBackend(formattedLatLngs);
            // } else if (e.layer instanceof L.Marker) {
            //     const latlng = e.layer.getLatLng();
            //     const formattedLatLng = [{ lat: latlng.lat, lng: latlng.lng }];
            //     console.log('LatLng List (Marker):', formattedLatLng);
            //     setLatLngList(formattedLatLng);
            //     sendCoordinatesToBackend(formattedLatLng);
            // }
            
            console.log('Shape created:', e.layer);
            sendCoordinatesToBackend( e.layer);
        });

        // Event: เมื่อผู้ใช้ลบรูปร่าง
        map.on('pm:remove', () => {
            console.log('Shape removed');
            setLatLngList([]);
            console.log("latLngList:",latLngList);
            
        });

        // Cleanup map instance on component unmount
        return () => {
            map.remove();
        };
    }, [latLngList]); // เพิ่ม latLngList ลงใน dependency array

    // Function: ส่งพิกัดไปยัง Backend
    const sendCoordinatesToBackend = (latLngList) => {
        console.log("sendCoordinatesToBackend𓇼🧉❀🐚𓆉︎ ࿔*:･☾𓇼🧉❀🐚𓆉︎ ࿔*:･☾");
        
        console.log("latLngList" , latLngList);
        
        // fetch('http://127.0.0.1:8000/process', {
        //     method: 'POST',
        //     headers: {
        //         'Content-Type': 'application/json',
        //     },
        //     body: JSON.stringify(latLngList), // ส่งพิกัดเป็น JSON
        // })
        //     .then((response) => response.json())
        //     .then((data) => {
        //         console.log('Response from Backend:', data);
        //     })
        //     .catch((error) => {
        //         console.error('Error:', error);
        //     });
    };

    return (
        <div>
            <div id="map" style={{ height: '100vh' }}></div>
        </div>
    );
};

export default MapComponent;
