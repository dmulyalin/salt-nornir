import json

def run(result):
    """
    Custom test function to test napalm get facts output
    """
    ret = []
    if "ceos" in result.result["get_facts"]["model"].lower():
        ret.append(
            {
                "result": "PASS", 
                "success": True,
            }
        )
    return ret
