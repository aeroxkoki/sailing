import React from 'react';

interface LayerItem {
  id: string;
  label: string;
  isVisible: boolean;
  icon?: React.ReactNode;
  color?: string;
}

interface LayerControlProps {
  layers: LayerItem[];
  onLayerToggle: (id: string, isVisible: boolean) => void;
  className?: string;
}

const LayerControl: React.FC<LayerControlProps> = ({
  layers,
  onLayerToggle,
  className = '',
}) => {
  return (
    <div className={`bg-gray-900 bg-opacity-80 backdrop-filter backdrop-blur-sm rounded-lg p-3 ${className}`}>
      <h3 className="text-sm font-medium text-gray-300 mb-2">レイヤー表示</h3>
      <div className="space-y-2">
        {layers.map((layer) => (
          <div key={layer.id} className="flex items-center justify-between">
            <div className="flex items-center">
              {layer.icon && (
                <span className="mr-2 text-gray-400">{layer.icon}</span>
              )}
              {layer.color && (
                <span 
                  className="w-3 h-3 rounded-full mr-2" 
                  style={{ backgroundColor: layer.color }}
                />
              )}
              <span className="text-sm text-gray-300">{layer.label}</span>
            </div>
            <button
              className={`w-10 h-5 rounded-full flex items-center transition duration-300 ease-in-out focus:outline-none shadow ${
                layer.isVisible ? 'bg-blue-600 justify-end' : 'bg-gray-700 justify-start'
              }`}
              onClick={() => onLayerToggle(layer.id, !layer.isVisible)}
            >
              <span className={`bg-white w-4 h-4 rounded-full shadow transform transition duration-300 ease-in-out ${
                layer.isVisible ? 'translate-x-0.5' : '-translate-x-0.5'
              }`}></span>
            </button>
          </div>
        ))}
      </div>
    </div>
  );
};

export default LayerControl;
