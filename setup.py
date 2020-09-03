import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="FLINCKMeshio",  # Replace with your own username
    version="20.8.24",
    author="Marcus Svensson",
    author_email="marcus.svensson@flinck.io",
    description="MeshIO extension",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/MarcusAndreasSvensson/meshio",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: Proprietary License",
        "Operating System :: OS Independent",
        "Development Status :: 2 - Pre-Alpha",
    ],
    python_requires=">=3.7",
)
