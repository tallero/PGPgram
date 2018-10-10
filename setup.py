from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(
    name = "PGPgram",
    version = "0.1",
    author = "Pellegrino Prevete",
    author_email = "pellegrinoprevete@gmail.com",
    description = "GPG encrypted backups on telegram",
    long_description = long_description,
    long_description_content_type = "text/markdown",
    url = "https://github.com/tallero/PGPgram",
    packages = find_packages(),
    package_data = {
        '': ['libtdjson.so'],
    },
    entry_points = {
        'console_scripts': ['pgpgram = pgpgram:main']
    },
    install_requires = [
    'trovotutto',
    'pyxdg',
    ],
    classifiers = [
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Operating System :: Unix",
    ],
)
