from setuptools import setup, find_packages

__version__ = "0.10.1"
__author__ = "Denis Mulyalin <d.mulyalin@gmail.com>"

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r", encoding="utf8") as f:
    REQUIREMENTS = [i for i in f.read().splitlines() if i.strip()]

with open("requirements-dev.txt", "r", encoding="utf8") as f:
    REQUIREMENTS_DEV = [i for i in f.read().splitlines() if i.strip()]

with open("requirements-prodmax.txt", "r", encoding="utf8") as f:
    REQUIREMENTS_PRODMAX = [i for i in f.read().splitlines() if i.strip()]

with open("requirements-prodmin.txt", "r", encoding="utf8") as f:
    REQUIREMENTS_PRODMIN = [i for i in f.read().splitlines() if i.strip()]

setup(
    name="salt_nornir",
    version=__version__,
    author="Denis Mulyalin",
    author_email="d.mulyalin@gmail.com",
    description="SALTSTACK Nornir Modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dmulyalin/salt-nornir",
    packages=find_packages(),
    include_package_data=True,
    keywords=["salt-extension"],
    extras_require={
        "dev": REQUIREMENTS_DEV + REQUIREMENTS_PRODMAX,
        "prodmax": REQUIREMENTS_PRODMAX,
        "prodmin": REQUIREMENTS_PRODMIN,
    },
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
    install_requires=REQUIREMENTS,
    entry_points="""
    [salt.loader]
    module_dirs=salt_nornir.loader:module_dirs
    proxy_dirs=salt_nornir.loader:proxy_dirs
    states_dirs=salt_nornir.loader:states_dirs
    runner_dirs=salt_nornir.loader:runner_dirs
    """,
    data_files=[('', ['LICENSE', 'requirements.txt', 'requirements-dev.txt', 'requirements-prodmax.txt', 'requirements-prodmin.txt'])]
)
