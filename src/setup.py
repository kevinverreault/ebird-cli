from setuptools import setup, find_packages

setup(
    name="ebird_cli",
    version="0.1",
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'ebird_cli=ebird_cli.main:main',
        ],
    },
    author="Kevin Verreault",
    author_email="dev@kevinverreault.com",
    description="eBird CLI",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
