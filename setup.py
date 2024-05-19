from setuptools import setup, find_packages

#entry_points={'console_scripts': ['pruby = pruby.__main__:main',]},
setup(
    name="pruby",
    version="1.00",
    install_requires=["wxPython","numpy","pandas","matplotlib","pypubsub"],

    package_dir={"": "src"},
    packages=find_packages(where="src"),
    # scripts=["pruby/main.py"],  
    author="Riccardo Galafassi",
    description="Program that reads and fit ruby files.",
    longdesctiption=open("Readme.md").read(),
)