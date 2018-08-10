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
$ docker build -t dplaapi:latest .
$ docker run --rm -d -p 8000:8000 --name dplaapi dplaapi:dev
$ docker container logs -f dplaapi
```

Make some requests, observe logging, etc.
The application will be available with the following endpoints:

* http://localhost:8000/schema
* http://localhost:8000/search?term=search+term
* http://localhost:8000/req-info  (just for testing at the moment)

```
$ docker container stop dplaapi
```

### Native (For development)

See [Development.md](./Development.md)

## Development

See [Development.md](./Development.md)

## License

See [LICENSE](./LICENSE)
