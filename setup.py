from setuptools import setup, find_packages

with open("README.md", "r") as f:
    long_description = f.read()

setup(
    name='beams',
    version='0.1.0',
    description='Basic and Effective Analysis for Muon-Spin Spectroscopy',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author='Alec Petersen, Ben Frandsen',
    author_email='k.alecpetersen@gmail.com',
    url='https://github.com/aPeter1/BEAMS',
    classifiers=[

    ],
    keywords="muon musr spin relaxation resonance spectroscopy",
    packages=find_packages(),
    install_requires=[
        'numpy',
        'pandas',
        'sympy',
        'scipy',
        'matplotlib',
        'requests',
        'pyqt5'
    ],
    python_requires="~=3.5"
)