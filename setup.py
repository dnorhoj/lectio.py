import setuptools

with open("README.md", "r") as f:
    long_description = f.read()

setuptools.setup(
    name="lectio.py",
    version="0.0.1",
    author="dnorhoj",
    author_email="daniel.norhoj@gmail.com",
    description="Interact with lectio through python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dnorhoj/lectio.py",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
)
