import React, { useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MarkerType,
  useNodesState,
  useEdgesState
} from 'reactflow';
import 'reactflow/dist/style.css';

export default function BioproductionNetwork({ biosynthesis }) {
  if (!biosynthesis || !biosynthesis.pathway_nodes) return null;

  const nodesList = biosynthesis.pathway_nodes;
  
  // Dynamically generate React Flow nodes
  const initialNodes = nodesList.map((nodeName, index) => ({
    id: `node-${index}`,
    position: { x: index * 250, y: index % 2 === 0 ? 100 : 200 },
    data: { label: nodeName },
    style: {
      background: index === nodesList.length - 1 ? '#10b981' : '#1e293b',
      color: 'white',
      border: '1px solid #475569',
      borderRadius: '8px',
      padding: '15px',
      fontWeight: 'bold',
      boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)'
    }
  }));

  // Dynamically generate React Flow edges
  const initialEdges = [];
  for (let i = 0; i < nodesList.length - 1; i++) {
    initialEdges.push({
      id: `edge-${i}`,
      source: `node-${i}`,
      target: `node-${i + 1}`,
      animated: true,
      style: { stroke: '#3b82f6', strokeWidth: 3 },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#3b82f6',
      },
    });
  }

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  return (
    <div className="w-full h-full bg-slate-900 rounded-xl overflow-hidden border border-slate-700">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        fitView
        attributionPosition="bottom-right"
      >
        <Background color="#334155" gap={16} />
        <Controls className="bg-slate-800 border-slate-700 fill-white" />
      </ReactFlow>
    </div>
  );
}
