from setuptools import setup, find_packages

setup(
    name="music-player",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.4.0",
    ],
    entry_points={
        "console_scripts": [
            "music-player = src.main:main",
        ]
    },
)