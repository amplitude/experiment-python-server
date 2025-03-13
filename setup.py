import sys
from setuptools import setup
import pathlib

here = pathlib.Path(__file__).parent.resolve()
sys.path.insert(0, str(here / 'src'))

version = {}
with open("src/amplitude_experiment/version.py") as fp:
    exec(fp.read(), version)

# Get the long description from the README file
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="amplitude-experiment",
    version=version['__version__'],
    description="The official Amplitude Experiment Python SDK for server-side instrumentation.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/amplitude/experiment-python-server",
    author="Amplitude Inc.",
    author_email="sdk.dev@amplitude.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
    keywords="amplitude, python, backend",
    install_requires=["dataclasses-json>=0.6.7","amplitude_analytics>=1.1.1","sseclient-py~=1.8.0"],
    package_dir={"": "src"},
    packages=["amplitude_experiment"],
    include_package_data=True,
    python_requires=">=3.6, <4",
    license='MIT License',
    project_urls={
        "Bug Reports": "https://github.com/amplitude/experiment-python-server/issues",
        "Source": "https://github.com/amplitude/experiment-python-server",
        "Developer Doc": "https://www.docs.developers.amplitude.com/experiment/sdks/python-sdk/"
    }
)
