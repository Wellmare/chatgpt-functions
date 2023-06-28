# import os
# from pathlib import Path
from setuptools import setup, find_packages


def readme():
    with open("README.md", "r") as f:
        return f.read()


# script_path = Path(os.path.dirname(os.path.abspath(__file__)))

# def read_requirements():
#     with open(script_path / 'requirements.txt', 'rb') as file:
#         content = file.read().decode('utf-8')
#     lines = content.splitlines()
#     lines = [line.strip() for line in lines if line.strip()]
#     return lines


setup(
    name="chatgpt_functions",
    version="0.1.4",
    author="Wellmare",
    author_email="ivan.kolipov@gmail.com",
    description="Wrapper over the gpt3.5 model, capable of calling functions",
    long_description=readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/Wellmare/chatgpt-functions",
    packages=find_packages(),
    install_requires=["loguru==0.7.0", "openai==0.27.8", "python-dotenv==1.0.0"],
    classifiers=[
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    keywords="chatgpt functions gpt",
    # project_urls={"Documentation": "link"},
    python_requires=">=3.7",
)
