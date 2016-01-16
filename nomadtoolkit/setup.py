from setuptools import setup
import os


#===============================================================================
def main():
    # Start package setup
    setup(
        name="nomadtoolkit",
        version="0.1",
        description="Tools for analysing calculation results parsed by NOMAD parsers.",
        author="Lauri Himanen",
        author_email="lauri.himanen@gmail.com",
        license="GPL3",
        packages=["nomadtoolkit"],
        install_requires=[
            'pint',
            'numpy',
        ],
        zip_safe=False
    )

# Run main function by default
if __name__ == "__main__":

    # Install the toolkit package
    main()

    # Save the path where the metainfo are saved for further use
    import nomadtoolkit.config
    metapath = os.path.realpath(os.path.join(os.path.dirname(__file__), "submodules/nomad-meta-info/meta_info/nomad_meta_info"))
    nomadtoolkit.config.set_config("metaInfoPath", metapath)
