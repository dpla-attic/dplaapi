# Development Guide

## Installation for Development

First, install Python with [Pyenv](https://github.com/pyenv/pyenv).

Run this in your shell: `unset PYENV_VERSION`. This will let the `.python-
version` file dictate which Python version you're using &mdash; important for
ensuring that every developer is using the same version of Python.  When you
`cd` to the `dplaapi` directory, Pyenv will automatically switch to the correct
installation of Python.

Then make sure that you
[have virtualenv installed](https://virtualenv.pypa.io/en/stable/installation/)
in the particular Python that you're using: `pip install virtualenv`.


1. Check out this repository from git
1. `cd dplaapi`
1. `virtualenv venv` If you don't have a venv directory there now. Note that
you can easily `deactivate; rm -r venv` to start over from scratch and do
`virtualenv venv` again to rebuild it.
1. `. venv/bin/activate`  (Or `source venv/bin/activate` if `.` doesn't work in
your shell.)
1. `pip install -r requirements.txt`
1. `pip install -e .[dev]` (And ignore any `FileNotFoundError` that says that
there is no such `.egg` file for the `dplaapi` package.)
1. Then see the "Workflow" section below.

## Dependencies

### Current Dependencies

* Python 3.6.6  (See `Dockerfile`, `.python-version`, and `.travis.yml`)
* Python packages indicated in `setup.py` and `requirements.txt`


### Updating Dependencies

Read https://caremad.io/posts/2013/07/setup-vs-requirement/.

The `setup.py` file has a short list of abstract dependencies, with loose
version specifications, and `requirements.txt` describes concrete dependencies,
with all of the packages in the software environment.

For a fresh installation or a production deployment we'll use
`pip install -r requirements.txt`.

Here is an easy way to upgrade all of the application's dependencies; for
instance, to keep up-to-date with security patches:

```
$ deactivate            # get out of virtual environment ...
$ rm -r venv
$ virtualenv venv       # recreate virtual environment
$ . venv/bin/activate   # get back into virtual environment
$ python setup.py install
$ pip freeze | grep -v dplaapi
```

Now take the output of `pip freeze` and replace the section of
`requirements.txt` that lists the pinned packages. After that, you should be
able to do a `git diff` and see what packages have been upgraded. You can run
tests and perform other quality-assurance to scrutinize the behavior of the
upgraded packages before checking in the changes to `requirements.txt`.

If you want to add new packages that will be included in the API code (with
an `include` statement), those should be indicated in `setup.py`.  Likewise, if
one of those needs to be upgraded, change the version selector in
`install_requires` in `setup.py`. Go through the process described above for
upgrading packages.

Check `Dockerfile`, `.python-version`, and `.travis.yml` if you've changed
Python versions.


## Releases and Branching

See https://digitalpubliclibraryofamerica.atlassian.net/wiki/spaces/TECH/pages/87037285/Branching+and+Release+Model

We follow the OneFlow branching model described there, with `master`, `stable`,
and feature branches.

### Cutting a release:

1. Edit `dplaapi/__init__.py` and update `__version__` with the new version
number.
1. If necessary, update the copyright year in `LICENSE`.
1. Commit those changes to `master`
1. Tag, merge, and `git push` as follows:
```
$ # on the master branch ...
$ git tag -s -m 'Release X.Y.N' X.Y.N
$ git checkout stable
$ git merge --ff-only X.Y.N
$ git push origin master X.Y.N stable
```

## Workflow

You can run the following series of commands when you're working on the code.
```
$ cd /path/to/dplaapi
$ PYTHONPATH=. ES_BASE=&lt;url&gt; gunicorn -k uvicorn.workers.UvicornWorker \
  --log-level=debug --reload dplaapi:app
```
That works well if you're iterating over changes to the files and want to see
how they work. The server will reload if you modify files.

It is usually best to use the test suite to iterate over changes you're making
to project files. The code should be structured such that it's easy to run a
unit test for the module or function that you're editing.

If you want to run the app natively like that, you might want to run our
Elasticsearch and PostgreSQL Docker containers, which have sample data. You run
these so that they expose their ports on localhost:

```
$ cd /path/to/dplaapi
$ docker run -d -p 9200:9200  dplatech/dplaapi_elasticsearch:latest
$ docker run -d -p 5432:5432  dplatech/dplaapi_postgresql:latest
$ PYTHONPATH=. ES_BASE=http://localhost:9200/dpla_alias \
  gunicorn -k uvicorn.workers.UvicornWorker --log-level=debug \
  --reload dplaapi:app
```

You can also use `docker-compose up` as illustrated in [README.md](./README.md),
which runs `dplaapi`, Elasticsearch, and PostgreSQL in their own private
network on your host machine. This is good for demonstration purposes or for
emulating as close as possible how the application is going to perform in
production. It's less convenient for iterating over changes to the application,
because it uses the production Dockerfile, which does not run `gunicorn` with
the `--reload` switch.

Please see the
[Docker CLI documentation](https://docs.docker.com/engine/reference/commandline/cli/)
for more information on the docker commands.  You can use `docker ps` to list
running containers, `docker image` to list and remove images, `docker stop` to
stop running containers; among other things.

## Testing

Run `make test` before submitting code for review, and especially before merging
to `master`.
