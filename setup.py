from setuptools import setup

setup(name='pypublishsubscribe',
      version='0.1',
      description='A simple Python Publish-Subscribe server.',
      author='Ruarc Sorensen',
      author_email='ruarcs@gmail.com',
      license='MIT',
      packages=['pypublishsubscribe'],
      install_requires=[
          'twisted',
          'requests'
      ],
      zip_safe=False)
