from pathlib import Path
from setuptools import setup
from marketdata import __version__


requirements_path = Path(Path.cwd(), "requirements.txt")
with open(requirements_path) as f:
    install_requires = f.readlines()

SETUP_REQUIRES = ["setuptools", "wheel"]

setup(
    name="marketdata",
    version=__version__,
    description="Gets market, securities and currencies information",
    author="Vlad Bezden",
    author_email="vladbezden@gmail.com",
    packages=["marketdata"],
    install_requires=install_requires,
    setup_requires=SETUP_REQUIRES,
    python_requires=">=3.7",
    entry_points={"console_scripts": ["marketdata=marketdata.main:main"]},
)
