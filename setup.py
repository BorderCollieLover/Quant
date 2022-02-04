#in the root folder, create a setup file
#python3 -m pip install setuptools
import setuptools

setuptools.setup(
    name="quantlib",
    version="0.1",
    description="quantlib by hangukquant",
    url="#",
    author="HangukQuant",
    install_requires = ["opencv-python"],
    author_email="",
    packages=setuptools.find_packages(),
    zip_safe=False
) # i have no idea what these parameters do, I just found it on Stack Overflow. 

