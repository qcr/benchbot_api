from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='benchbot',
    version='0.1.3',
    author='Gavin Suddrey',
    author_email='g.suddrey@qut.edu.au',
    description='Benchbot provides a simple python-based wrapper for use with the QUT-based BenchBot service',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    )
)