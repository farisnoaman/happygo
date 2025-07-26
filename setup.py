from setuptools import setup, find_packages

setup(
    name='hayago_mapping',
    version='0.0.1',
    description='Hayago Mapping App for Frappe',
    author='farisnoaman',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=['frappe'],
)
