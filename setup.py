from pathlib import Path

from setuptools import setup

requires = ["sh==1.14.1"]
here = Path(__file__).parent
about = {}
with (here / "autograder" / "__version__.py").open(encoding="utf-8") as f:
    exec(f.read(), about)
with (here / "README.md").open(encoding="utf-8") as f:
    long_description = f.read()

setup(
    name=about["__title__"],
    packages=[
        "autograder",
        "autograder.testcase_utils",
    ],
    version=about["__version__"],
    include_package_data=True,
    install_requires=requires,
    entry_points={"console_scripts": ["autograder=autograder.__main__:main"]},
    # metadata to display on PyPI
    author=about["__author__"],
    author_email=about["__author_email__"],
    description=about["__description__"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    license=about["__license__"],
    project_urls={"Source Code": "https://github.com/Ovsyanka83/autograder"},
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Environment :: Console",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
