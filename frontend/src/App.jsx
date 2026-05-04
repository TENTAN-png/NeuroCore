import { useState, useEffect } from 'react'
import axios from 'axios'
import ProteinViewer from './components/ProteinViewer'
import BioproductionNetwork from './components/BioproductionNetwork'
import './App.css'

function App() {
  const [query, setQuery] = useState('Glioblastoma')
  const [diseaseData, setDiseaseData] = useState(null)
  const [loading, setLoading] = useState(false)

  const searchDisease = async () => {
    setLoading(true)
    try {
      const response = await axios.get(`http://localhost:8000/search?query=${query}`)
      setDiseaseData(response.data)
    } catch (error) {
      console.error("Error fetching data:", error)
    }
    setLoading(false)
  }

  useEffect(() => {
    searchDisease()
  }, [])

  return (
    <div className="min-h-screen bg-[#0f172a] text-white p-8 font-sans">
      <header className="mb-12 border-b border-slate-700 pb-6 flex justify-between items-end">
        <div>
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            BioGenesis UI
          </h1>
          <p className="text-slate-400 mt-2">React + Three.js + FastAPI Architecture</p>
        </div>
        <div className="flex gap-4">
          <input 
            type="text" 
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            className="px-4 py-2 bg-slate-800 border border-slate-600 rounded-lg focus:outline-none focus:border-blue-400 w-64"
            placeholder="Enter disease..."
          />
          <button 
            onClick={searchDisease}
            className="px-6 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg transition-colors font-semibold shadow-lg shadow-blue-500/20"
          >
            {loading ? "Searching..." : "Search Pipeline"}
          </button>
        </div>
      </header>

      {diseaseData && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* Left Column */}
          <div className="space-y-8">
            {/* Stage 1 */}
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 backdrop-blur-sm">
              <h2 className="text-2xl font-bold mb-4 text-emerald-400 flex items-center gap-2">
                <span className="bg-emerald-400/10 p-2 rounded-lg">🧬</span> Stage 1: Genomics
              </h2>
              <div className="space-y-2 mb-6">
                <p className="text-lg"><span className="text-slate-400 font-medium">Match:</span> {diseaseData.name}</p>
                <p className="text-lg"><span className="text-slate-400 font-medium">Target Gene:</span> <span className="font-mono text-blue-300 bg-blue-900/30 px-2 py-1 rounded">{diseaseData.mutated_gene}</span></p>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-slate-900/50 p-4 rounded-xl border border-red-900/30">
                  <p className="text-red-400 font-semibold mb-3 flex items-center gap-2">↑ Upregulated</p>
                  <div className="flex flex-wrap gap-2">
                    {diseaseData.up_regulated.map(g => <span key={g} className="px-2 py-1 bg-red-500/10 text-red-300 rounded text-sm">{g}</span>)}
                  </div>
                </div>
                <div className="bg-slate-900/50 p-4 rounded-xl border border-blue-900/30">
                  <p className="text-blue-400 font-semibold mb-3 flex items-center gap-2">↓ Downregulated</p>
                  <div className="flex flex-wrap gap-2">
                    {diseaseData.down_regulated.map(g => <span key={g} className="px-2 py-1 bg-blue-500/10 text-blue-300 rounded text-sm">{g}</span>)}
                  </div>
                </div>
              </div>
            </div>

            {/* Stage 4 */}
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 backdrop-blur-sm">
               <h2 className="text-2xl font-bold mb-4 text-amber-400 flex items-center gap-2">
                  <span className="bg-amber-400/10 p-2 rounded-lg">⚙️</span> Stage 4: Bioproduction
               </h2>
               <p className="mb-4 text-slate-300">
                  Host Organism: <span className="font-semibold text-white">{diseaseData.biosynthesis?.organism}</span>
               </p>
               <div className="h-64 rounded-xl overflow-hidden">
                  <BioproductionNetwork biosynthesis={diseaseData.biosynthesis} />
               </div>
            </div>
          </div>

          {/* Right Column */}
          <div className="space-y-8">
            {/* Stage 2 */}
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 backdrop-blur-sm h-[500px] flex flex-col">
               <h2 className="text-2xl font-bold mb-4 text-purple-400 flex items-center gap-2">
                  <span className="bg-purple-400/10 p-2 rounded-lg">⚛️</span> Stage 2: 3D Protein Viewer
               </h2>
               <div className="flex-grow rounded-xl overflow-hidden relative">
                  <div className="absolute top-4 left-4 z-10 bg-slate-900/80 px-3 py-1 rounded-full text-xs font-mono border border-slate-700 backdrop-blur-md">
                     Three.js Render: {diseaseData.mutated_gene}
                  </div>
                  <ProteinViewer />
               </div>
            </div>

            {/* Stage 3 Placeholder for later */}
            <div className="bg-slate-800/50 p-6 rounded-2xl border border-slate-700 backdrop-blur-sm">
               <h2 className="text-2xl font-bold mb-4 text-pink-400 flex items-center gap-2">
                  <span className="bg-pink-400/10 p-2 rounded-lg">💊</span> Stage 3: GNN Screening
               </h2>
               <div className="p-4 bg-slate-900/50 rounded-xl font-mono text-sm break-all text-slate-400 border border-slate-700/50">
                 {diseaseData.drug_candidates?.[0]?.smiles || "No SMILES available"}
               </div>
            </div>
          </div>
          
        </div>
      )}
    </div>
  )
}

export default App
