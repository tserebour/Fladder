#!/usr/bin/env python3
"""Generate semantic content for batch analysis results."""
import json
import os
import sys

ua_dir = sys.argv[1]
project_root = sys.argv[2]

with open(f'{ua_dir}/intermediate/batches.json') as f:
    batches_data = json.load(f)

batches = batches_data['batches']

def generate_summary(file_data, extraction):
    """Generate a summary for a file based on its structure."""
    path = file_data['path']
    lang = file_data['language']
    cat = file_data['fileCategory']
    funcs = extraction.get('functions', [])
    classes = extraction.get('classes', [])
    exports = extraction.get('exports', [])

    if cat == 'config':
        return f"Configuration file for {os.path.basename(path).split('.')[0]}"
    elif cat == 'docs':
        return f"Documentation: {os.path.basename(path)}"
    elif cat == 'infra':
        return f"Infrastructure configuration: {os.path.basename(path)}"
    elif cat == 'data':
        return f"Data file: {os.path.basename(path)}"
    elif cat == 'script':
        return f"Script file: {os.path.basename(path)}"
    elif cat == 'markup':
        return f"Markup file: {os.path.basename(path)}"

    parts = []
    if classes:
        class_names = [c['name'] for c in classes[:3]]
        parts.append(f"Defines {', '.join(class_names)}")
    if funcs:
        func_names = [f['name'] for f in funcs[:5]]
        parts.append(f"with functions: {', '.join(func_names)}")

    if parts:
        return f"{', '.join(parts)}."
    return f"Code file: {os.path.basename(path)}"

def generate_tags(file_data, extraction):
    """Generate tags for a file."""
    lang = file_data['language']
    cat = file_data['fileCategory']
    path = file_data['path']
    funcs = extraction.get('functions', [])
    classes = extraction.get('classes', [])

    tags = [lang, cat]

    if 'android' in path:
        tags.append('android')
    if 'ios' in path:
        tags.append('ios')
    if 'macos' in path:
        tags.append('macos')
    if 'linux' in path:
        tags.append('linux')
    if 'windows' in path:
        tags.append('windows')
    if 'web' in path:
        tags.append('web')

    if classes:
        tags.append('class')
    if funcs:
        tags.append('function')

    if 'main.dart' in path:
        tags.append('entry-point')
    if 'test' in path:
        tags.append('test')
    if 'model' in path.lower():
        tags.append('model')
    if 'service' in path.lower():
        tags.append('service')
    if 'provider' in path.lower() or 'riverpod' in path.lower():
        tags.append('state-management')
    if 'screen' in path.lower() or 'page' in path.lower():
        tags.append('ui')
    if 'widget' in path.lower():
        tags.append('widget')

    return list(set(tags))

def calculate_complexity(extraction):
    """Calculate complexity based on code metrics."""
    funcs = extraction.get('functions', [])
    classes = extraction.get('classes', [])
    call_graph = extraction.get('callGraph', [])
    metrics = extraction.get('metrics', {})

    func_count = metrics.get('functionCount', len(funcs))
    class_count = metrics.get('classCount', len(classes))

    if func_count > 20 or class_count > 5:
        return 'complex'
    elif func_count > 10 or class_count > 2:
        return 'moderate'
    else:
        return 'simple'

all_nodes = []
all_edges = []

for batch in batches:
    batch_index = batch['batchIndex']
    files = batch['files']
    import_data = batch.get('batchImportData', {})

    extract_path = f'{ua_dir}/tmp/ua-file-extract-results-{batch_index}.json'
    if not os.path.exists(extract_path):
        print(f'Warning: Missing extraction for batch {batch_index}')
        continue

    with open(extract_path) as f:
        extraction = json.load(f)

    batch_nodes = []
    batch_edges = []

    for file_info in files:
        path = file_info['path']
        file_id = f'file:{path}'

        # Find extraction result
        result = None
        for r in extraction.get('results', []):
            if r['path'] == path:
                result = r
                break

        if not result:
            result = {'functions': [], 'classes': [], 'exports': [], 'metrics': {}, 'callGraph': []}

        summary = generate_summary(file_info, result)
        tags = generate_tags(file_info, result)
        complexity = calculate_complexity(result)

        file_node = {
            'id': file_id,
            'type': 'file',
            'name': os.path.basename(path),
            'filePath': path,
            'summary': summary,
            'tags': tags,
            'complexity': complexity
        }
        batch_nodes.append(file_node)

        # Add function nodes
        for func in result.get('functions', []):
            func_id = f'function:{path}:{func["name"]}'
            func_node = {
                'id': func_id,
                'type': 'function',
                'name': func['name'],
                'filePath': path,
                'summary': f"Function {func['name']} in {os.path.basename(path)}",
                'tags': ['function', file_info['language']],
                'complexity': 'simple'
            }
            batch_nodes.append(func_node)
            batch_edges.append({
                'source': file_id,
                'target': func_id,
                'type': 'contains',
                'confidence': 1.0
            })

        # Add class nodes
        for cls in result.get('classes', []):
            class_id = f'class:{path}:{cls["name"]}'
            class_node = {
                'id': class_id,
                'type': 'class',
                'name': cls['name'],
                'filePath': path,
                'summary': f"Class {cls['name']} in {os.path.basename(path)}",
                'tags': ['class', file_info['language']],
                'complexity': 'moderate'
            }
            batch_nodes.append(class_node)
            batch_edges.append({
                'source': file_id,
                'target': class_id,
                'type': 'contains',
                'confidence': 1.0
            })

            # Add method nodes
            for method in cls.get('methods', []):
                method_id = f'function:{path}:{cls["name"]}.{method}'
                method_node = {
                    'id': method_id,
                    'type': 'function',
                    'name': method,
                    'filePath': path,
                    'summary': f"Method {method} of {cls['name']}",
                    'tags': ['method', file_info['language']],
                    'complexity': 'simple'
                }
                batch_nodes.append(method_node)
                batch_edges.append({
                    'source': class_id,
                    'target': method_id,
                    'type': 'contains',
                    'confidence': 1.0
                })

        # Add import edges
        imports = import_data.get(path, [])
        for imp in imports:
            if imp and not imp.startswith('dart:') and not imp.startswith('package:'):
                target_id = f'file:{imp}'
                batch_edges.append({
                    'source': file_id,
                    'target': target_id,
                    'type': 'imports',
                    'confidence': 0.9
                })

    all_nodes.extend(batch_nodes)
    all_edges.extend(batch_edges)

    # Write batch output
    batch_output = {
        'batchIndex': batch_index,
        'nodes': batch_nodes,
        'edges': batch_edges
    }
    output_path = f'{ua_dir}/intermediate/batch-{batch_index}.json'
    with open(output_path, 'w') as f:
        json.dump(batch_output, f)

print(f'Generated {len(all_nodes)} nodes and {len(all_edges)} edges across {len(batches)} batches')
