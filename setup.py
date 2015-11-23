from setuptools import setup


#===============================================================================
def main():
    # Start package setup
    setup(
        name="cp2kparser",
        version="0.1",
        description="NoMaD parser implementation for CP2K",
        author="Lauri Himanen",
        author_email="lauri.himanen@gmail.com",
        license="GPL3",
        packages=["cp2kparser"],
        install_requires=[
            'pint',
            'numpy',
            'enum34',
            'ase'
        ],
        zip_safe=False
    )

# Run main function by default
if __name__ == "__main__":
    main()
