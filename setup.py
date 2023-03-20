from setuptools import setup, find_packages

from time

# -> Fetch documentation from readme
with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="RedisROS",
    version="0.0.3",
    license="GNU GPLv3",
    description="A redis-based event-based ROS2-like library for python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/vguillet/RedisROS",
    packages=find_packages(),
    install_requires=["redis", "python-redis-lock"],
    keywords=["ROS", "ROS2", "event-based", "python", "redis", "robotics"],
    python_requires=">= 3.8",
    author="Victor Guillet",
    author_email="victor.guillet@protonmail.com",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
    ]
    )