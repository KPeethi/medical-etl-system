# Runs ETL against included examples for a smoke test
$root = Split-Path -Parent $PSScriptRoot
$src = Join-Path $root 'test_data'
$dest = Join-Path $root 'temp_output'
$examples = Join-Path $root 'examples'
$map = Join-Path $examples 'demographics_object.json'

python "$root\main.py" "$src" "$dest" --mapping "$map"
