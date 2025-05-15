import React, { useState, useEffect } from 'react';

const WeaponAssemblyDiagram = () => {
  const [selectedWeapon, setSelectedWeapon] = useState('sword');

  // Define different assembly structures
  const weaponStructures = {
    sword: [
      { type: 'pommel', y: 0, color: '#B87333', label: 'Pommel' },
      { type: 'handle', y: 50, color: '#8B4513', label: 'Handle' },
      { type: 'guard', y: 100, color: '#FFD700', label: 'Guard' },
      { type: 'blade', y: 150, color: '#C0C0C0', label: 'Blade' },
    ],
    axe: [
      { type: 'pommel', y: 0, color: '#B87333', label: 'Pommel' },
      { type: 'handle', y: 50, color: '#8B4513', label: 'Handle' },
      { type: 'head', y: 150, color: '#A52A2A', label: 'Head' },
    ],
    gun: [
      { type: 'handle', y: 0, color: '#556B2F', label: 'Grip' },
      { type: 'trigger', y: 50, color: '#708090', label: 'Trigger' },
      { type: 'body', y: 75, color: '#696969', label: 'Body' },
      { type: 'barrel', y: 125, color: '#696969', label: 'Barrel' },
      { type: 'sight', y: 150, color: '#2F4F4F', label: 'Sight' },
      { type: 'magazine', y: 25, color: '#778899', label: 'Magazine' },
    ],
  };

  const nodeNetwork = () => {
    const structure = weaponStructures[selectedWeapon];
    
    return (
      <svg width="600" height="400" viewBox="0 0 600 400" className="bg-gray-800 rounded-lg">
        {/* Network lines */}
        <line x1="120" y1="200" x2="220" y2="200" stroke="#666" strokeWidth="2" />
        <line x1="320" y1="200" x2="420" y2="200" stroke="#666" strokeWidth="2" />
        <line x1="520" y1="200" x2="570" y2="200" stroke="#666" strokeWidth="2" />
        
        {/* Input nodes - Part files */}
        <g transform="translate(70,200)">
          {structure.map((part, index) => (
            <g key={index} transform={`translate(0,${(index-Math.floor(structure.length/2))*40})`}>
              <rect x="-40" y="-15" width="80" height="30" rx="5" fill="#444" stroke="#888" />
              <text x="0" y="5" fontSize="12" fill="white" textAnchor="middle">{`FILE_${part.type}`}</text>
            </g>
          ))}
        </g>
        
        {/* Transform nodes */}
        <g transform="translate(270,200)">
          {structure.map((part, index) => (
            <g key={index} transform={`translate(0,${(index-Math.floor(structure.length/2))*40})`}>
              <rect x="-40" y="-15" width="80" height="30" rx="5" fill="#444" stroke="#888" />
              <text x="0" y="5" fontSize="12" fill="white" textAnchor="middle">{`XFORM_${part.type}`}</text>
            </g>
          ))}
          
          {/* Links from File to Transform */}
          {structure.map((part, index) => (
            <path 
              key={`link-${index}`} 
              d={`M 40 ${(index-Math.floor(structure.length/2))*40} C 60 ${(index-Math.floor(structure.length/2))*40}, 
                    140 ${(index-Math.floor(structure.length/2))*40}, 160 ${(index-Math.floor(structure.length/2))*40}`} 
              fill="none" 
              stroke="#666" 
              strokeWidth="2"
            />
          ))}
        </g>
        
        {/* Merge node */}
        <g transform="translate(470,200)">
          <rect x="-40" y="-25" width="80" height="50" rx="5" fill="#555" stroke="#888" />
          <text x="0" y="5" fontSize="12" fill="white" textAnchor="middle">MERGE_Parts</text>
          
          {/* Input connections */}
          {structure.map((part, index) => (
            <line 
              key={`merge-in-${index}`}
              x1="-50" 
              y1={`${(index-Math.floor(structure.length/2))*15}`} 
              x2="-40" 
              y2={`${(index-Math.floor(structure.length/2))*15}`} 
              stroke="#666" 
              strokeWidth="2"
            />
          ))}
          
          {/* Links from Transform to Merge */}
          {structure.map((part, index) => (
            <path 
              key={`link2-${index}`} 
              d={`M 330 ${(index-Math.floor(structure.length/2))*40} 
                  C 350 ${(index-Math.floor(structure.length/2))*40}, 
                    380 ${(index-Math.floor(structure.length/2))*15}, 
                    420 ${(index-Math.floor(structure.length/2))*15}`} 
              fill="none" 
              stroke="#666" 
              strokeWidth="2"
            />
          ))}
        </g>
        
        {/* Output node */}
        <g transform="translate(570,200)">
          <rect x="-40" y="-15" width="80" height="30" rx="5" fill="#3a6" stroke="#4b7" />
          <text x="0" y="5" fontSize="12" fill="white" textAnchor="middle">OUTPUT_Weapon</text>
        </g>
      </svg>
    );
  };

  const weaponPreview = () => {
    const structure = weaponStructures[selectedWeapon];
    const maxHeight = 250;
    
    return (
      <svg width="250" height={maxHeight} viewBox="0 0 100 250" className="bg-gray-700 rounded-lg">
        {/* Weapon parts */}
        {structure.map((part, index) => (
          <g key={index}>
            <rect 
              x="35" 
              y={part.y} 
              width="30" 
              height={index < structure.length - 1 ? structure[index+1].y - part.y : 50} 
              fill={part.color} 
              stroke="#000"
            />
            <line 
              x1="20" 
              y1={part.y + 25} 
              x2="30" 
              y2={part.y + 25} 
              stroke="#fff" 
              strokeWidth="1" 
            />
            <text x="15" y={part.y + 30} fontSize="10" fill="white" textAnchor="end">{part.label}</text>
          </g>
        ))}
      </svg>
    );
  };

  return (
    <div className="flex flex-col p-4 space-y-6">
      <h2 className="text-2xl font-bold text-center">Weapon Assembly Structure</h2>
      
      <div className="flex justify-center space-x-4">
        <button 
          onClick={() => setSelectedWeapon('sword')}
          className={`px-4 py-2 rounded ${selectedWeapon === 'sword' ? 'bg-blue-600' : 'bg-gray-600'}`}
        >
          Sword
        </button>
        <button 
          onClick={() => setSelectedWeapon('axe')}
          className={`px-4 py-2 rounded ${selectedWeapon === 'axe' ? 'bg-blue-600' : 'bg-gray-600'}`}
        >
          Axe
        </button>
        <button 
          onClick={() => setSelectedWeapon('gun')}
          className={`px-4 py-2 rounded ${selectedWeapon === 'gun' ? 'bg-blue-600' : 'bg-gray-600'}`}
        >
          Gun
        </button>
      </div>
      
      <div className="flex flex-col md:flex-row space-y-4 md:space-y-0 md:space-x-4">
        <div className="flex-1">
          <div className="p-2 bg-gray-900 rounded-lg">
            <h3 className="text-lg font-bold mb-2">Weapon Structure</h3>
            {weaponPreview()}
            <div className="mt-2 text-sm text-gray-400">
              Each weapon type has its own structure of parts that will be assembled vertically.
            </div>
          </div>
        </div>
        
        <div className="flex-1">
          <div className="p-2 bg-gray-900 rounded-lg">
            <h3 className="text-lg font-bold mb-2">Node Network</h3>
            {nodeNetwork()}
            <div className="mt-2 text-sm text-gray-400">
              This diagram shows how the HDA creates a node network to import, transform, and assemble the weapon parts.
            </div>
          </div>
        </div>
      </div>
      
      <div className="bg-gray-900 p-4 rounded-lg">
        <h3 className="text-lg font-bold mb-2">Assembly Process</h3>
        <ol className="list-decimal list-inside space-y-2">
          <li>Each part is imported using a <span className="text-blue-400">File</span> node</li>
          <li>Parts are positioned with <span className="text-blue-400">Transform</span> nodes based on API metadata</li>
          <li>All parts are combined in a <span className="text-blue-400">Merge</span> node</li>
          <li>The assembled weapon is output via the <span className="text-green-400">OUTPUT</span> node</li>
          <li>Each weapon type uses a different structure of parts and positions</li>
        </ol>
      </div>
    </div>
  );
};

export default WeaponAssemblyDiagram;
