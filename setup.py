from setuptools import setup, find_packages

setup(
    name="ragchat",
    version="1.0.0",
    description="Universal Documentation & Community Chatbot (RAG)",
    author="soumen888",
    packages=find_packages(),
    py_modules=["main", "sync_daemon"],
    entry_points={
        "console_scripts": [
            "ragchat=main:main",
        ],
    },
)
