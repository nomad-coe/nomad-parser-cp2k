"""
This is a setup script for installing the parser locally on python path with
all the required dependencies. Used mainly for local testing.
"""
from setuptools import setup


#===============================================================================
def main():
    # Start package setup
    setup(
        name="cp2kparser",
        version="0.1",
        include_package_data=True,
        package_data={
            '': ['*.pickle'],
        },
        description="NoMaD parser implementation for CP2K",
        author="Lauri Himanen",
        author_email="lauri.himanen@gmail.com",
        license="GPL3",
        packages=["cp2kparser"],
        install_requires=[
            'pint',
            'numpy',
        ],
        zip_safe=False
    )

# Run main function by default
if __name__ == "__main__":
    main()
