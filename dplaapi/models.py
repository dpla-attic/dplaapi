
import os
import peewee
from playhouse.pool import PooledPostgresqlExtDatabase


db_name = os.getenv('POSTGRES_DATABASE')
db_host = os.getenv('POSTGRES_HOST')
db_user = os.getenv('POSTGRES_USER')
db_pw = os.getenv('POSTGRES_PASSWORD')
# See http://docs.peewee-orm.com/en/latest/peewee/playhouse.html#pool-apis
# for the following tuning parameters.
db_max_conn = os.getenv('POSTGRES_MAX_CONN', 20)
db_timeout = os.getenv('POSTGRES_TIMEOUT')
db_stale_timeout = os.getenv('POSTGRES_STALE_TIMEOUT')

db = PooledPostgresqlExtDatabase(
    db_name,
    host=db_host,
    user=db_user,
    password=db_pw,
    max_connections=db_max_conn,
    stale_timeout=db_stale_timeout)


class Account(peewee.Model):
    id = peewee.PrimaryKeyField()
    key = peewee.FixedCharField(max_length=32)
    email = peewee.CharField(max_length=100)
    enabled = peewee.BooleanField()
    staff = peewee.BooleanField()
    created_at = peewee.DateTimeField()
    updated_at = peewee.DateTimeField()

    class Meta:
        database = db
