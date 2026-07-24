from setuptools import setup, find_packages, Extension
from pathlib import Path
import re

package_name = "libfst"

root_dir   = Path(__file__).resolve().parent
source_dir = root_dir / "src" / package_name
init_py    = source_dir / "__init__.py"
with open(init_py, "r", encoding="utf-8") as f:
    source       = f.read()
    version      = re.search(r'__version__\s*=\s*[\'\"](.+?)[\'\"]'     , source).group(1)
    license      = re.search(r'__license__\s*=\s*[\'\"](.+?)[\'\"]'     , source).group(1)
    author       = re.search(r'__author__\s*=\s*[\'\"](.+?)[\'\"]'      , source).group(1)
    author_email = re.search(r'__email__\s*=\s*[\'\"](.+?)[\'\"]'       , source).group(1)
    description  = re.search(r'__description__\s*=\s*[\'\"](.+?)[\'\"]' , source).group(1)

assert version
assert license
assert author
assert author_email
assert description

extensions  = [
    Extension(
        f'{package_name}.Enum',
        sources = [
            str(source_dir / 'enum.c'),
        ],
        define_macros = [('PACKAGE_NAME', package_name)],
        include_dirs  = [str(source_dir)],
    ),
    Extension(
        f'{package_name}.hier',
        sources = [
            str(source_dir / 'hier.c'),
        ],
        define_macros = [('PACKAGE_NAME', package_name)],
        include_dirs  = [str(source_dir)],
    ),
    Extension(
        f'{package_name}.reader',
        sources = [
            str(source_dir / 'reader.c'),
            str(source_dir / 'libfst' / 'fstapi.c'),
            str(source_dir / 'libfst' / 'fastlz.c'),
            str(source_dir / 'libfst' / 'lz4.c'   ),
        ],
        define_macros = [('PACKAGE_NAME', package_name)],
        include_dirs  = [str(source_dir)],
    ),
    Extension(
        f'{package_name}.writer',
        sources = [
            str(source_dir / 'writer.c'),
            str(source_dir / 'libfst' / 'fstapi.c'),
            str(source_dir / 'libfst' / 'fastlz.c'),
            str(source_dir / 'libfst' / 'lz4.c'   ),
        ],
        define_macros = [('PACKAGE_NAME', package_name)],
        include_dirs  = [str(source_dir)],
    ),
]    

setup(
    name=package_name,
    version=version,
    description=description,
    long_description="GTKWave FST I/O Package",
    author=author,
    author_email=author_email,
    license=license,
    ext_modules=extensions,
    package_dir={"": "src"},
    packages=find_packages(where="src")
)
