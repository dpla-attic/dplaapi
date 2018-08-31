FIRST:  Ensure that there is a role named 'dplaapi' that can log in. This is
the application user.  The GRANT statement near the end of the pg_dump file
assumes that this role already exists.

Example:

CREATE USER dplaapi PASSWORD 'devpassword';


