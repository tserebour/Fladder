#!/usr/bin/env python3
"""Write meta.json for the knowledge graph."""
import json
import os
import sys
import subprocess

ua_dir = sys.argv[1]
project_root = sys.argv[2]

# Get git commit hash
result = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, cwd=project_root)
commit_hash = result.stdout.strip()

# Read scan result for file count
with open(f'{ua_dir}/intermediate/scan-result.json') as f:
    scan = json.load(f)

# Read knowledge graph for stats
with open(f'{ua_dir}/knowledge-graph.json') as f:
    kg = json.load(f)

meta = {
    "gitCommitHash": commit_hash,
    "totalFiles": scan.get('totalFiles', 0),
    "totalNodes": len(kg.get('nodes', [])),
    "totalEdges": len(kg.get('edges', [])),
    "totalLayers": len(kg.get('layers', [])),
    "tourSteps": len(kg.get('tour', [])),
    "estimatedComplexity": scan.get('estimatedComplexity', 'unknown'),
    "languages": scan.get('languages', []),
    "frameworks": scan.get('frameworks', [])
}

# Write meta.json
meta_path = f'{ua_dir}/meta.json'
with open(meta_path, 'w') as f:
    json.dump(meta, f, indent=2)

print(f'Meta written to {meta_path}')
print(f'  Commit: {commit_hash[:12]}...')
print(f'  Files: {meta["totalFiles"]}')
print(f'  Nodes: {meta["totalNodes"]}')
print(f'  Edges: {meta["totalEdges"]}')
print(f'  Layers: {meta["totalLayers"]}')
print(f'  Tour steps: {meta["tourSteps"]}')
