from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name='benchbot',
    version='0.1.4',
    author='Gavin Suddrey',
    author_email='g.suddrey@qut.edu.au',
    description='Benchbot provides a simple python-based wrapper for use with the QUT-based BenchBot service',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    install_requires=[
      'numpy',
      'opencv-python',
      'requests'
    ],
    classifiers=(
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: 3.6",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    )
)