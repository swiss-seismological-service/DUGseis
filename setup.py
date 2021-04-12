#  Setup Script for DUG-Seis
#
# :copyright:
#    ETH Zurich, Switzerland and The ObsPy Development Team (devs@obspy.org)
# :license:
#    GNU Lesser General Public License, Version 3
#    (https://www.gnu.org/copyleft/lesser.html)
#


import sys
from setuptools import setup, find_packages


if sys.version_info[:2] < (3, 6):
    raise RuntimeError("Python version >= 3.6 required.")

_authors = [
    'Joseph Doetsch',
    'Linus Villiger',
    'Thomas Haag',
    'Sem Demir']
_authors_email = [
    'joseph.doetsch@erdw.ethz.ch',
    'linus.villiger@sed.ethz.ch']

_install_requires = [
    "pyside6",
    "pyqtgraph",
    "pyopengl",
    "obspy",
    "tqdm",
    "click",
    "pyyaml",
    "oyaml",
    "pyasdf",
    "pandas",
    "pyproj",
    "numba",
    ]

setup(
    name='DUG-Seis',
    version='0.0',
    author=' (SCCER-SoE, SED, ETHZ),'.join(_authors),
    author_email=', '.join(_authors_email),
    description=('Data acquisition and real-time processing of'
                 'induced seismicity during rock-laboratory experiments. '),
    license='LGPL',
    keywords=[
        'induced seismicity',
        'seismology'],
    url='https://gitlab.seismo.ethz.ch/doetschj/DUG-Seis.git',
    classifiers=[
        'Environment :: Console',
        'Environment :: X11 Applications :: Qt',
        'Intended Audience :: Science/Research',
        ('License :: OSI Approved :: GNU Lesser '
            'General Public License v3 or later (LGPLv3+)'),
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Topic :: Scientific/Engineering', ],
    platforms=['Linux', 'MAC', 'Windows'],
    install_requires=_install_requires,
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    entry_points={
        'console_scripts': ['dug-seis=dug_seis.cmd_line:cli']}
)

# ----- END OF setup.py -----
