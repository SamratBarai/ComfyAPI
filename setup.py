from setuptools import setup, find_packages
import os

# Function to read the README file.
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname), encoding='utf-8').read()

setup(
    name='comfyapi-client', # Changed name slightly to be more descriptive and likely unique
    version='0.1.0', # Initial version
    author='Samrat', # Placeholder - User should replace
    author_email='baraisamrat20@gmail.com', # Placeholder - User should replace
    description='A Python client library for interacting with the ComfyUI API.',
    long_description=read('README.md'),
    long_description_content_type='text/markdown',
    url='https://github.com/samratbarai/comfyapi-client', # Placeholder - User should replace
    packages=find_packages(exclude=['api', 'tests*']), # Find packages automatically, exclude api examples
    install_requires=[
        'requests>=2.20.0',
        'websocket-client>=1.0.0', # Ensure compatible version
    ],
    classifiers=[
        'Development Status :: 3 - Alpha', # Initial development stage
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License', # Assuming MIT License
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
        'Topic :: Multimedia :: Graphics',
    ],
    python_requires='>=3.7', # Minimum Python version requirement
    keywords='comfyui api client stable-diffusion image-generation',
)
