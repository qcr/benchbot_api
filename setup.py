from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='benchbot_api',
      version='1.1.0',
      author='Ben Talbot',
      author_email='b.talbot@qut.edu.au',
      description=
      'The BenchBot API for use with the ACRV Scene Understanding Challenge',
      long_description=long_description,
      long_description_content_type='text/markdown',
      packages=find_packages(),
      install_requires=[
          'jsonpickle', 'matplotlib', 'numpy', 'opencv-python', 'requests',
          'scipy>=1.2.0'
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
      ))
