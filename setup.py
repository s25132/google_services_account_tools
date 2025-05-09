from setuptools import setup, find_packages


setup(
    name='google_services_account_tools',  
    version='1.4.0',
    packages=find_packages(),
    install_requires=['google', 'google-api-python-client', 'datetime', 'pandas'],
    author='author',
    author_email='author@email.com',
    description='Biblioteka dla google_services_account_tools',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.6',
)
