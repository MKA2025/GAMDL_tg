from setuptools import setup, find_packages
import codecs
import os

# Read the contents of README.md
def read_readme():
    with codecs.open(os.path.join(os.path.dirname(__file__), 'README.md'), encoding='utf-8') as f:
        return f.read()

# Read requirements from requirements.txt
def read_requirements():
    with open('requirements.txt', 'r') as f:
        return [line.strip() for line in f if line.strip() and not line.startswith('#')]

setup(
    name='telegram-download-bot',  # Your project name
    version='0.1.0',  # Initial version
    author='Your Name',
    author_email='your.email@example.com',
    description='A Telegram bot for file downloading and management',
    long_description=read_readme(),
    long_description_content_type='text/markdown',
    url='https://github.com/yourusername/telegram-download-bot',
    
    # Package discovery
    packages=find_packages(
        exclude=[
            'tests', 
            'tests.*', 
            'docs', 
            'examples'
        ]
    ),
    
    # Dependencies
    install_requires=read_requirements(),
    
    # Extra dependencies for different environments
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
            'black',
            'flake8',
            'mypy',
        ],
        'test': [
            'pytest',
            'pytest-mock',
            'coverage',
            'faker',
        ],
        'docs': [
            'sphinx',
            'recommonmark',
        ],
    },
    
    # Entry points for CLI
    entry_points={
        'console_scripts': [
            'telegram-download-bot=app.main:main',
            'telegram-bot-cli=app.cli:main',
        ],
    },
    
    # Classifiers for PyPI
    classifiers=[
        # Specify the Python versions supported
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        
        # Development Status
        'Development Status :: 3 - Alpha',
        
        # Intended Audience
        'Intended Audience :: Developers',
        'Intended Audience :: System Administrators',
        
        # License
        'License :: OSI Approved :: MIT License',
        
        # Operating System
        'Operating System :: OS Independent',
        
        # Categories
        'Topic :: Internet :: WWW/HTTP',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'Topic :: Utilities',
    ],
    
    # Metadata
    keywords='telegram bot download file management',
    
    # Python version requirements
    python_requires='>=3.8,<4',
    
    # Package data inclusion
    package_data={
        'app': [
            'config/*.yaml',
            'config/*.json',
            'templates/*.html',
            'static/*',
        ],
    },
    
    # Data files outside the package
    data_files=[
        ('config', ['config/default.yaml']),
        ('logs', []),  # Creates an empty logs directory
    ],
    
    # Project dependencies and build system
    setup_requires=[
        'setuptools>=45.0',
        'wheel',
    ],
)
