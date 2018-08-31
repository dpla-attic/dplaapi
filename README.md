# The DPLA API

A web API for querying the
[Digital Public Library of America's](https://dp.la/) metadata.

[![Build Status](https://travis-ci.org/dpla/dplaapi.svg?branch=master)](https://travis-ci.org/dpla/dplaapi) [![Codacy Badge](https://api.codacy.com/project/badge/Grade/a8ed2faf8fdd4ce287e8d964aa3a9320)](https://www.codacy.com/app/dpla/dplaapi?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=dpla/dplaapi&amp;utm_campaign=Badge_Grade) [![Codacy Badge](https://api.codacy.com/project/badge/Coverage/a8ed2faf8fdd4ce287e8d964aa3a9320)](https://www.codacy.com/app/dpla/dplaapi?utm_source=github.com&utm_medium=referral&utm_content=dpla/dplaapi&utm_campaign=Badge_Coverage)

## Installation and Execution

### Docker

The Docker installation is going to be the closest thing you can get to
production.

## Quick walkthrough

```
$ cd /path/to/dplaapi
$ docker-compose up
```

Make some requests, observe logging, etc.
The application will be available with the following endpoints:

* `http://localhost:8000/v2/items`
* `http://localhost:8000/v2/items/<item ID>`

See [the API Codex](https://pro.dp.la/developers/api-codex) for usage.

You can press ctrl-C to stop following the logs, then:
```
$ docker-compose down
```

See [Development.md](./Development.md) for more ways to run the application.

### Environment Variables

The application recognizes the following environment variables.

* `ES_BASE` (required!):  The base URL of the Elasticsearch index, including the
  path to the index
* `APP_LOG_LEVEL`: The logging level of the `dplaapi` application; as distinct
  from the middleware, e.g. `uvicorn`.  ("debug" | "info" | "warning" |
  "error" | "critical"). Defaults to "debug".

Running natively (in development), you can pass the variables like this:
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

## TODO / FIXME

* Change the Travis CI "Build Status" link when we have a `stable` branch.
