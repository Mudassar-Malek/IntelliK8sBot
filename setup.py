"""Setup script for IntelliK8sBot."""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="intellik8sbot",
    version="1.0.0",
    author="IntelliK8sBot Team",
    author_email="team@intellik8sbot.io",
    description="AI-Powered Kubernetes Management Assistant",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-org/intellik8sbot",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Systems Administration",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    python_requires=">=3.11",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "intellik8s=cli:app",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["static/*", "k8s/*"],
    },
)
