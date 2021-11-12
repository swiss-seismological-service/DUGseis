from setuptools import setup, find_packages, Extension

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    required_list = f.read().splitlines()


cmodule = Extension('aurem/src/aurem_clib',
                    sources=['aurem/src/aurem_clib.c'],
                    extra_compile_args=["-O3"])

setup(
    name="aurem",
    version="1.0.2",
    author="Matteo Bagagli",
    author_email="matteo.bagagli@erdw.ethz.com",
    description="Auto REgressive Models for time series transient identification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    # url="https://github.com/billy4all/quake",
    python_requires='>=3.6',
    install_requires=required_list,
    packages=find_packages(),
    package_data={"aurem": ['src/*.c']},
    include_package_data=True,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: Unix",
        "Intended Audience :: Science/Research",
    ],
    ext_modules=[cmodule]
)


# ========== HELP

# In this example, setup() is called with additional meta-information,
# which is recommended when distribution packages have to be built.
# For the extension itself, it specifies preprocessor defines,
# include directories, library directories, and libraries.
# Depending on the compiler, distutils passes this information in
# different ways to the compiler.
# For example, on Unix, this may result in the compilation commands

# ```
# gcc -DNDEBUG -g -O3 -Wall -Wstrict-prototypes -fPIC -DMAJOR_VERSION=1 \
#     -DMINOR_VERSION=0 -I/usr/local/include \
#     -I/usr/local/include/python2.2 -c demo.c \
#     -o build/temp.linux-i686-2.2/demo.o

# gcc -shared build/temp.linux-i686-2.2/demo.o -L/usr/local/lib -ltcl83
#     -o build/lib.linux-i686-2.2/demo.so
# ```

# These lines are for demonstration purposes only; distutils users
# should trust that distutils gets the invocations right.

# The manifest template has one command per line, where each command specifies a set of files to include or exclude from the source distribution. For an example, again we turn to the Distutils’ own manifest template:

# include *.txt
# recursive-include examples *.txt *.py
# prune examples/sample?/build

# The meanings should be fairly clear: include all files in the
# distribution root matching *.txt, all files anywhere under the examples
# directory matching *.txt or *.py, and exclude all directories matching
# examples/sample?/build. All of this is done after the standard include
# set, so you can exclude files from the standard set with explicit
# instructions in the manifest template. (Or, you can use the --no-defaults
# option to disable the standard set entirely.)
# There are several other commands available in the manifest template
# mini-language; see section Creating a source distribution:
# the sdist command.
