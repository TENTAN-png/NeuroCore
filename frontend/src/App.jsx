import React, { useState, useRef, useEffect, useMemo } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { OrbitControls, Sphere, Cylinder, Float, Environment, ContactShadows } from '@react-three/drei';
import { Activity, Beaker, Dna, Network, ChevronRight, Search, Play, CheckCircle } from 'lucide-react';
import ReactFlow, { Background, Controls, MarkerType } from 'reactflow';
import 'reactflow/dist/style.css';
import diseasesData from './data/diseases.json';
import './index.css';

// 3D Molecule Component (Drug Candidate)
const Molecule = ({ step = 0 }) => {
  const group = useRef();
  useFrame((state) => {
    group.current.rotation.y = state.clock.elapsedTime * 0.2;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.2;
  });
  
  // Calculate dynamic properties based on the reaction step
  const scale = Math.min(1 + (step * 0.2), 1.8);
  const coreColor = step === 0 ? "#10b981" : step === 1 ? "#8b5cf6" : step > 1 ? "#2563eb" : "#2563eb";

  return (
    <group ref={group} scale={scale}>
      <Float speed={2} rotationIntensity={0.5} floatIntensity={1}>
        <Sphere position={[0, 0, 0]} args={[0.5, 32, 32]}><meshStandardMaterial color={coreColor} metalness={0.8} roughness={0.2} /></Sphere>
        
        {step >= 0 && (
          <>
            <Cylinder position={[0.8, 0.8, 0]} args={[0.1, 0.1, 2]} rotation={[0, 0, -Math.PI / 4]}><meshStandardMaterial color="#94a3b8" metalness={0.5} /></Cylinder>
            <Sphere position={[1.5, 1.5, 0]} args={[0.3, 32, 32]}><meshStandardMaterial color="#14b8a6" metalness={0.8} roughness={0.2} /></Sphere>
          </>
        )}
        
        {step >= 1 && (
          <>
            <Cylinder position={[-0.8, 0.8, 0]} args={[0.1, 0.1, 2]} rotation={[0, 0, Math.PI / 4]}><meshStandardMaterial color="#94a3b8" metalness={0.5} /></Cylinder>
            <Sphere position={[-1.5, 1.5, 0]} args={[0.4, 32, 32]}><meshStandardMaterial color="#ef4444" metalness={0.8} roughness={0.2} /></Sphere>
          </>
        )}
        
        {step >= 2 && (
          <>
            <Cylinder position={[0, -1, 0.8]} args={[0.1, 0.1, 2]} rotation={[Math.PI / 4, 0, 0]}><meshStandardMaterial color="#94a3b8" metalness={0.5} /></Cylinder>
            <Sphere position={[0, -1.8, 1.5]} args={[0.3, 32, 32]}><meshStandardMaterial color="#eab308" metalness={0.8} roughness={0.2} /></Sphere>
          </>
        )}
      </Float>
    </group>
  );
};

// ReactFlow Custom Node
const PathwayNode = ({ data }) => {
  return (
    <div className={`px-6 py-4 shadow-lg rounded-xl border-2 transition-all duration-300 ${
      data.status === 'completed' ? 'bg-green-900/50 border-green-500 text-green-300' :
      data.status === 'active' ? 'bg-orange-900/50 border-orange-500 text-orange-300 scale-110 shadow-orange-500/50' :
      'bg-slate-900 border-slate-700 text-slate-300'
    }`}>
      <div className="font-bold text-sm text-center">{data.label}</div>
    </div>
  );
};

const nodeTypes = { custom: PathwayNode };

function App() {
  const [activeTab, setActiveTab] = useState("Genomics Profiling");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDisease, setSelectedDisease] = useState(diseasesData[0]);
  const [searchResults, setSearchResults] = useState([]);

  // Bioproduction Animation State
  const [animStep, setAnimStep] = useState(-1);
  const [isPlaying, setIsPlaying] = useState(false);

  // iframe ref for 3Dmol
  const iframeRef = useRef(null);

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
    setAnimStep(-1);
    setIsPlaying(false);
  };

  // Sync 3Dmol iframe when tab changes or disease changes
  useEffect(() => {
    if (activeTab === "3D Protein Fold" && iframeRef.current) {
      iframeRef.current.contentWindow.postMessage({ type: 'LOAD_PDB', gene: selectedDisease.mutated_gene }, '*');
    }
  }, [activeTab, selectedDisease]);

  // Bioproduction Animation Loop
  useEffect(() => {
    let interval;
    const nodesCount = selectedDisease.biosynthesis?.pathway_nodes?.length || 0;
    
    if (isPlaying) {
      if (animStep < nodesCount) {
        interval = setInterval(() => {
          setAnimStep(prev => prev + 1);
        }, 1200); // 1.2 seconds per step like streamlit
      } else {
        setIsPlaying(false); // Stop when done
      }
    }
    return () => clearInterval(interval);
  }, [isPlaying, animStep, selectedDisease]);

  // ReactFlow Setup
  const pathwayNodes = useMemo(() => {
    const nodesList = selectedDisease.biosynthesis?.pathway_nodes || [];
    return nodesList.map((node, i) => ({
      id: `node-${i}`,
      type: 'custom',
      position: { x: i * 250, y: 100 },
      data: { 
        label: node, 
        status: animStep > i ? 'completed' : animStep === i ? 'active' : 'pending' 
      }
    }));
  }, [selectedDisease, animStep]);

  const pathwayEdges = useMemo(() => {
    const nodesList = selectedDisease.biosynthesis?.pathway_nodes || [];
    const edges = [];
    for (let i = 0; i < nodesList.length - 1; i++) {
      edges.push({
        id: `e-${i}-${i+1}`,
        source: `node-${i}`,
        target: `node-${i+1}`,
        animated: animStep === i, // animate the edge if current step is active
        style: { stroke: animStep > i ? '#22c55e' : animStep === i ? '#f97316' : '#475569', strokeWidth: 3 },
        markerEnd: { type: MarkerType.ArrowClosed, color: animStep > i ? '#22c55e' : animStep === i ? '#f97316' : '#475569' }
      });
    }
    return edges;
  }, [selectedDisease, animStep]);


  const tabs = [
    { icon: <Activity size={18} />, label: "Genomics Profiling" },
    { icon: <Beaker size={18} />, label: "3D Protein Fold" },
    { icon: <Dna size={18} />, label: "Drug Candidate" },
    { icon: <Network size={18} />, label: "Bioproduction" },
  ];

  return (
    <div className="min-h-screen bg-slate-950 text-slate-50 flex overflow-hidden font-sans selection:bg-blue-500/30">
      
      {/* Sidebar */}
      <div className="w-64 border-r border-slate-800 bg-slate-900/80 backdrop-blur-xl flex flex-col z-20">
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-center gap-3 text-blue-500 font-bold text-xl tracking-tight">
            <Dna size={28} />
            BioGenesis
          </div>
          <div className="mt-2 text-xs font-semibold text-teal-400 bg-teal-400/10 border border-teal-400/20 inline-block px-2 py-1 rounded">
            SYSTEM ONLINE
          </div>
        </div>
        
        <div className="p-4 flex-1">
          <div className="text-[10px] font-bold text-slate-500 tracking-widest uppercase mb-4 mt-4">Pipeline Stages</div>
          <nav className="space-y-1">
            {tabs.map((item, i) => (
              <button 
                key={i} 
                onClick={() => setActiveTab(item.label)}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all duration-200 ${
                  activeTab === item.label 
                  ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
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
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[1000px] h-[500px] bg-blue-600/10 rounded-full blur-[120px] pointer-events-none z-0"></div>

        {/* Top Navbar */}
        <header className="h-20 border-b border-slate-800/80 bg-slate-900/50 flex items-center justify-between px-8 z-20 backdrop-blur-md relative">
          <div className="relative w-96">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={18} />
            <input 
              type="text" 
              value={searchQuery}
              onChange={handleSearch}
              placeholder="Search diseases or target genes..." 
              className="w-full bg-slate-950/50 border border-slate-700 rounded-full py-2.5 pl-10 pr-4 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 text-slate-200 transition-all placeholder-slate-600"
            />
            {searchResults.length > 0 && (
              <div className="absolute top-full left-0 right-0 mt-2 bg-slate-800 border border-slate-700 rounded-xl shadow-2xl overflow-hidden max-h-60 overflow-y-auto z-50">
                {searchResults.map((d, i) => (
                  <button 
                    key={i} 
                    onClick={() => selectDisease(d)}
                    className="w-full flex justify-between items-center px-4 py-3 hover:bg-blue-600 transition-colors text-sm border-b border-slate-700/50 last:border-0"
                  >
                    <div className="font-semibold text-white">{d.name}</div>
                    <div className="text-xs bg-slate-900 px-2 py-1 rounded text-slate-300">Target: {d.mutated_gene}</div>
                  </button>
                ))}
              </div>
            )}
          </div>
          <div className="flex items-center gap-4">
            <div className="text-sm font-medium text-slate-400">Target Match: <span className="text-white bg-slate-800 px-3 py-1.5 rounded-full border border-slate-700 ml-2">{selectedDisease.name} ({selectedDisease.mutated_gene})</span></div>
          </div>
        </header>

        {/* Dashboard Content */}
        <main className="flex-1 p-8 overflow-y-auto relative z-10">
          
          {/* STAGE 1: GENOMICS */}
          {activeTab === "Genomics Profiling" && (
            <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              <h2 className="text-2xl font-semibold text-white">Stage 1: Genomics & Transcriptomics</h2>
              
              <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md lg:col-span-1">
                  <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">Target Identity</h3>
                  
                  <div className="mb-6">
                    <div className="text-slate-500 text-xs mb-1">MUTATED GENE</div>
                    <div className="text-3xl text-blue-400 font-bold">{selectedDisease.mutated_gene}</div>
                  </div>
                  
                  <div className="mb-6">
                    <div className="text-slate-500 text-xs mb-1">PRIMARY TISSUE / CELL TYPE</div>
                    <div className="text-lg text-white font-medium">{selectedDisease.cell_type}</div>
                  </div>

                  <hr className="border-slate-800 my-6" />

                  <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-4">Gene Expression Profile</h3>
                  <div className="space-y-4">
                    <div>
                      <div className="flex items-center gap-2 text-xs text-red-400 font-bold mb-2 uppercase">↑ Up-Regulated</div>
                      <div className="flex flex-wrap gap-2">
                        {selectedDisease.up_regulated?.map((g, i) => (
                          <span key={i} className="bg-red-500/10 border border-red-500/20 text-red-300 px-2 py-1 rounded text-xs">{g}</span>
                        )) || <span className="text-slate-600 text-sm">No data</span>}
                      </div>
                    </div>
                    <div>
                      <div className="flex items-center gap-2 text-xs text-blue-400 font-bold mb-2 uppercase">↓ Down-Regulated</div>
                      <div className="flex flex-wrap gap-2">
                        {selectedDisease.down_regulated?.map((g, i) => (
                          <span key={i} className="bg-blue-500/10 border border-blue-500/20 text-blue-300 px-2 py-1 rounded text-xs">{g}</span>
                        )) || <span className="text-slate-600 text-sm">No data</span>}
                      </div>
                    </div>
                  </div>
                </div>

                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-0 backdrop-blur-md lg:col-span-2 overflow-hidden flex flex-col">
                  <div className="p-6 border-b border-slate-800 flex justify-between items-center bg-slate-950/50">
                    <h3 className="text-slate-300 text-sm font-bold uppercase tracking-widest">FASTA Protein Sequence</h3>
                    <div className="text-xs text-teal-500 bg-teal-500/10 px-2 py-1 rounded border border-teal-500/20">Length: {selectedDisease.sequence?.length || 0} AA</div>
                  </div>
                  <div className="p-6 overflow-y-auto max-h-[400px] font-mono text-xs text-slate-400 leading-loose break-all bg-[#0a0f1c]">
                    <span className="text-blue-500">{'>'}sp|{selectedDisease.mutated_gene}_HUMAN | Length: {selectedDisease.sequence?.length || 0}</span><br/>
                    {selectedDisease.sequence || "No sequence data available."}
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* STAGE 2: PROTEIN */}
          {activeTab === "3D Protein Fold" && (
            <div className="max-w-6xl mx-auto space-y-6 h-[70vh] flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-semibold text-white">Stage 2: 3D Protein Folding (ESMFold/AlphaFold)</h2>
                <div className="bg-slate-800 border border-slate-700 px-4 py-2 rounded-lg text-sm text-slate-300 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div> Live Py3Dmol Rendering
                </div>
              </div>
              
              <div className="flex-1 bg-slate-900/80 border border-slate-700 rounded-2xl overflow-hidden relative shadow-2xl">
                {/* 3Dmol.js HTML injection via iframe */}
                <iframe 
                  ref={iframeRef}
                  src="/protein_viewer.html" 
                  className="w-full h-full border-none"
                  title="3D Protein Viewer"
                />
              </div>
            </div>
          )}

          {/* STAGE 3: DRUG CANDIDATE */}
          {activeTab === "Drug Candidate" && (
            <div className="max-w-6xl mx-auto space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
               <h2 className="text-2xl font-semibold text-white">Stage 3: GNN Drug Generation</h2>
               <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                
                <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 backdrop-blur-md">
                  <h3 className="text-slate-400 text-xs font-bold uppercase tracking-widest mb-6">Top Candidate Profile</h3>
                  
                  <div className="space-y-6">
                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Compound ID</div>
                      <div className="font-mono text-sm text-blue-400 bg-slate-950 p-3 rounded-lg border border-slate-800">
                        {selectedDisease.drug_candidates[0]?.name || "Unknown"}
                      </div>
                    </div>
                    
                    <div>
                      <div className="text-xs text-slate-500 mb-1 uppercase tracking-wider">Binding Affinity</div>
                      <div className="flex items-center gap-2">
                        <div className="text-3xl font-light text-white">{selectedDisease.drug_candidates[0]?.affinity || "-9.0"}</div>
                        <div className="text-sm text-teal-400">kcal/mol</div>
                      </div>
                    </div>

                    <div>
                      <div className="text-xs text-slate-500 mb-2 uppercase tracking-wider flex justify-between">
                        <span>ADMET Score</span>
                        <span className="text-white">{(selectedDisease.drug_candidates[0]?.admet_score * 100).toFixed(0)}%</span>
                      </div>
                      <div className="w-full bg-slate-800 rounded-full h-2">
                        <div className="bg-gradient-to-r from-blue-500 to-teal-400 h-2 rounded-full" style={{ width: `${(selectedDisease.drug_candidates[0]?.admet_score || 0.8) * 100}%` }}></div>
                      </div>
                    </div>
                  </div>

                  <button 
                    onClick={() => setActiveTab("Bioproduction")}
                    className="w-full mt-10 bg-blue-600 hover:bg-blue-500 text-white py-3 rounded-xl font-medium transition-colors flex items-center justify-center gap-2"
                  >
                    Generate Biosynthesis Pathway <ChevronRight size={18} />
                  </button>
                </div>

                <div className="lg:col-span-2 bg-slate-900/40 border border-slate-800 rounded-2xl relative overflow-hidden flex flex-col backdrop-blur-sm min-h-[500px]">
                  <div className="absolute top-6 left-6 z-10 pointer-events-none">
                    <h3 className="text-lg font-semibold text-white">Interactive 3D Structure</h3>
                    <p className="text-sm text-slate-400 mt-1">Rendered with Three.js Engine</p>
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
                    <div className="bg-slate-950/80 backdrop-blur border border-slate-800 p-3 rounded-lg pointer-events-auto max-w-sm truncate shadow-xl">
                      <div className="text-[10px] text-slate-500 uppercase tracking-widest mb-1">SMILES string</div>
                      <div className="font-mono text-xs text-slate-300 truncate">
                        {selectedDisease.drug_candidates[0]?.smiles || "N/A"}
                      </div>
                    </div>
                  </div>
                </div>

               </div>
            </div>
          )}

          {/* STAGE 4: BIOPRODUCTION */}
          {activeTab === "Bioproduction" && (
            <div className="max-w-6xl mx-auto space-y-6 h-[75vh] flex flex-col animate-in fade-in slide-in-from-bottom-4 duration-500">
              <div className="flex justify-between items-start">
                <div>
                  <h2 className="text-2xl font-semibold text-white">Stage 4: Retrosynthesis & Bio-Production</h2>
                  <p className="text-slate-400 mt-2">Mapping the chemical drug candidate back to natural biosynthesis pathways.</p>
                </div>
                <div className="bg-slate-800 border border-slate-700 px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                  <span className="text-slate-400">Host Organism:</span> 
                  <span className="text-teal-400 font-semibold">{selectedDisease.biosynthesis?.organism || "N/A"}</span>
                </div>
              </div>
              
              <div className="flex-1 bg-slate-900/80 border border-slate-800 rounded-2xl p-6 backdrop-blur-md flex flex-col relative shadow-xl">
                
                <div className="flex justify-between items-center mb-4 z-10">
                  <h3 className="text-slate-300 text-sm font-bold uppercase tracking-widest">Biosynthesis Pathway Network</h3>
                  
                  <button 
                    onClick={() => { setAnimStep(0); setIsPlaying(true); }}
                    disabled={isPlaying}
                    className="bg-blue-600 hover:bg-blue-500 disabled:bg-slate-700 disabled:text-slate-500 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center gap-2"
                  >
                    {isPlaying ? <Activity size={16} className="animate-spin" /> : <Play size={16} />}
                    {isPlaying ? `Synthesizing Node ${animStep + 1}...` : 'Simulate Reaction'}
                  </button>
                </div>

                {animStep >= (selectedDisease.biosynthesis?.pathway_nodes?.length || 0) && (
                  <div className="absolute top-6 left-1/2 -translate-x-1/2 bg-green-500/20 text-green-400 border border-green-500/30 px-6 py-2 rounded-full font-medium flex items-center gap-2 z-20 animate-in slide-in-from-top-4">
                    <CheckCircle size={18} /> Drug Synthesis Complete!
                  </div>
                )}

                <div className="flex-1 w-full bg-slate-950/50 rounded-xl overflow-hidden border border-slate-800/50">
                  <ReactFlow 
                    nodes={pathwayNodes} 
                    edges={pathwayEdges} 
                    nodeTypes={nodeTypes}
                    fitView
                    attributionPosition="bottom-left"
                  >
                    <Background color="#1e293b" gap={16} size={1} />
                    <Controls className="bg-slate-800 border-slate-700 fill-white" />
                  </ReactFlow>
                </div>

                {/* Simulated RDKit Molecule View Side-Panel (Mocked in React) */}
                <div className="absolute right-6 bottom-6 bg-slate-900 border border-slate-700 p-4 rounded-xl shadow-2xl w-64 z-10">
                   <div className="text-xs text-slate-400 uppercase tracking-widest mb-2 font-bold border-b border-slate-800 pb-2">Active Formula</div>
                   <div className="h-40 flex items-center justify-center border border-slate-800/50 rounded-lg bg-slate-950 mb-2 overflow-hidden relative">
                      {/* Instead of native RDKit, we show a Three.js wireframe as a proxy for the changing formula */}
                      <Canvas camera={{ position: [0, 0, 5] }}>
                        <ambientLight />
                        <pointLight position={[10, 10, 10]} />
                        <Molecule step={animStep} />
                        <OrbitControls autoRotate autoRotateSpeed={2 + (animStep * 2)} enableZoom={false} />
                      </Canvas>
                   </div>
                   <div className="text-center font-mono text-xs text-blue-400">
                     {animStep >= 0 && animStep < (selectedDisease.biosynthesis?.pathway_nodes?.length || 0) 
                       ? selectedDisease.biosynthesis.pathway_nodes[animStep] 
                       : animStep >= (selectedDisease.biosynthesis?.pathway_nodes?.length || 0) 
                         ? "Final Product Synthesized" 
                         : "Awaiting Simulation..."}
                   </div>
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
