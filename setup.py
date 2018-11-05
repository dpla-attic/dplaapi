"""
dplaapi
~~~~~~~

A web API for querying the Digital Public Library of America's metadata
"""

import re
import sys
import ast
from setuptools import setup, find_packages

if sys.version_info.major != 3 and sys.version_info.minor != 6 \
        and sys.version_info.micro != 6:
    print('Python 3.6.6 required.', file=sys.stderr)
    exit(1)

_version_re = re.compile(r'__version__\s+=\s+(.*)')

with open('dplaapi/__init__.py', 'rb') as f:
    version = str(ast.literal_eval(_version_re.search(
        f.read().decode('utf-8')).group(1)))

setup(name='dplaapi',
      version=version,
      description='Digital Public Library of America web API',
      long_description=__doc__,
      url='https://pro.dp.la/developers/api-codex',
      project_urls={
          'Source Code': 'https://github.com/dpla/dplaapi'
      },
      author='DPLA Tech Team',
      author_email='tech@dp.la',
      packages=find_packages(),
      scripts=['bin/devapi'],
      install_requires=[
          'starlette~=0.7.0',
          'apistar~=0.6.0',
          'uvicorn~=0.3.2',
          'gunicorn~=19.9.0',
          'peewee~=3.6.0',
          'psycopg2-binary~=2.7.5',
          'boto3~=1.8.6',
          'cachetools~=2.1.0'
      ],
      extras_require={
        'dev': [
          'pytest~=3.7.2',
          'pytest-asyncio~=0.9.0',
          'pytest-cov~=2.5.1',
          'pytest-mock~=1.10.0',
          'flake8~=3.5.0',
          'coverage~=4.5.1',
          'codacy-coverage~=1.3.11'
        ]
      },
      license='MIT')
