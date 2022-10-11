"""
Setup for Firebase Functions Python.
"""
from setuptools import find_packages, setup

install_requires = [
    'flask>=2.1.2', 'functions-framework>=3.0.0', 'firebase-admin>=6.0.0',
    'pyyaml>=6.0', 'typing-extensions>=4.3.0', 'cloudevents>=1.6.1',
    'flask-cors>=3.0.10', 'pyjwt[crypto]>=2.5.0'
]

setup(
    name='firebase_functions',
    version='0.0.1',
    description='Firebase Functions Python SDK',
    install_requires=install_requires,
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    python_requires='>=3.10',
    classifiers=[
        'Development Status :: 1 - Planning',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'Programming Language :: Python :: 3.10',
    ],
)
