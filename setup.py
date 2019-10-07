import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="simple_parsing",
    version="0.0.1",
    author="Fabrice Normandin",
    author_email="fabrice.normandin@gmail.com",
    description="A small utility for simplifying and cleaning up argument parsing scripts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lebrice/EasyArgs",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.7',
)