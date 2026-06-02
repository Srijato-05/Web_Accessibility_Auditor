import { useEffect, useState } from 'react';
import { client } from '../api/client.ts';
import { Network } from 'lucide-react';

interface GraphNode {
  id: string;
  label: string;
  type: string;
}

interface GraphLink {
  source: string;
  target: string;
}

interface PositionedNode extends GraphNode {
  x: number;
  y: number;
}

const NODE_COLORS: Record<string, string> = {
  page: '#00f2ff',           // Cyan
  component: '#7000ff',      // Violet
  violation: '#ff007a',      // Magenta
  violation_major: '#ff007a', 
  violation_critical: '#ff007a', 
};

export const GraphView = () => {
  const [nodes, setNodes] = useState<PositionedNode[]>([]);
  const [links, setLinks] = useState<{ sourceNode: PositionedNode; targetNode: PositionedNode }[]>([]);
  const [loading, setLoading] = useState(true);
  const [hoveredNode, setHoveredNode] = useState<PositionedNode | null>(null);

  useEffect(() => {
    client.get('/graph-visualization')
      .then(res => {
        const rawNodes: GraphNode[] = res.data.nodes || [];
        const rawLinks: GraphLink[] = res.data.links || [];

        // Position nodes on concentric radar rings
        const width = 600;
        const height = 400;
        const centerX = width / 2;
        const centerY = height / 2;

        const pageNodes = rawNodes.filter(n => n.type === 'page');
        const childNodes = rawNodes.filter(n => n.type !== 'page');

        const nodeMap: Record<string, PositionedNode> = {};

        // 1. Center node (Root or first page)
        if (pageNodes.length > 0) {
          const root = pageNodes[0];
          nodeMap[root.id] = { ...root, x: centerX, y: centerY };
        }

        // 2. Ring 1: Other pages (radius = 90)
        const otherPages = pageNodes.slice(1);
        otherPages.forEach((node, index) => {
          const angle = (index * 2 * Math.PI) / (otherPages.length || 1);
          const r = 90;
          nodeMap[node.id] = {
            ...node,
            x: centerX + r * Math.cos(angle),
            y: centerY + r * Math.sin(angle)
          };
        });

        // 3. Ring 2: Components and Violations (radius = 160)
        // Group child nodes by their first linked page
        const childrenByPage: Record<string, GraphNode[]> = {};
        childNodes.forEach(child => {
          const link = rawLinks.find(l => l.target === child.id || l.source === child.id);
          const parentId = link ? (link.source === child.id ? link.target : link.source) : (pageNodes[0]?.id || '');
          if (!childrenByPage[parentId]) {
            childrenByPage[parentId] = [];
          }
          childrenByPage[parentId].push(child);
        });

        // Place children close to their parent's angular vector
        Object.entries(childrenByPage).forEach(([parentId, list]) => {
          const parent = nodeMap[parentId];
          if (!parent) return;

          const baseAngle = Math.atan2(parent.y - centerY, parent.x - centerX);
          const spread = Math.PI / 3; // 60 degrees spread

          list.forEach((child, index) => {
            const offsetAngle = list.length === 1 ? 0 : (index * spread) / (list.length - 1) - spread / 2;
            const finalAngle = baseAngle + offsetAngle;
            const r = 165;
            nodeMap[child.id] = {
              ...child,
              x: centerX + r * Math.cos(finalAngle),
              y: centerY + r * Math.sin(finalAngle)
            };
          });
        });

        // Fill remaining nodes that might be disconnected
        rawNodes.forEach(node => {
          if (!nodeMap[node.id]) {
            const angle = Math.random() * 2 * Math.PI;
            const r = 120;
            nodeMap[node.id] = {
              ...node,
              x: centerX + r * Math.cos(angle),
              y: centerY + r * Math.sin(angle)
            };
          }
        });

        const positionedNodes = Object.values(nodeMap);
        setNodes(positionedNodes);

        // Map links
        const mappedLinks = rawLinks.map(l => {
          const sourceNode = nodeMap[l.source];
          const targetNode = nodeMap[l.target];
          if (sourceNode && targetNode) {
            return { sourceNode, targetNode };
          }
          return null;
        }).filter(Boolean) as { sourceNode: PositionedNode; targetNode: PositionedNode }[];

        setLinks(mappedLinks);
        setLoading(false);
      })
      .catch(err => {
        console.error("Could not fetch graph data", err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-on-surface-variant gap-2" aria-live="polite">
        <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
        <span className="text-xs font-mono uppercase tracking-widest text-primary">Synchronizing Nodes...</span>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-on-surface-variant gap-3 px-4 text-center">
        <Network size={32} className="opacity-20 text-primary" />
        <div>
          <p className="text-sm font-bold uppercase tracking-widest text-on-surface-variant">Awaiting Telemetry</p>
          <p className="text-xs text-on-surface-variant mt-1 opacity-60">Run a spider audit to inspect link remediation connections.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full h-full relative select-none">
      <svg className="w-full h-full" viewBox="0 0 600 400" preserveAspectRatio="xMidYMid meet">
        {/* Decorative Grid Lines */}
        <line x1="300" y1="0" x2="300" y2="400" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />
        <line x1="0" y1="200" x2="600" y2="200" stroke="rgba(255, 255, 255, 0.03)" strokeWidth="1" />

        {/* Concentric Target Circles */}
        <circle cx="300" cy="200" r="90" fill="none" stroke="rgba(0, 242, 255, 0.08)" strokeWidth="1.5" strokeDasharray="4 4" />
        <circle cx="300" cy="200" r="165" fill="none" stroke="rgba(112, 0, 255, 0.05)" strokeWidth="1.5" />

        {/* Connections */}
        {links.map((link, idx) => (
          <line
            key={`link-${idx}`}
            x1={link.sourceNode.x}
            y1={link.sourceNode.y}
            x2={link.targetNode.x}
            y2={link.targetNode.y}
            stroke={link.targetNode.type.includes('violation') ? 'rgba(255, 0, 122, 0.25)' : 'rgba(255, 255, 255, 0.08)'}
            strokeWidth={link.targetNode.type.includes('violation') ? '1.5' : '1'}
          />
        ))}

        {/* Nodes */}
        {nodes.map((node) => {
          const color = NODE_COLORS[node.type] || '#94A3B8';
          const isViolation = node.type.includes('violation');
          return (
            <g
              key={node.id}
              className="cursor-pointer"
              onMouseEnter={() => setHoveredNode(node)}
              onMouseLeave={() => setHoveredNode(null)}
            >
              {/* Glow filter backing */}
              {isViolation && (
                <circle
                  cx={node.x}
                  cy={node.y}
                  r="10"
                  fill="none"
                  stroke={color}
                  strokeWidth="1.5"
                  className="animate-ping opacity-30"
                />
              )}
              
              <circle
                cx={node.x}
                cy={node.y}
                r={node.type === 'page' ? '7' : '5'}
                fill={color}
                stroke="#050507"
                strokeWidth="1.5"
                className="transition-transform duration-200 hover:scale-125"
              />
            </g>
          );
        })}
      </svg>

      {/* Interactive HUD Overlay */}
      {hoveredNode && (
        <div className="absolute top-2 left-2 glass-panel p-3 border border-primary/30 max-w-[240px] pointer-events-none">
          <span className="text-[9px] uppercase tracking-wider text-on-surface-variant block font-bold">Node Telemetry</span>
          <span className="text-xs font-bold text-on-surface truncate block mt-1">{hoveredNode.label}</span>
          <div className="flex items-center gap-2 mt-2">
            <span className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: NODE_COLORS[hoveredNode.type] || '#94A3B8' }}></span>
            <span className="text-[9px] font-mono uppercase tracking-widest text-on-surface-variant font-bold">
              {hoveredNode.type.replace('_', ' ')}
            </span>
          </div>
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-2 left-2 flex flex-wrap gap-2">
        {Object.entries(NODE_COLORS).slice(0, 3).map(([type, color]) => (
          <div key={type} className="flex items-center gap-1.5 text-[9px] text-on-surface-variant font-bold uppercase tracking-wider bg-surface/80 px-2 py-1 rounded border border-surface-border">
            <span className="w-1.5 h-1.5 rounded-full inline-block" style={{ backgroundColor: color }}></span>
            {type}
          </div>
        ))}
      </div>

      <div className="absolute top-2 right-2 bg-surface/80 px-2 py-1 text-[10px] rounded border border-surface-border text-on-surface-variant font-bold uppercase tracking-widest font-mono">
        {nodes.length} Nodes · {links.length} Links
      </div>
    </div>
  );
};
