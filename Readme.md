python-libfst
==================================================================================

Installation
----------------------------------------------------------------------------------

### From source:

#### 1. Install required tools:

 * GCC or Clang compiler
 * Python development headers (e.g., `python3-dev` on Linux)

#### 2. Clone the repository:

```console
shell$ git clone https://github.com/ikwzm/python-libfst.git
shell$ cd python-libfst
```

#### 3. Build libfst module

```console
shell$ python3 setup.py build_ext --inplace
```

#### 4. Install libfst package

```console
shell$ sudo python3 setup.py install
```

