from pathlib import Path
from pybind11.setup_helpers import Pybind11Extension, build_ext
from setuptools import setup

module = Pybind11Extension('operations',
                           [str(fname) for fname in Path('src').glob('*.cpp')],
                           include_dirs = ['include'],
                           extra_complie_args = ['-03']
                           )

setup(
    name='operations',
    version='0.1',
    author='CHANG, Wei-Chen',
    author_email='wcchang@gmail.com',
    description='Basic image/video operations',
    ext_modules=[module],
    cmdclass={"build_ext": build_ext},
)