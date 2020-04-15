from setuptools import setup, find_packages


requires = ['sh']

setup(
    name="assignment-autograder",
    packages=find_packages(),
    install_requires=requires,
    package_data={'autograder.test_helpers': ['test_helper.c', 'TestHelper.java']},
    include_package_data=True,
    entry_points={
        'console_scripts': ['autograder=autograder.__main__:main']
    },

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