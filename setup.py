from setuptools import setup, find_packages

setup(
    name="instadroid",
    version="0.1.0",
    author="Alicia Lorandi",
    author_email="alicia.lorandi00@yahoo.com",
    description="InstaDroid - A package for automated Instagram interactions and scraping",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/alicialorandi/InstaDroid",
    license="GPLv3",
    packages=find_packages(),
    install_requires=[
        "python-dotenv",
        "pytz",
        "requests",
        "selenium",
        "selenium-stealth",
        "webdriver_manager"
    ],
    extras_require={
        "test": ["pytest"]
    },
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Development Status :: 5 - Production/Stable",
        "Topic :: Utilities",
        "Topic :: Software Development :: Build Tools",
    ],
    python_requires=">=3.7, <3.12",
    keywords="python, instadroid, instagram, automation, social media, bot, scraping, selenium",
    include_package_data=True,
    entry_points={
        "console_scripts": [
            # upcoming CLI script
        ],
    },
)