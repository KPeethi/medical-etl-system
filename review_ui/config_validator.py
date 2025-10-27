"""
Config validation with JSON Schema
Ensures roster.path is provided and valid
"""

import os
from jsonschema import validate, ValidationError

CONFIG_SCHEMA = {
    "type": "object",
    "properties": {
        "identity": {
            "type": "object",
            "properties": {
                "roster": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "minLength": 1}
                    },
                    "required": ["path"]
                }
            },
            "required": ["roster"]
        }
    }
}

def validate_config(config):
    """
    Validate configuration against schema
    Returns (is_valid, error_message)
    """
    if not config:
        return False, "Configuration is required"
    
    try:
        validate(instance=config, schema=CONFIG_SCHEMA)
    except ValidationError as e:
        if "'path' is a required property" in str(e):
            return False, "ERROR: identity.roster.path is required and must point to a readable file. Tip: include it in the request body or supply a Practice Pack."
        elif "'roster' is a required property" in str(e):
            return False, "ERROR: identity.roster configuration is required. Tip: include roster.path in your request."
        elif "'identity' is a required property" in str(e):
            return False, "ERROR: identity configuration is required. Tip: include identity.roster.path in your request."
        else:
            return False, f"Configuration validation error: {e.message}"
    
    roster_path = config.get('identity', {}).get('roster', {}).get('path')
    
    if roster_path is None or roster_path == 'null' or roster_path.strip() == '':
        return False, "ERROR: identity.roster.path is required and must point to a readable file. Tip: include it in the request body or supply a Practice Pack."
    
    if not os.path.exists(roster_path):
        return False, f"ERROR: Roster file not found at '{roster_path}'. Please verify the path is correct."
    
    if not os.path.isfile(roster_path):
        return False, f"ERROR: Roster path '{roster_path}' is not a file."
    
    ext = os.path.splitext(roster_path)[1].lower()
    if ext not in ['.xlsx', '.xls', '.csv', '.json']:
        return False, f"ERROR: Roster file must be .xlsx, .xls, .csv, or .json. Got: {ext}"
    
    return True, None


def calculate_unmapped_rate(stats):
    """Calculate percentage of unmapped files"""
    total = stats.get('processed', 0)
    unmapped = stats.get('unmapped', 0)
    
    if total == 0:
        return 0.0
    
    return unmapped / total


def check_high_unmapped_rate(stats, threshold=0.6):
    """
    Check if unmapped rate is too high
    Returns (is_high, warning_message)
    """
    rate = calculate_unmapped_rate(stats)
    
    if rate > threshold:
        unmapped = stats.get('unmapped', 0)
        total = stats.get('processed', 0)
        percentage = int(rate * 100)
        
        return True, (
            f"High unmapped rate ({percentage}% - {unmapped}/{total} files). "
            f"Likely bad roster mapping. Run GET /api/unmapped to preview examples."
        )
    
    return False, None
