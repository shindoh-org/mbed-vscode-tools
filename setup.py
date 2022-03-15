import setuptools
import os

curdir = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(curdir, 'README.md'), 'r', encoding='utf-8') as f:
    long_description = f.read()


setuptools.setup(
    name='mbed-vscode-tools',
    version='0.1.4',
    license='MIT',
    install_requires=['click>=7.0.0, <8.0.0'],
    entry_points={
        'console_scripts': [
            'mbed-vscode-tools=mbed_vscode_tools.mbed_vscode_tools:main']
    },
    author='Keisuke Sugiura',
    author_email='mineto.tsukada@gmail.com',
    description='A command-line tool to help vscode intellisense for your mbed-os projects.',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/sterngerlach/mbed-vscode-tools',
    packages=setuptools.find_packages(),
    classifiers=[
        'Programming Language :: Python :: 3 :: Only',
        'License :: OSI Approved :: MIT License',
        'Operating System :: POSIX :: Linux'
    ],
    python_requires='>=3.6')
