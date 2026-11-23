import setuptools

with open('README.md', 'r', encoding='utf-8') as fh:
    long_description = fh.read()


setuptools.setup(
    name='adaptive-tree-of-thoughts',
    author='Rohit Mitharwal',
    author_email='rohitmitharwal19@gmail.com',
    description='Adaptive Tree of Thoughts: Dynamic Beam Pruning and Early-Exit Verification for Token-Efficient LLM Reasoning',
    url='https://github.com/rohitmitharwal19/adaptive-tree-of-thoughts',
    project_urls={
        'Homepage': 'https://github.com/rohitmitharwal19/adaptive-tree-of-thoughts',
    },
    package_dir={'': 'src'},
    packages=setuptools.find_packages(where='src'),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        'Intended Audience :: Science/Research',
        'Topic :: Scientific/Engineering :: Artificial Intelligence',
    ],
    python_requires='>=3.7',
    install_requires=[
        'setuptools',
    ],
    include_package_data=True,
)
