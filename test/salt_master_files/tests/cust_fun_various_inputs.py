from nornir.core.task import Result, MultiResult

def run(result):
    """
    Custom test function to test devices output.
          
    Sample usage:
    
        salt nrp1 nr.test suite="salt://tests/sample_suite.txt" table=brief
    """
    ret = []
    # handle single result item
    if isinstance(result, Result):
        if "Clock source: NTP" not in result.result:
            ret.append(
                {
                    "exception": "NTP not synced", 
                    "result": "FAIL", 
                    "success": False
                }
            )
    # handle list of Result objects or MultiResult object
    elif isinstance(result, (MultiResult, list)):
        for item in result:
            if item.name == "show clock":
                if "Clock source: NTP" not in item.result:
                    ret.append(
                        {
                            "exception": "NTP not synced cust fun 3",
                            "result": "FAIL",
                            "success": False,
                        }
                    )
            elif item.name == "show ip int brief":
                if "10.10.10.10" not in item.result:
                    ret.append(
                        {
                            "exception": "10. IP not configured",
                            "result": "FAIL",
                            "success": False,
                        }
                    )
    else:
        raise TypeError("Unsuppted result type '{}'".format(type(result)))
    return ret
