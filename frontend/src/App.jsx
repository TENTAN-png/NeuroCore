import React, { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Cylinder, Float, Environment, ContactShadows } from '@react-three/drei';
import { Activity, Beaker, Dna, Network, ChevronRight, Search } from 'lucide-react';
import './index.css';

// 3D Molecule Component
const Molecule = () => {
  const group = useRef();
  
  // Rotate the entire molecule slowly
  useFrame((state) => {
    group.current.rotation.y = state.clock.elapsedTime * 0.2;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.2;
  });

  return (
    <group ref={group}>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
        {/* Core Atom */}
        <Sphere position={[0, 0, 0]} args={[0.5, 32, 32]}>
          <meshStandardMaterial color="#2563eb" metalness={0.8} roughness={0.2} />
        </Sphere>
        
        {/* Branch 1 */}
        <Cylinder position={[0.8, 0.8, 0]} args={[0.1, 0.1, 2]} rotation={[0, 0, -Math.PI / 4]}>
          <meshStandardMaterial color="#94a3b8" metalness={0.5} />
        </Cylinder>
        <Sphere position={[1.5, 1.5, 0]} args={[0.3, 32, 32]}>
          <meshStandardMaterial color="#14b8a6" metalness={0.8} roughness={0.2} />
        </Sphere>

        {/* Branch 2 */}
        <Cylinder position={[-0.8, 0.8, 0]} args={[0.1, 0.1, 2]} rotation={[0, 0, Math.PI / 4]}>
          <meshStandardMaterial color="#94a3b8" metalness={0.5} />
        </Cylinder>
        <Sphere position={[-1.5, 1.5, 0]} args={[0.4, 32, 32]}>
          <meshStandardMaterial color="#ef4444" metalness={0.8} roughness={0.2} />
        </Sphere>

        {/* Branch 3 */}
        <Cylinder position={[0, -1, 0.8]} args={[0.1, 0.1, 2]} rotation={[Math.PI / 4, 0, 0]}>
          <meshStandardMaterial color="#94a3b8" metalness={0.5} />
        </Cylinder>
        <Sphere position={[0, -1.8, 1.5]} args={[0.3, 32, 32]}>
          <meshStandardMaterial color="#eab308" metalness={0.8} roughness={0.2} />
        </Sphere>
      </Float>
    </group>
  );
};

function App() {
  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex overflow-hidden font-sans">
      
      {/* Sidebar */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl flex flex-col z-10">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3 text-blue-500 font-bold text-xl tracking-tight">
            <Dna size={28} />
            BioGenesis
          </div>
          <div className="mt-2 text-xs font-semibold text-teal-400 bg-teal-400/10 inline-block px-2 py-1 rounded">
            SYSTEM ONLINE
          </div>
        </div>
        
        <div className="p-4 flex-1">
          <div className="text-xs font-bold text-slate-500 tracking-wider mb-4 mt-4">PIPELINE STAGES</div>
          <nav className="space-y-2">
            {[
              { icon: <Activity size={18} />, label: "Genomics Profiling", active: false },
              { icon: <Beaker size={18} />, label: "3D Protein Fold", active: false },
              { icon: <Dna size={18} />, label: "Drug Candidate", active: true },
              { icon: <Network size={18} />, label: "Bioproduction", active: false },
            ].map((item, i) => (
              <button 
                key={i} 
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  item.active 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/50' 
                  : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                }`}
              >
                {item.icon}
                {item.label}
              </button>
            ))}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <div className="flex-1 flex flex-col relative">
        {/* Background Ambient Glow */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none"></div>

        {/* Top Navbar */}
        <header className="h-20 border-b border-slate-800/50 flex items-center justify-between px-8 z-10 backdrop-blur-sm">
          <div className="relative w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type="text" 
              placeholder="Search target disease..." 
              className="w-full bg-slate-900 border border-slate-700 rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-slate-200"
            />
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm font-medium text-slate-400">Target: <span className="text-white">Glioblastoma (EGFR)</span></div>
          </div>
        </header>

        {/* Dashboard Area */}
        <main className="flex-1 p-8 grid grid-cols-1 lg:grid-cols-3 gap-8 z-10 overflow-y-auto">
          
          {/* Left Column: Metadata */}
          <div className="space-y-6">
            <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
              <h2 className="text-lg font-semibold text-white mb-6">Molecular Candidate</h2>
              
              <div className="space-y-4">
                <div>
                  <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Compound ID</div>
                  <div className="font-mono text-sm text-blue-400 bg-slate-950 p-3 rounded-lg border border-slate-800">EGFR-Inhibitor-v4</div>
                </div>
                
                <div>
                  <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Binding Affinity</div>
                  <div className="flex items-center gap-2">
                    <div className="text-2xl font-light text-white">-9.8</div>
                    <div className="text-sm text-teal-400">kcal/mol</div>
                  </div>
                </div>

                <div>
                  <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">ADMET Score</div>
                  <div className="w-full bg-slate-800 rounded-full h-2 mt-2">
                    <div className="bg-gradient-to-r from-blue-500 to-teal-400 h-2 rounded-full" style={{ width: '85%' }}></div>
                  </div>
                </div>
              </div>

              <button className="w-full mt-8 bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2">
                Generate Biosynthesis Pathway <ChevronRight size={18} />
              </button>
            </div>
          </div>

          {/* Right Column: 3D Canvas */}
          <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-2xl relative overflow-hidden flex flex-col backdrop-blur-sm min-h-[500px]">
            <div className="absolute top-6 left-6 z-10">
              <h2 className="text-lg font-semibold text-white">Interactive 3D Structure</h2>
              <p className="text-sm text-slate-400 mt-1">Generated via RDKit & Three.js</p>
            </div>
            
            <div className="flex-1 w-full h-full cursor-grab active:cursor-grabbing">
              <Canvas camera={{ position: [0, 0, 6], fov: 45 }}>
                <ambientLight intensity={0.5} />
                <directionalLight position={[10, 10, 5]} intensity={1} />
                <Environment preset="city" />
                <Molecule />
                <OrbitControls enableZoom={true} autoRotate={true} autoRotateSpeed={0.5} />
                <ContactShadows position={[0, -2.5, 0]} opacity={0.4} scale={10} blur={2} far={4} />
              </Canvas>
            </div>
            
            <div className="absolute bottom-6 left-6 right-6 flex justify-between items-end pointer-events-none">
              <div className="bg-slate-950/80 backdrop-blur border border-slate-800 p-3 rounded-lg pointer-events-auto">
                <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">SMILES string</div>
                <div className="font-mono text-xs text-slate-300">CC1=C(C=C(C=C1)NC(=O)...</div>
              </div>
              <div className="flex gap-2 pointer-events-auto">
                <button className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm transition-colors border border-slate-700">Export PDB</button>
                <button className="bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg text-sm transition-colors border border-slate-700">Full Screen</button>
              </div>
            </div>
          </div>
          
        </main>
      </div>
    </div>
  );
}

export default App;
