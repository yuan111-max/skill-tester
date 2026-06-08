"""Validate JSON files for structural correctness."""

import json

def validate_json(filepath: str) -> dict:
    with open(filepath) as f:
        try:
            data = json.load(f)
            return {"valid": True, "keys": len(data)}
        except json.JSONDecodeError as e:
            return {"valid": False, "error": str(e)}
