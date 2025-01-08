import React, { useEffect, useRef, useState } from 'react';

const Claude = () => {
  const mapRef = useRef(null);
  const [coordinates, setCoordinates] = useState({ lat: 0, lng: 0 });

  useEffect(() => {
    // Load Google Maps Script
    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?libraries=visualization&key=AIzaSyCr-bzOX00C52hDhS_50Njb1pUyZhk3dvI`;
    // AIzaSyCr-bzOX00C52hDhS_50Njb1pUyZhk3dvI
    script.async = true;
    script.defer = true;
    script.addEventListener('load', initializeMap);
    document.body.appendChild(script);

    return () => {
      document.body.removeChild(script);
    };
  }, []);

  const initializeMap = () => {
    const map = new window.google.maps.Map(mapRef.current, {
      zoom: 13,
      center: { lat: 13.753804, lng: 100.498519 }
    });

    const markerIcon = {
      url: "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABUAAAAiCAYAAACwaJKDAAAABmJLR0QA/wD/AP+gvaeTAAACBklEQVRIia3VzUtUURgH4GdG/AiyZZShtWgXUbSIFtGqRYtqWRLhXyBYf0K6MaJQ2gRtayHtijYpleHKSCgIcRHoIiOSKEzLKea0OOeqTfPlzPzg5Qwz9zz3nXPvPTeneo7gNA4gjyI+Ygbva8z9L2cxi9BHOE+4msY+gliz6biayWE0R7GfMEcoEkJJzRH6CbnY+WiaVxEc6yY8KQOVq8eE7tj1WCV4qIswUyeY1QyhK8JDpWAP1m7vEMzqTkTXkrOZkYOEQoNogXAowiPE2wQuDqC9nktZJu0YSE72XRs2phrsMqup2OkG2vLpRB19DXaZJc3vQHv294Um0e3z8yigsNQkmuYXUMie5/npJtE0fz55YLiXsNHELdUbV2B4+4n2Y/Vmg+itCK4m558MdhBe7hCcJnRGdLDS0ox3E17XCb4h7IngeLX1zuFhD2G5BriytY4Tqmx9WXbh3Tnl99KsLkdwAbtrgVmO4/eDCuCkzd3/TL1glru9hF8lYJFwMoKPdgrCXqzfL0GfR7CIo42gcO9YCXopolONgnAC4W0Cv9l8dVxpBoWFGwmdiOC6Glc8X+3HlKeT6cOzOLzAjyaaBBc602ZzOHZ6vVkQ9kl7Qi6ip1qBwpdrEfwjPnFVU8+awuKrOC7hZ6vQlQ9baM3Ui379HsfVVqKf07jcSvRTGhfrOfgvIP3ECS77BDoAAAAASUVORK5CYII=",
      labelOrigin: new window.google.maps.Point(10, 11)
    };

    // Add markers
    const markers = [
      { position: { lat: 13.753804, lng: 100.498519 }, title: "Start" },
      { position: { lat: 13.752669, lng: 100.499912 }, title: "End" },
      { position: { lat: 13.752643, lng: 100.498330 } },
      { position: { lat: 13.753597, lng: 100.500008 } }
    ];

    markers.forEach(markerData => {
      new window.google.maps.Marker({
        position: markerData.position,
        title: markerData.title,
        icon: markerIcon,
        map: map
      });
    });

    // Add polyline
    const pathCoordinates = [
      { lat: 13.753804, lng: 100.498519 },
      { lat: 13.752643, lng: 100.498330 },
      { lat: 13.752669, lng: 100.499912 },
      { lat: 13.753597, lng: 100.500008 }
    ];

    new window.google.maps.Polyline({
      path: pathCoordinates,
      geodesic: true,
      strokeColor: "#0000FF",
      strokeOpacity: 1.0,
      strokeWeight: 3,
      map: map
    });

    // Add mousemove listener
    map.addListener('mousemove', (event) => {
      const lat = event.latLng.lat().toFixed(6);
      const lng = event.latLng.lng().toFixed(6);
      setCoordinates({ lat, lng });
    });
  };

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
          fontSize: '14px'
        }}
      >
        Latitude: {coordinates.lat}, Longitude: {coordinates.lng}
      </div>
    </div>
  );
};

export default Claude;