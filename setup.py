from setuptools import setup, find_packages

setup(
    name="pg-optimizer",
    version="1.0.0",
    author="Табачкова А.М.",
    description="Автоматическая оптимизация PostgreSQL с использованием генетических алгоритмов",
    packages=find_packages(),
    install_requires=[
        "docker>=6.0.0",
        "psutil>=5.9.0",
        "pandas>=2.0.0",
        "matplotlib>=3.5.0",
        "seaborn>=0.12.0",
        "numpy>=1.24.0",
        "deap>=1.3.0",
    ],
    entry_points={
        "console_scripts": [
            "pg-optimizer=pg_optimizer.cli:main",
        ],
    },
    python_requires=">=3.9",
)