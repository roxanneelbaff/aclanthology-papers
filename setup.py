import setuptools
from setuptools import setup

setup(
    name='aad',
    version='0.2',
    description='Python package for downloading aclanthology papers based on keywords',
    # url='',
    author='Roxanne El Baff',
    author_email='roxanne.elbaff@gmail.com',
    license='MIT',
    packages=setuptools.find_packages(),
    install_requires=[
                      'pandas',
                      'tqdm',
                      'bibtexparser==1.4.0'
                      ],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python',
    ],
    #zip_safe=False,
    #include_package_data=True,
    #package_data={"../data": ["*"]},
)
