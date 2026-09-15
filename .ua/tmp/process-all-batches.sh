#!/bin/bash
UA_DIR="$1"
SKILL_DIR="$2"
PROJECT_ROOT="$3"

# Read batches.json and process each batch
python3 -c "
import json
import subprocess
import os

ua_dir = '$UA_DIR'
skill_dir = '$SKILL_DIR'
project_root = '$PROJECT_ROOT'

with open(f'{ua_dir}/intermediate/batches.json') as f:
    data = json.load(f)

batches = data['batches']
total = len(batches)

for i, batch in enumerate(batches):
    batch_index = batch['batchIndex']
    files = batch['files']
    import_data = batch.get('batchImportData', {})
    
    # Create input file
    input_data = {
        'projectRoot': project_root,
        'batchFiles': files,
        'batchImportData': import_data
    }
    
    input_path = f'{ua_dir}/tmp/ua-file-analyzer-input-{batch_index}.json'
    with open(input_path, 'w') as f:
        json.dump(input_data, f)
    
    # Run extraction script
    output_path = f'{ua_dir}/tmp/ua-file-extract-results-{batch_index}.json'
    result = subprocess.run(
        ['node', f'{skill_dir}/extract-structure.mjs', input_path, output_path],
        capture_output=True,
        text=True,
        cwd=project_root
    )
    
    if result.returncode != 0:
        print(f'Warning: Batch {batch_index} extraction failed: {result.stderr[:200]}')
    else:
        # Check if output exists
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            print(f'Batch {batch_index}/{total} extracted successfully')
        else:
            print(f'Warning: Batch {batch_index} produced empty output')

print('All batches processed')
