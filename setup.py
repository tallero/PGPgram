"""Setup for PGPgram"""
from platform import system, machine
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name="PGPgram",
    version="0.4",
    author="Pellegrino Prevete",
    author_email="pellegrinoprevete@gmail.com",
    description="GPG encrypted backups on telegram",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/tallero/PGPgram",
    packages=find_packages(),
    package_data={
        '': ['libtdjson_{}_{}.so'.format(system(), machine())],
    },
    entry_points={
        'console_scripts': ['pgpgram = pgpgram:main']
    },
    install_requires=[
        'appdirs',
        'setproctitle',
        'sqlitedict',
        'trovotutto',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU Affero General Public License v3 or later (AGPLv3+)",
        "Operating System :: Unix",
    ],
)
