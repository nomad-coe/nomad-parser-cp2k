from setuptools import setup, find_packages


#===============================================================================
def main():
    # Start package setup
    setup(
        name="parsercp2k",
        version="0.1",
        include_package_data=True,
        package_data={
            '': ['*.json', '*.pickle'],
        },
        description="NoMaD parser implementation for CP2K",
        author="Lauri Himanen",
        author_email="lauri.himanen@gmail.com",
        license="GPL3",
        packages=["parsercp2k"],
        install_requires=[
            'pint',
            'numpy',
            'ase'
        ],
        zip_safe=False
    )

# Run main function by default
if __name__ == "__main__":
    main()
