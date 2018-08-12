# The DPLA API

A web API for querying the
[Digital Public Library of America's](https://dp.la/) metadata.

[![Build Status](https://travis-ci.org/dpla/dplaapi.svg?branch=stable)](https://travis-ci.org/dpla/dplaapi)

## Installation and Execution

### Docker

The Docker installation is going to be the closest thing you can get to
production.

Quick walkthrough

```
$ cd /path/to/dplaapi
$ docker build -t dplaapi:dev .
$ docker run --rm -d -p 8000:8000 --name dplaapi \
  -e ES_BASE=http://elasticsearch-server:9200/dpla_alias dplaapi:dev
$ docker container logs -f dplaapi
```

Make some requests, observe logging, etc.
The application will be available with the following endpoints:

* http://localhost:8000/schema/  (Note trailing slash)
* http://localhost:8000/search?term=search+term
* http://localhost:8000/req-info  (just for testing at the moment)

```
$ docker container stop dplaapi
```

### Native (For development)

See [Development.md](./Development.md)

### Environment Variables

The application recognizes the following environment variables.

* `ES_BASE` (required!):  The base URL of the Elasticsearch index, including the
  path to the index
* `APP_LOG_LEVEL`: The logging level of the `dplaapi` application; as distinct
  from the middleware, e.g. `uvicorn`.  ("debug" | "info" | "warning" |
  "error" | "critical"). Defaults to "debug".
* `DEBUG_SYSINFO`: For development and testing only. Enables the `/sysinfo`
  endpoint if it is defined, e.g. `DEBUG_SYSINFO=1`

Running natively (in development), you can pass the variables like this:
```
$ ES_BASE=http://example:9200/dpla_alias uvicorn dplaapi:app
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
