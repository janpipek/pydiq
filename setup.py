#!/usr/bin/env python
from setuptools import setup, find_packages

setup(
    name='pydiq',
    version='0.2.0',
    packages=find_packages(),
    license='MIT',
    description='Simple open-source DICOM browser/viewer in Python and Qt4.',
    long_description=open('README.md').read(),
    author='Jan Pipek',
    author_email='jan.pipek@gmail.com',
    url='https://github.com/janpipek/pydiq',
    install_requires = [ 'pydicom', 'qtpy' ],
    entry_points = {
        'console_scripts' : [
            'pydiq = pydiq:run_app'
        ]
    }
)
