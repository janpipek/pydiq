from setuptools import setup, find_packages

setup(
    name='pydiq',
    version='0.1.1',
    packages=find_packages(),
    license='MIT',
    description='Simple open-source DICOM browser/viewer in Python and Qt4.',
    long_description=open('README').read(),
    author='Jan Pipek',
    author_email='jan.pipek@gmail.com',
    url='https://github.com/janpipek/pydiq',
    install_requires = [ 'pydicom' ]
)