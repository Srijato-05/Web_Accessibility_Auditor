import { useEffect, useState, useRef } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { client } from '../api/client';
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

const NODE_COLORS: Record<string, string> = {
    page: '#2563EB',           // blue - pages
    component: '#7C3AED',      // purple - DOM components
    violation: '#F59E0B',      // amber - minor violations
    violation_major: '#F97316', // orange - major violations
    violation_critical: '#EF4444', // red - critical violations
};

export const GraphView = () => {
    const [graphData, setGraphData] = useState<{ nodes: GraphNode[], links: GraphLink[] }>({ nodes: [], links: [] });
    const [loading, setLoading] = useState(true);
    const graphRef = useRef<any>(null);

    useEffect(() => {
        client.get('/graph-visualization')
            .then(res => {
                setGraphData(res.data);
                setLoading(false);
            })
            .catch(err => {
                console.error("Could not fetch graph data", err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-on-surface-variant gap-2">
                <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></div>
                <span className="text-xs font-medium">Connecting to TigerGraph...</span>
            </div>
        );
    }

    if (graphData.nodes.length === 0) {
        return (
            <div className="h-full flex flex-col items-center justify-center text-on-surface-variant gap-3 px-4 text-center">
                <Network size={32} className="opacity-20" />
                <div>
                    <p className="text-sm font-medium text-on-surface-variant">No graph data yet</p>
                    <p className="text-xs text-on-surface-variant mt-1 opacity-60">Run a scan first to populate the compliance graph</p>
                </div>
            </div>
        );
    }

    return (
        <div className="w-full h-full overflow-hidden relative">
            <ForceGraph2D
                ref={graphRef}
                graphData={graphData}
                nodeLabel="label"
                nodeColor={(node: any) => NODE_COLORS[node.type] || '#94A3B8'}
                nodeRelSize={5}
                linkColor={() => '#CBD5E1'}
                linkDirectionalParticles={2}
                linkDirectionalParticleSpeed={0.005}
                linkDirectionalParticleColor={() => '#2563EB'}
                cooldownTicks={100}
                onEngineStop={() => graphRef.current?.zoomToFit(400, 30)}
                backgroundColor="transparent"
            />
            {/* Legend */}
            <div className="absolute bottom-2 left-2 flex flex-wrap gap-2">
                {Object.entries(NODE_COLORS).map(([type, color]) => (
                    <div key={type} className="flex items-center gap-1 text-[9px] text-on-surface-variant font-bold uppercase tracking-wider bg-surface/80 px-2 py-1 rounded border border-surface-border">
                        <span className="w-2 h-2 rounded-full inline-block" style={{ backgroundColor: color }}></span>
                        {type.replace('_', ' ')}
                    </div>
                ))}
            </div>
            <div className="absolute top-2 right-2 bg-surface/80 px-2 py-1 text-[10px] rounded border border-surface-border text-on-surface-variant font-bold uppercase tracking-widest">
                {graphData.nodes.length} Nodes · {graphData.links.length} Links
            </div>
        </div>
    );
};
