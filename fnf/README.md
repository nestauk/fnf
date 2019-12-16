## How to setup and use a PostgreSQL DB ##
Install PostgreSQL:
* For macOS users, the fastest way is to download the [Postgres.app](https://postgresapp.com/) and follow the installation instructions. To connect to a database, make sure that the app is running.
* For all other users, you should be able to find a suitable distribution [here](https://www.postgresql.org/download/).

Then, run `python mag_orm.py` to create the project's database (`disinfo`) and its tables.

Note that the `.env` file contains two connections to PostgreSQL in the following format:

``` python
postgresdb = postgres+psycopg2://postgres@localhost/disinfo
test_postgresdb = postgres+psycopg2://postgres@localhost/postgres
```

`disinfo`: the project's database.
`postgres`: default database that is shipped with PostgreSQL and used here for testing the ORMs.
