from setuptools import setup, find_packages

setup(
    name="self_healing",
    version="0.1",
    packages=find_packages(),
    install_requires=["openai", "PyGithub"],
)
