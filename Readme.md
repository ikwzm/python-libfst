python-libfst
==================================================================================

Overview
----------------------------------------------------------------------------------

Python bindings for GTKWave FST library.

`python3-libfst` provides Python interfaces for reading and writing
GTKWave FST (Fast Signal Trace) waveform files.

The package contains C extension modules based on the FST library:

- `libfst.reader` - FST waveform reader
- `libfst.writer` - FST waveform writer
- `libfst.hier`   - FST hierarchy objects
- `libfst.Enum`   - FST enumeration support


Install
----------------------------------------------------------------------------------

### Requirements

#### Software

- Python 3.9 or later
- setuptools
- C compiler (gcc or clang)
- Git


#### Debian / Ubuntu

Install required packages:

```bash
sudo apt install python3-dev python3-pip build-essential git
```

### Get Source Code

Clone the repository with the FST library submodule:

```bash
git clone --recurse-submodules https://github.com/ikwzm/python-libfst.git
cd python-libfst
```

If the repository was cloned without submodules:

```bash
git submodule update --init --recursive
```

The FST library source is included as a git submodule:

```
libfst/
└── src/
    ├── fstapi.c
    ├── fstapi.h
    ├── fastlz.c
    └── lz4.c
```

### Build

Build the extension modules:

```bash
python setup.py build_ext --inplace
```

### Install Package

Install the package into the current Python environment:

```bash
python -m pip install .
```

For development, use editable installation:

```bash
python -m pip install -e .
```

### Verify Installation

Run Python:

```bash
python
```

Check import:

```python
import libfst

print(libfst.__version__)
```

License
----------------------------------------------------------------------------------

This project uses the GTKWave FST library.

See the license information in the included FST source tree.


