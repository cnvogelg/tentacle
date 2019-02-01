from setuptools import setup, find_packages


# fetch version, author, ...
exec(open("tentacle/__about__.py").read())


def read_readme():
    """read README.rst file."""
    with open("README.rst") as fobj:
        return fobj.read()


setup(name=__title__,
      version=__version__,
      description=__summary__,
      long_description=read_readme(),
      url=__uri__,
      author=__author__,
      author_email=__email__,
      license=__license__,
      packages=find_packages(),
      zip_safe=False,
      include_package_data=True,
      install_requires=[
          'qdarkstyle',
          'octorest'
      ],
      entry_points={
          'console_scripts': [
              'tentacle = tentacle.__main__:main'
          ]
      }
      )
