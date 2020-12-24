from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

__author__ = "Denis Mulyalin <d.mulyalin@gmail.com>"

setup(
    name="salt_nornir",
    version="0.2.1",
    author="Denis Mulyalin",
    author_email="d.mulyalin@gmail.com",
    description="SALTSTACK Nornir Modules",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dmulyalin/salt-nornir",
    packages=find_packages(),
    include_package_data=True,
    data_files=[('', ['LICENSE'])],
    classifiers=[
        "Topic :: Utilities",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.6",
    entry_points = """
	[salt.loader]
    module_dirs=salt_nornir.loader:module_dirs	
	proxy_dirs=salt_nornir.loader:proxy_dirs	
	state_dirs=salt_nornir.loader:state_dirs	
	runner_dirs=salt_nornir.loader:runner_dirs	
	"""
)