import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Trail } from '@react-three/drei';
import * as THREE from 'three';

// A highly dynamic, aesthetic 3D representation of a protein folding
function RotatingProtein() {
  const groupRef = useRef();

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (groupRef.current) {
      groupRef.current.rotation.y = t * 0.5;
      groupRef.current.rotation.x = t * 0.2;
    }
  });

  // Generate a procedural chain simulating a protein backbone
  const atoms = [];
  for (let i = 0; i < 50; i++) {
    const x = Math.sin(i * 0.5) * 3 + Math.sin(i * 0.1) * 2;
    const y = Math.cos(i * 0.3) * 3;
    const z = Math.sin(i * 0.7) * 3 + Math.cos(i * 0.2) * 2;
    atoms.push([x, y, z]);
  }

  return (
    <group ref={groupRef}>
      <Trail width={2} length={10} color={new THREE.Color(0x10b981)} attenuation={(t) => t * t}>
        {atoms.map((pos, idx) => (
          <Sphere key={idx} position={pos} args={[0.3, 16, 16]}>
            <meshStandardMaterial 
              color={idx % 3 === 0 ? "#3b82f6" : "#10b981"} 
              roughness={0.2} 
              metalness={0.8} 
            />
          </Sphere>
        ))}
      </Trail>
      
      {/* Connective bonds */}
      {atoms.map((pos, idx) => {
        if (idx === atoms.length - 1) return null;
        const nextPos = atoms[idx + 1];
        const distance = new THREE.Vector3(...pos).distanceTo(new THREE.Vector3(...nextPos));
        const center = new THREE.Vector3(...pos).lerp(new THREE.Vector3(...nextPos), 0.5);
        
        return (
          <mesh key={`bond-${idx}`} position={center} lookAt={() => new THREE.Vector3(...nextPos)}>
            <cylinderGeometry args={[0.08, 0.08, distance, 8]} />
            <meshStandardMaterial color="#94a3b8" />
          </mesh>
        );
      })}
    </group>
  );
}

export default function ProteinViewer() {
  return (
    <div className="w-full h-full bg-slate-900 rounded-xl overflow-hidden shadow-2xl border border-slate-700">
      <Canvas camera={{ position: [0, 0, 10], fov: 60 }}>
        <ambientLight intensity={0.5} />
        <spotLight position={[10, 10, 10]} angle={0.15} penumbra={1} intensity={2} />
        <pointLight position={[-10, -10, -10]} intensity={1} color="#3b82f6" />
        
        <RotatingProtein />
        <OrbitControls enableZoom={true} autoRotate autoRotateSpeed={1.5} />
      </Canvas>
    </div>
  );
}
