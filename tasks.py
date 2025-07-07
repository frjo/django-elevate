from functools import partial

from invoke import run as _run
from invoke import task

# Always echo out the commands
run = partial(_run, echo=True, pty=True)


@task
def lint(c, verbose=False):
    "Run ruff linter"
    c.run("uv run ruff check --fix{0}".format(" --verbose" if verbose else ""))


@task(lint)
def test(c, verbose=False):
    "Run tests using tox"
    c.run("tox --skip-missing-interpreters{0}".format(" -- -v" if verbose else ""))


@task
def clean(c):
    "Clean working directory"
    c.run("rm -rf *.egg-info *.egg")
    c.run("rm -rf dist build")


@task(clean)
def release(c):
    "Cut a new release"
    version = c.run("python setup.py --version").stdout.strip()
    assert version, "No version found in setup.py?"

    print("### Releasing new version: {0}".format(version))
    c.run("git tag {0}".format(version))
    c.run("git push --tags")

    c.run("python setup.py sdist bdist_wheel")
    c.run("twine upload -s dist/*")
