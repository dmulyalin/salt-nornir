# -*- coding: utf-8 -*-
"""
Nornir State module
===================

"""
# Import python libs
import logging


# -----------------------------------------------------------------------------
# globals
# -----------------------------------------------------------------------------


log = logging.getLogger(__name__)
__virtualname__ = "nr"


# ----------------------------------------------------------------------------------------------------------------------
# property functions
# ----------------------------------------------------------------------------------------------------------------------


def __virtual__():
    return __virtualname__


# -----------------------------------------------------------------------------
# callable functions
# -----------------------------------------------------------------------------


def cfg(*args, **kwargs):
    """
    Enforce configuration state on device using Nornir
    execution module ``nr.cfg`` function.
    
    """
    state_name = kwargs.pop("name") 
    result = __salt__["nr.cfg"](**kwargs)
    ret = {
        "name": state_name,
        "changes": result,
        "result": True,
        "comment": "",
    }
    return ret

    
def task():
    """
    Enforce configuration state on device using Nornir
    execution module ``nr.task`` function.
    
    """
    state_name = kwargs.pop("name") 
    result = __salt__["nr.task"](**kwargs)
    ret = {
        "name": state_name,
        "changes": result,
        "result": True,
        "comment": "",
    }
    return ret