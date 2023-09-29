# -*- coding: utf-8 -*-
from setuptools import setup, find_packages
import re, ast

version = '0.0.1'

with open('requirements.txt') as f:
	install_requires = f.read().strip().split('\n')
	
setup(
	name='warranty_management',
	version=version,
	description='Warranty Management Process',
	author='Matiyas Solutions LLP',
	author_email='business@matiyas.com',
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
