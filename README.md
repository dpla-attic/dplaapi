# The DPLA API

A web API for querying the
[Digital Public Library of America's](https://dp.la/) metadata.

[![Build Status](https://travis-ci.org/dpla/dplaapi.svg?branch=master)](https://travis-ci.org/dpla/dplaapi) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/a8ed2faf8fdd4ce287e8d964aa3a9320)](https://www.codacy.com/app/dpla/dplaapi?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=dpla/dplaapi&amp;utm_campaign=Badge_Grade) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/a8ed2faf8fdd4ce287e8d964aa3a9320)](https://www.codacy.com/app/dpla/dplaapi?utm_source=github.com&utm_medium=referral&utm_content=dpla/dplaapi&utm_campaign=Badge_Coverage)

## Installation and Execution

### Docker

The Docker installation is going to be the closest thing you can get to
production.

## Quick walkthrough

If you already have a Docker image named `dplaapi_dplaapi:latest`, then remove
that image with `docker image rm`. If you have never run `docker-compose`
before, then this won't concern you.

Moving along:
```
$ cd /path/to/dplaapi
$ docker-compose up
```

Make some requests, observe logging, etc.
The application will be available with the following endpoints:

* `http://localhost:8000/v2/items`
* `http://localhost:8000/v2/items/<item ID or IDs>`
* `http://localhost:8000/v2/items/<item ID or IDs>/mlt`

See [the API Codex](https://pro.dp.la/developers/api-codex) for usage.

The PostgreSQL database Docker container that is included in that setup contains
a user account for testing. Its API key is `08e3918eeb8bf4469924f062072459a8`.

You can press ctrl-C to stop following the logs, then:
```
$ docker-compose down
```

See [Development.md](./Development.md) for more ways to run the application.

### Environment Variables

The application recognizes the following environment variables.

* `ES_BASE` (required!):  The base URL of the main Elasticsearch index, including
  the path to the index.
* `NECRO_BASE` (required!):  The base URL of the Elasticsearch index that holds
  tombstones for items no longer in DPLA under their old ids.  Include the
  path to the index.
* `APP_LOG_LEVEL`: The logging level of the `dplaapi` application; as distinct
  from the middleware, e.g. `uvicorn`.  ("debug" | "info" | "warning" |
  "error" | "critical"). Defaults to "debug".
* `DISABLE_AUTH`: If this is defined, then checking of API keys will be disabled.
You will also be able to get by without PostgreSQL, because the database won't
be used.
* `EMAIL_FROM`: Email "From:" address for sending API key emails.
* `POSTGRES_DATABASE`: The database name
* `POSTGRES_HOST`: The database hostname.  For example, 'localhost'.
* `POSTGRES_PASSWORD`: The database password.
* `GA_TID`: Google Analytics property ID. If undefined, then no tracking will
happen.

The following environment variables may be defined, but are optional and have
defaults.  See
[the Peewee ORM documentation](http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#pool-apis).

* `POSTGRES_MAX_CONN`
* `POSTGRES_TIMEOUT`
* `POSTGRES_STALE_TIMEOUT`

Additionally, there are some environment variables that may be necessary in
order to configure Amazon SES (Simple Email Service).  SES is used for sending
out API key notifications. This is not necessary for development or
demonstration usage, since you are provided with a test account, as indicated
above. The production application could actually be deployed with
IAM EC2 instance profiles, which obviate the need for these variables. Whatever
the case, these standard variables are:

* `AWS_ACCESS_KEY_ID`
* `AWS_SECRET_ACCESS_KEY`

Running natively (in development), you can pass environment variables like this:
```
$ PYTHONPATH=. ES_BASE=http://example:9200/dpla_alias gunicorn \
  -k uvicorn.workers.UvicornWorker dplaapi:app
```
... Or you could `export` the variables in your shell so that you don't have to
specify them for every run.

Running in Docker, the variables should be passed with `docker`'s `-e`
option; for example, `-e ES_BASE=http://example:9200/dpla_alias -e
APP_LOG_LEVEL=info`.

## Development

See [Development.md](./Development.md)

## License

See [LICENSE](./LICENSE)
