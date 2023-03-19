from setuptools import setup, find_packages

setup(
    name="PyROS",
    version="1.0.0",
    license="GNU GPLv3",
    description="An event-based ROS2-like library for python",
    url="https://github.com/vguillet/pyROS",
    packages=find_packages(),
    install_requires=[],
    python_requires=">= 3.4",
    author="Victor Guillet",
    author_email="victor.guillet@protonmail.com",
    )