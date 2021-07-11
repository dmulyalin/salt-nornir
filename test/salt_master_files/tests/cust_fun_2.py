def run(result):
    """Function to test use_all_tasks=True"""
    ret = []
    for item in result:
        if item.result == None:
            continue
        if "Clock source: NTP" not in item.result:
            ret.append(
                {"exception": "NTP not synced", "result": "FAIL", "success": False}
            )
    return ret
