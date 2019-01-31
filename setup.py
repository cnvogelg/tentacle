from setuptools import setup, find_packages

setup(name='tentacle',
      version='0.1',
      description='An OctoPrint frontend suitable for small displays',
      url='http://github.com/cnvogelg/tentacle',
      author='Christian Vogelgsang',
      author_email='chris@vogelgsang.org',
      license='GLPv3',
      packages=find_packages(),
      zip_safe=True,
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
