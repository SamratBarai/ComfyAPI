from setuptools import setup, find_packages
import os

# Function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8').read()

setup(
    name='comfyapi', 
    version='2.0.1', 
    author='Samrat', 
    author_email='baraisamrat20@gmail.com', 
    description='A Python client library for interacting with the ComfyUI API.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/samratbarai/comfyapi-client', 
    packages=find_packages(exclude=['api', 'tests*']), 
    install_requires=[
        'requests>=2.20.0',
        'websocket-client>=1.0.0', 
    ],
    python_requires='>=3.7', 
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    include_package_data=True,
    package_data={
        '': ['README.md'],
    },
)
