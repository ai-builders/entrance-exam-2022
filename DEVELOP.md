# Development Notes

This project adopts the new configuration file  [`pyproject.toml`](pyproject.toml)
per [PEP 518](https://www.python.org/dev/peps/pep-0518/)
and uses [Poetry](https://python-poetry.org/) as build dependency.
Although Poetry is not required to use this project just for notebook grading,
we recommend installing it for project development.


## Project Structure

- [`src/nbnursery`](src/nbnursery) Python source code to grading scripts
- [`exam.ipynb`](exam.ipynb) Jupyter notebook containing exam questions
- [`grade.py`](grade.py) Grading script for [`exam.ipynb`](exam.ipynb)

## Development Setup

1. Install the following tools to local development machine:
   - Python ≥ 3.7.1, < 3.8.0 (pro tip: use [pyenv](https://github.com/pyenv/pyenv))
   - [Poetry 1.2.0a2](https://python-poetry.org/docs/master/)
   - [Just](https://github.com/casey/just)
   - [Pre-commit](https://pre-commit.com/)
2. Install dependencies with Poetry
   ```shell
   $ poetry install
   ```
   and run post installation script (will install pre-commit hooks)
   ```shell
   $ just post-install
   ```

## Package Dependency Management

All Python package dependencies are configured in [`pyproject.toml`](pyproject.toml).
The pre-commit script will ensure that frozen dependencies
are automatically generated and saved into
[`poetry.lock`](poetry.lock) and [`requirements.txt`](requirements.txt).
