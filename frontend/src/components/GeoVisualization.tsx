import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import { FiMapPin } from 'react-icons/fi';
import { useAppSelector } from '../hooks/useAppSelector';
import 'leaflet/dist/leaflet.css';
import L from 'leaflet';

delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

const GeoVisualization: React.FC = () => {
  const { selectedNode } = useAppSelector(state => state.graph);
  
  const locations = selectedNode?.data?.addresses?.filter((addr: any) => 
    addr.latitude && addr.longitude
  ) || [];

  const defaultCenter: [number, number] = [37.7749, -122.4194];
  const center: [number, number] = locations.length > 0 
    ? [locations[0].latitude, locations[0].longitude]
    : defaultCenter;

  return (
    <div className="h-full bg-white dark:bg-dark-800 rounded-lg shadow overflow-hidden">
      <div className="p-4 border-b border-gray-200 dark:border-dark-700">
        <div className="flex items-center space-x-2">
          <FiMapPin className="text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            Geographic Distribution
          </h3>
        </div>
        <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
          {locations.length} location{locations.length !== 1 ? 's' : ''} found
        </p>
      </div>

      <div className="h-[calc(100%-80px)]">
        {locations.length > 0 ? (
          <MapContainer
            center={center}
            zoom={10}
            style={{ height: '100%', width: '100%' }}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            {locations.map((location: any, index: number) => (
              <Marker
                key={index}
                position={[location.latitude, location.longitude]}
              >
                <Popup>
                  <div className="p-2">
                    <p className="font-medium">{location.type}</p>
                    {location.city && <p className="text-sm">{location.city}</p>}
                    {location.state && <p className="text-sm">{location.state}</p>}
                    {location.country && <p className="text-sm">{location.country}</p>}
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        ) : (
          <div className="h-full flex items-center justify-center">
            <p className="text-gray-500 dark:text-gray-400">
              No geographic data available
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default GeoVisualization;
