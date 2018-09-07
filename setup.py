import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dh_testers",
    version="0.1.0",
    author="Michael Scott Cuthbert",
    author_email="cuthbert@mit.edu",
    description="Testing module for projects, including dh",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dhmit/dh_testers",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ],
)
