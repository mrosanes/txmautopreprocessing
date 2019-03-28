#!/usr/bin/env python

from setuptools import setup, find_packages

# The version is updated automatically with bumpversion
# Do not update manually
__version = '1.0.0-alpha'

long_description = """This is a DS to execute MISTRAL preprocessing Workflows
"""


classifiers = [
    'Development Status :: 3 - Alpha',
    'Intended Audience :: Developers',
    'Topic :: Scientific/Engineering',
    'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
    'Programming Language :: Python :: 2.7',
]

setup(
    name='TXMAutoPreprocessing',
    version=__version,
    packages=find_packages(),
    entry_points={
        'console_scripts': ['TXMAutoPreprocessing = TXMAutoPreprocessing.TXMAutoPreprocessing:runDS']
    }, # METADATA
    author='Carlos Falcon',
    author_email='cfalcon@cells.es',
    include_package_data=True,
    license='LGPL',
    description='TXMAutoPreprocessing Device Server',
    long_description=long_description,
    requires=['setuptools (>=1.1)'],
    install_requires=['PyTango'],
    classifiers=classifiers
)
