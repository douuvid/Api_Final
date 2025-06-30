from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="france-travail-api",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A Python client for the France Travail (Pôle Emploi) API",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/france-travail-api",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
    install_requires=[
        'requests>=2.25.0',
    ],
    extras_require={
        'dev': [
            'pytest>=6.0',
            'black>=21.5b2',
            'isort>=5.8.0',
            'mypy>=0.812',
        ],
    },
)
