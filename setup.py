from setuptools import setup, find_packages

setup(
    name='hackathon_project',
    version='0.1.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=4.0',
        # Add other dependencies here
    ],
    entry_points={
        'console_scripts': [
            'hackathon-manage = manage:main',
        ],
    },
    description='Django Hackathon Project',
    author='Your Name',
    author_email='your@email.com',
    url='https://github.com/1002merve/Hackathon',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Framework :: Django',
    ],
)
