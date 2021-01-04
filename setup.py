import setuptools


with open("README.md", "r") as readme:
    readme_text = readme.read()

setuptools.setup(
    name="vmf_tool",
    packages=["vmf_tool"],
    version="0.2.0",
    license="gpl-3.0",
    description="A library for interpreting & editing .vmf files",
    author="Jared Ketterer",
    author_email="haveanotherbiscuit@gmail.com",
    long_description=readme_text,
    long_description_content_type="text/markdown",
    url="https://github.com/snake-biscuits/vmf_tool",
    download_url="https://github.com/snake-biscuits/vmf_tool/archive/v0.1.0.tar.gz",
    keywords=["source", "vmf", "valve"],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Topic :: Games/Entertainment :: First Person Shooters",
        "Topic :: Multimedia :: Graphics :: 3D Modeling",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8"
    ],
    python_requires=">=3.6",
)
