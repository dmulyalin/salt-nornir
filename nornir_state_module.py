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


def cfg(*commands, **kwargs):
    """
    Enforce configuration state on device using Nornir
    execution module ``nr.cfg`` function.
    
    """
    log.debug("commands: {}, kwargs: {}".format(commands, kwargs))
    ret = {
        "name": name,
        "changes": {},
        "result": False,
        "comment": "",
    }
    return ret

    
def task():
    """
    Enforce configuration state on device using Nornir
    execution module ``nr.task`` function.
    
    """
    ret = {
        "name": name,
        "changes": {},
        "result": False,
        "comment": "",
    }
    return ret