from setuptools import setup

setup(
    name='beams',
    version='0.1.0',
    description='Basic and Effective Analysis for Muon-Spin Spectroscopy',
    author='Alec Petersen, Ben Frandsen',
    author_email='k.alecpetersen@gmail.com',
    url='https://github.com/aPeter1/BEAMS',
    packages=['beams'],
    install_requires=[
        'numpy',
        'pandas',
        'sympy',
        'scipy',
        'matplotlib',
        'requests',
        'pyqt5'
    ]
)