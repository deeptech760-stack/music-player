from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="music-player",
    version="0.1.0",
    author="deeptech760-stack",
    author_email="",
    description="A modern desktop music player with PySide6 and VLC",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/deeptech760-stack/music-player",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "music-player = src.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "src.frontend.resources": ["*.qss", "*.png", "*.ico"],
    },
)