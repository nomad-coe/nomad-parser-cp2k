from setuptools import setup, find_packages


def main():
    setup(
        name="cp2kparser",
        version="0.1",
        package_data={
            'cp2kparser.versions.cp2k262': ['input_data/cp2k_input_tree.pickle'],
        },
        description="NoMaD parser implementation for CP2K.",
        author="Lauri Himanen",
        author_email="lauri.himanen@aalto.fi",
        license="GPL3",
        package_dir={'': 'parser/parser-cp2k'},
        packages=find_packages(),
        install_requires=[
            'nomadcore',
        ],
    )

if __name__ == "__main__":
    main()
