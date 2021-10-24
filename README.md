
### Features

- Convert binary data files from multiple µSR facilities.
- Display and interact with multiple sets of data.
- Write your data to a common file type.
- Compatible with Linux, Mac and Windows

# BEAMS
> A simple interface for visualizing and analyzing µSR data.

**Table of Contents**

## Getting Started

### Prerequisites
- Python 3.6 or greater

### Installation
- Download or clone this repository.
- Open a terminal and navigate to the BEAMS folder.

#### Without Anaconda
- Run the following command to install the package requirements for BEAMS
```shell
$ python -m pip install -r python_requirements.txt
```
#### Anaconda
- Run the following command in the anaconda prompt to install requirements.
```shell
$ conda install -c anaconda --file conda_requirements.txt
```

Start BEAMS for either, once you have navigated to the directory with the following
```shell
$ python beams
```

### Troubleshooting
#### Can't install requirements on Mac (Apple Silicon)
For trouble installing requirements on Apple Silicon see the answer to this issue: https://github.com/scipy/scipy/issues/13409

#### Text in file trees is truncated
If the text is truncated you most likely don't have PyQt5 installed (you can confirm this by running 'pip freeze' in the terminal and you will probably see QtPy). Simply fix by using pip to install PyQt5.
 
```shell
$ pip install PyQt5
```
