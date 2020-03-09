from setuptools import setup


requires = ['sh']

setup(
    name="autograder",
    packages=['autograder'],
    install_requires=requires,

    # metadata to display on PyPI
    author="Stanislav Zmiev",
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