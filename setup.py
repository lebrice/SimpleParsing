from __future__ import annotations

import sys

import setuptools

import versioneer

with open("README.md") as fh:
    long_description = fh.read()
packages = setuptools.find_namespace_packages(include=["simple_parsing*"])
print("PACKAGES FOUND:", packages)
print(sys.version_info)

with open("requirements.txt") as req_file:
    install_requires = req_file.read().splitlines(keepends=False)

extras_require: dict[str, list[str]] = {
    "test": [
        "pytest",
        "pytest-xdist",
        "pytest-regressions",
        "pytest-benchmark",
        "numpy",
        # "torch",
    ],
    "yaml": ["pyyaml"],
}
extras_require["all"] = list(set(sum(extras_require.values(), [])))


setuptools.setup(
    name="simple_parsing",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    author="Fabrice Normandin",
    author_email="fabrice.normandin@gmail.com",
    description="A small utility for simplifying and cleaning up argument parsing scripts.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/lebrice/SimpleParsing",
    packages=packages,
    package_data={"simple_parsing": ["py.typed"]},
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.7",
    install_requires=install_requires,
    extras_require=extras_require,
    setup_requires=["pre-commit"],
)
