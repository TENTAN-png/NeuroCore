import React, { useState, useRef, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Cylinder, Float, Environment, ContactShadows } from '@react-three/drei';
import { Activity, Beaker, Dna, Network, ChevronRight, Search, ActivitySquare } from 'lucide-react';
import diseasesData from './data/diseases.json';
import './index.css';

// 3D Molecule Component
const Molecule = () => {
  const group = useRef();
  
  useFrame((state) => {
    group.current.rotation.y = state.clock.elapsedTime * 0.2;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.2;
  });

  return (
    <group ref={group}>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
        <Sphere position={[0, 0, 0]} args={[0.5, 32, 32]}>
          <meshStandardMaterial color="#2563eb" metalness={0.8} roughness={0.2} />
        </Sphere>
        <Cylinder position={[0.8, 0.8, 0]} args={[0.1, 0.1, 2]} rotation={[0, 0, -Math.PI / 4]}>
          <meshStandardMaterial color="#94a3b8" metalness={0.5} />
        </Cylinder>
        <Sphere position={[1.5, 1.5, 0]} args={[0.3, 32, 32]}>
          <meshStandardMaterial color="#14b8a6" metalness={0.8} roughness={0.2} />
        </Sphere>
        <Cylinder position={[-0.8, 0.8, 0]} args={[0.1, 0.1, 2]} rotation={[0, 0, Math.PI / 4]}>
          <meshStandardMaterial color="#94a3b8" metalness={0.5} />
        </Cylinder>
        <Sphere position={[-1.5, 1.5, 0]} args={[0.4, 32, 32]}>
          <meshStandardMaterial color="#ef4444" metalness={0.8} roughness={0.2} />
        </Sphere>
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
  const [activeTab, setActiveTab] = useState("Drug Candidate");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDisease, setSelectedDisease] = useState(diseasesData[0]);
  const [searchResults, setSearchResults] = useState([]);

  const handleSearch = (e) => {
    const query = e.target.value;
    setSearchQuery(query);
    if (query.length > 0) {
      const results = diseasesData.filter(d => 
        d.name.toLowerCase().includes(query.toLowerCase()) || 
        d.mutated_gene.toLowerCase().includes(query.toLowerCase())
      );
      setSearchResults(results);
    } else {
      setSearchResults([]);
    }
  };

  const selectDisease = (disease) => {
    setSelectedDisease(disease);
    setSearchQuery("");
    setSearchResults([]);
  };

  const tabs = [
    { icon: <Activity size={18} />, label: "Genomics Profiling" },
    { icon: <Beaker size={18} />, label: "3D Protein Fold" },
    { icon: <Dna size={18} />, label: "Drug Candidate" },
    { icon: <Network size={18} />, label: "Bioproduction" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex overflow-hidden font-sans">
      
      {/* Sidebar */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/50 backdrop-blur-xl flex flex-col z-20 relative">
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
            {tabs.map((item, i) => (
              <button 
                key={i} 
                onClick={() => setActiveTab(item.label)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === item.label 
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
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[500px] bg-blue-600/20 rounded-full blur-[120px] pointer-events-none z-0"></div>

        {/* Top Navbar with Functional Search */}
        <header className="h-20 border-b border-slate-800/50 flex items-center justify-between px-8 z-20 backdrop-blur-sm relative">
          <div className="relative w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type="text" 
              value={searchQuery}
              onChange={handleSearch}
              placeholder="Search diseases or genes (e.g. ALS, CFTR)..." 
              className="w-full bg-slate-900 border border-slate-700 rounded-full py-2 pl-10 pr-4 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-slate-200"
            />
            {/* Search Dropdown Results */}
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-lg shadow-xl overflow-hidden max-h-60 overflow-y-auto z-50">
                {searchResults.map((d, i) => (
                  <button 
                    key={i} 
                    onClick={() => selectDisease(d)}
                    className="w-full text-left px-4 py-3 hover:bg-blue-600 transition-colors text-sm border-b border-slate-700/50 last:border-0"
                  >
                    <div className="font-semibold text-white">{d.name}</div>
                    <div className="text-xs text-slate-400">Target: {d.mutated_gene}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm font-medium text-slate-400">Target: <span className="text-white font-bold">{selectedDisease.name} ({selectedDisease.mutated_gene})</span></div>
          </div>
        </header>

        {/* Dynamic Dashboard Area based on Active Tab */}
        <main className="flex-1 p-8 grid grid-cols-1 lg:grid-cols-3 gap-8 z-10 overflow-y-auto relative">
          
          {activeTab === "Drug Candidate" && (
            <>
              {/* Left Column */}
              <div className="space-y-6">
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
                  <h2 className="text-lg font-semibold text-white mb-6">Molecular Candidate</h2>
                  
                  <div className="space-y-4">
                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Compound ID</div>
                      <div className="font-mono text-sm text-blue-400 bg-slate-950 p-3 rounded-lg border border-slate-800">
                        {selectedDisease.drug_candidates[0]?.name || "Unknown"}
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Binding Affinity</div>
                      <div className="flex items-center gap-2">
                        <div className="text-2xl font-light text-white">{selectedDisease.drug_candidates[0]?.affinity || "-9.0"}</div>
                        <div className="text-sm text-teal-400">kcal/mol</div>
                      </div>
                    </div>

                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">ADMET Score</div>
                      <div className="w-full bg-slate-800 rounded-full h-2 mt-2">
                        <div className="bg-gradient-to-r from-blue-500 to-teal-400 h-2 rounded-full" style={{ width: `${(selectedDisease.drug_candidates[0]?.admet_score || 0.8) * 100}%` }}></div>
                      </div>
                    </div>
                  </div>

                  <button 
                    onClick={() => setActiveTab("Bioproduction")}
                    className="w-full mt-8 bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    Generate Biosynthesis Pathway <ChevronRight size={18} />
                  </button>
                </div>
              </div>

              {/* Right Column: 3D Canvas */}
              <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-2xl relative overflow-hidden flex flex-col backdrop-blur-sm min-h-[500px]">
                <div className="absolute top-6 left-6 z-10 pointer-events-none">
                  <h2 className="text-lg font-semibold text-white">Interactive 3D Structure</h2>
                  <p className="text-sm text-slate-400 mt-1">Generated via Three.js Engine</p>
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
                  <div className="bg-slate-950/80 backdrop-blur border border-slate-800 p-3 rounded-lg pointer-events-auto max-w-sm truncate">
                    <div className="text-xs text-slate-500 uppercase tracking-widest mb-1">SMILES string</div>
                    <div className="font-mono text-xs text-slate-300 truncate">
                      {selectedDisease.drug_candidates[0]?.smiles || "N/A"}
                    </div>
                  </div>
                </div>
              </div>
            </>
          )}

          {activeTab === "Genomics Profiling" && (
            <div className="lg:col-span-3 bg-slate-900/60 border border-slate-800 rounded-2xl p-8 backdrop-blur-md">
              <h2 className="text-2xl font-semibold text-white mb-6">Genomic Analysis</h2>
              <div className="grid grid-cols-2 gap-8">
                <div>
                  <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-2">Affected Target</h3>
                  <div className="text-3xl text-blue-400 font-bold mb-6">{selectedDisease.mutated_gene}</div>
                  <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider mb-2">Primary Tissue/Cell</h3>
                  <div className="text-xl text-white">{selectedDisease.cell_type}</div>
                </div>
                <div className="bg-slate-950 p-4 rounded-lg border border-slate-800 overflow-y-auto max-h-64">
                   <h3 className="text-slate-400 text-xs font-bold uppercase tracking-wider mb-2 sticky top-0 bg-slate-950 pb-2">Amino Acid Sequence</h3>
                   <div className="font-mono text-xs text-teal-500 break-all leading-relaxed">
                     {selectedDisease.sequence || "Fetching FASTA sequence..."}
                   </div>
                </div>
              </div>
            </div>
          )}

          {activeTab === "3D Protein Fold" && (
            <div className="lg:col-span-3 bg-slate-900/60 border border-slate-800 rounded-2xl p-8 backdrop-blur-md flex flex-col items-center justify-center min-h-[400px]">
               <ActivitySquare size={64} className="text-blue-500 mb-4 animate-pulse" />
               <h2 className="text-2xl font-semibold text-white mb-2">AlphaFold / ESMFold API</h2>
               <p className="text-slate-400 text-center max-w-md">The 3D protein structure viewer requires the Py3Dmol engine which is currently active on the Streamlit dashboard.</p>
            </div>
          )}

          {activeTab === "Bioproduction" && (
            <div className="lg:col-span-3 bg-slate-900/60 border border-slate-800 rounded-2xl p-8 backdrop-blur-md">
              <h2 className="text-2xl font-semibold text-white mb-6">Metabolic Biosynthesis Pathway</h2>
              <div className="flex items-center gap-4 mb-8">
                <div className="px-4 py-2 bg-teal-500/10 text-teal-400 border border-teal-500/20 rounded-lg font-medium">
                  Host: {selectedDisease.biosynthesis?.organism || "Saccharomyces cerevisiae"}
                </div>
              </div>
              <div className="relative">
                <div className="absolute top-1/2 left-0 right-0 h-1 bg-slate-800 -translate-y-1/2 z-0"></div>
                <div className="flex justify-between relative z-10">
                  {selectedDisease.biosynthesis?.pathway_nodes?.map((node, i) => (
                    <div key={i} className="flex flex-col items-center gap-4">
                      <div className={`w-12 h-12 rounded-full flex items-center justify-center border-4 border-slate-950 shadow-xl ${i === selectedDisease.biosynthesis.pathway_nodes.length - 1 ? 'bg-teal-500' : 'bg-blue-600'}`}>
                        {i + 1}
                      </div>
                      <div className="text-sm font-semibold text-slate-300">{node}</div>
                    </div>
                  )) || <div className="text-slate-500 italic">No pathway data available for this target.</div>}
                </div>
              </div>
            </div>
          )}

        </main>
      </div>
    </div>
  );
}

export default App;
