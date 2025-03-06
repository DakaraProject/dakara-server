# Contributing

## Development

### Dependencies

For development, you need the extra dependencies:

```sh
pip install -r requirements_dev.txt
```

### Tests

Tests are run by [Pytest](https://docs.pytest.org/en/stable/) with:

```sh
pytest
```

Both Pytest style and standard Unittest style tests can be used.
Coverage is checked automatically with [Pytest-cov](https://pypi.org/project/pytest-cov/).

### Imports

Imports are sorted by [isort](https://pycqa.github.io/isort/) with the command:

```sh
isort .
```

You need to call isort before committing changes.

### Code style

The code follows the [PEP8](https://www.python.org/dev/peps/pep-0008/) style guide (88 characters per line).
Quality of code is checked with [Ruff](https://pypi.org/project/ruff/):

```sh
ruff check .
```

Style is enforced using [Black](https://github.com/ambv/black):

```sh
black .
```

You need to call Black before committing changes.
You may want to configure your editor to call it automatically.
Additionnal checking can be manually performed with [Pylint](https://www.pylint.org/).

### Hooks

Pre-commit hooks allow to perform checks before commiting changes.
They are managed with [Pre-commit](https://pre-commit.com/), use the following command to install them:

```sh
pre-commit install
```

### API documentation

The project uses [`drf-spectacular`](https://pypi.org/project/drf-spectacular/) for the self-documentation of the API.
You can generate and browse it locally with:

```sh
./manage.py spectacular --color --file schema.yml
docker run -p 80:8080 -e SWAGGER_JSON=/schema.yml -v ${PWD}/schema.yml:/schema.yml swaggerapi/swagger-ui
```

## Release

1. Move to the `develop` branch and pull.
   ```sh
   git checkout develop
   git pull
   ```
   If there are cosmetic modifications to perform on the changelog file, do it now.
2. Call the bump version script:
   ```sh
   ./bump_version.sh 0.0.0 0.1.0
   ```
   with `0.0.0` the release version number and `0.1.0` the next version (without 'v', without '-dev').
3. Push the version commit and its tag:
   ```sh
   git push
   git push --tags
   ```
4. Move to the `master` branch and merge created tag into it.
   Then push.
   ```sh
   git checkout master
   git pull
   git merge 0.0.0
   git push
   ```
5. Before creating the server bundle, make sure dependencies are up to date:
   ```sh
   pip install -r requirements.txt -r requirements_dev.txt
   ```
6. Call the script to create the archive:
   ```sh
   ./create_archive.sh 0.0.0 9.9.9
   ```
   with `0.0.0` the according version number and `9.9.9` the corresponding Dakara web client version number.
7. On GitHub, draft a new release, set the version number with the created tag ("Existing tag" should read).
   Set the release title with "Version 0.0.0" (with number, you get it?).
   Copy-paste corresponding section of the changelog file in the release description.
   Add the created archive file.
   You can now publish the release.
