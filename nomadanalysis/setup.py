from setuptools import setup


#===============================================================================
def main():
    # Start package setup
    setup(
        name="nomadanalysis",
        version="0.1",
        description="Tools for analysing calculation results parsed by NOMAD parsers.",
        author="Lauri Himanen",
        author_email="lauri.himanen@gmail.com",
        license="GPL3",
        packages=["nomadanalysis"],
        install_requires=[
            'pint',
            'numpy',
        ],
        zip_safe=False
    )

# Run main function by default
if __name__ == "__main__":
    main()
