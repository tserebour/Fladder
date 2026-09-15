#!/usr/bin/env python3
"""Assemble final knowledge-graph.json from all intermediate files."""
import json
import os
import sys
from datetime import datetime

ua_dir = sys.argv[1]
project_root = sys.argv[2]

# Read assembled graph
with open(f'{ua_dir}/intermediate/assembled-graph.json') as f:
    assembled = json.load(f)

# Read layers
with open(f'{ua_dir}/intermediate/layers.json') as f:
    layers = json.load(f)

# Read tour
with open(f'{ua_dir}/intermediate/tour.json') as f:
    tour = json.load(f)

# Read scan result for project metadata
with open(f'{ua_dir}/intermediate/scan-result.json') as f:
    scan = json.load(f)

# Read git commit hash
import subprocess
result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=project_root)
commit_hash = result.stdout.strip()

# Assemble final knowledge graph
knowledge_graph = {
    "version": "1.0.0",
    "project": {
        "name": scan.get('name', 'fladder'),
        "languages": scan.get('languages', []),
        "frameworks": scan.get('frameworks', []),
        "description": scan.get('description', ''),
        "analyzedAt": datetime.utcnow().isoformat() + "Z",
        "gitCommitHash": commit_hash
    },
    "nodes": assembled.get('nodes', []),
    "edges": assembled.get('edges', []),
    "layers": layers,
    "tour": tour
}

# Validate layers
for layer in layers:
    if 'id' not in layer or 'name' not in layer or 'description' not in layer or 'nodeIds' not in layer:
        print(f'Warning: Layer missing required fields: {layer.get("id", "unknown")}')

# Validate tour
for step in tour:
    if 'order' not in step or 'title' not in step or 'description' not in step or 'nodeIds' not in step:
        print(f'Warning: Tour step missing required fields: {step.get("order", "unknown")}')

# Write final knowledge graph
output_path = f'{ua_dir}/knowledge-graph.json'
with open(output_path, 'w') as f:
    json.dump(knowledge_graph, f, indent=2)

print(f'Final knowledge graph written to {output_path}')
print(f'  Nodes: {len(knowledge_graph["nodes"])}')
print(f'  Edges: {len(knowledge_graph["edges"])}')
print(f'  Layers: {len(knowledge_graph["layers"])}')
print(f'  Tour steps: {len(knowledge_graph["tour"])}')
