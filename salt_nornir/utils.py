"""File to contain various utility functions"""


def _is_url(path):
    """
    Helper function to check if given path string is one of URL schemes
    supported by SaltStack ``cp.get_url`` execution module function.

    :param path: string, path to check
    :return: True or False
    """
    schemes = [
        "salt://",
        "http://",
        "https://",
        "ftp://",
        "s3://",
        "swift://",
        "file://",
    ]

    path = str(path)

    return any(path.startswith(s) for s in schemes)
