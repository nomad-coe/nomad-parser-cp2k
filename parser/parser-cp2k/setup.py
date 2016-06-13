"""
This is a setup script for installing the parser locally on python path with
all the required dependencies. Used mainly for local testing.
"""
from setuptools import setup, find_packages


#===============================================================================
def main():
    # Start package setup
    setup(
        name="cp2kparser",
        version="0.1",
        include_package_data=True,
        package_data={
            'cp2kparser.versions.cp2k262': ['input_data/cp2k_input_tree.pickle'],
        },
        description="NoMaD parser implementation for CP2K.",
        author="Lauri Himanen",
        author_email="lauri.himanen@aalto.fi",
        license="GPL3",
        packages=find_packages(),
        install_requires=[
            'pint',
            'numpy',
            'mdtraj',
            'ase'
        ],
        zip_safe=False
    )

# Run main function by default
if __name__ == "__main__":
    main()
