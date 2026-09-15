#!/usr/bin/env python3
import json
import subprocess
import os
import sys

ua_dir = sys.argv[1]
skill_dir = sys.argv[2]
project_root = sys.argv[3]

with open(f'{ua_dir}/intermediate/batches.json') as f:
    data = json.load(f)

batches = data['batches']
total = len(batches)

for i, batch in enumerate(batches):
    batch_index = batch['batchIndex']
    files = batch['files']
    import_data = batch.get('batchImportData', {})
    
    input_data = {
        'projectRoot': project_root,
        'batchFiles': files,
        'batchImportData': import_data
    }
    
    input_path = f'{ua_dir}/tmp/ua-file-analyzer-input-{batch_index}.json'
    with open(input_path, 'w') as f:
        json.dump(input_data, f)
    
    output_path = f'{ua_dir}/tmp/ua-file-extract-results-{batch_index}.json'
    result = subprocess.run(
        ['node', f'{skill_dir}/extract-structure.mjs', input_path, output_path],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    if result.returncode != 0:
        print(f'Warning: Batch {batch_index} failed: {result.stderr[:100]}')
    elif os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        print(f'Batch {batch_index}/{total} OK')
    else:
        print(f'Warning: Batch {batch_index} empty output')

print('Done')
