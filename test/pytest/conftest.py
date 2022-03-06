def pytest_configure(config):
    # add markers for pytest to not complain
    config.addinivalue_line(
        "markers", "modify_pillar_target"
    )
    config.addinivalue_line(
        "markers", "modify_pillar_pre_add"
    )
    config.addinivalue_line(
        "markers", "modify_pillar_pre_remove"
    )
    config.addinivalue_line(
        "markers", "modify_pillar_post_add"
    )
    config.addinivalue_line(
        "markers", "modify_pillar_post_remove"
    )