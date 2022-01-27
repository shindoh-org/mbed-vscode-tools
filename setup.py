# coding: utf-8
# setup.py

import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setuptools.setup(
    name="mbed-config-gen",
    version="0.0.1",
    install_requires=["mbed-tools"],
    entry_points={
        "console_scripts": [
            "mbed-config-gen=mbed_config_gen.mbed_config_gen:main"]
    },
    author="Keisuke Sugiura",
    author_email="std.experimental.optional@gmail.com",
    description="Command-line tool to generate C/C++ headers and update " \
                "Visual Studio Code C/C++ properties for Mbed projects",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sterngerlach/mbed-config-gen",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3 :: Only",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux"
    ],
    python_requires=">=3.7")
