from setuptools import setup, find_packages

with open("README.md") as file:
    readme = file.read()

setup(
    name="mpris-rich-presence",
    author="nickofolas",
    url="https://github.com/nickofolas/mpris-rich-presence",
    version="0.1.1",
    license="MIT",
    description="Uses Playerctl to generate Discord Rich Presence",
    long_description=readme,
    packages=find_packages(),
    include_package_data=True,
    entry_points={"console_scripts": ["mpris-rich-presence=mpris_rich_presence.app:main"]}
)
