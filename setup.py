from setuptools import setup, find_packages
from pathlib import Path


requires = ['sh']

path_to_testhelpers = Path(__file__).parent / "autograder/test_helpers"
paths_to_testhelpers = [str(p) for p in path_to_testhelpers.iterdir()]

setup(
    name="assignment-autograder",
    packages=["autograder"],
    version="2.2.1",
    install_requires=requires,
    data_files=[
        ('autograder', ['autograder/default_config.ini']),
        ('test_helpers', paths_to_testhelpers),
    ],
    entry_points={
        'console_scripts': ['autograder=autograder.__main__:main']
    },

    # metadata to display on PyPI
    author="Stanislav Zmiev",
    author_email="szmiev2000@gmail.com",
    description="Automates programming assignment grading",
    license="MIT",
    project_urls={"Source Code": "https://github.com/Ovsyanka83/autograder"},
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
    ]
)