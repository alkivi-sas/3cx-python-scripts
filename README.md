# 3cx-python-scripts

Some scripts in python for 3CX

## Requirements

You need postgresql-server-dev-X.Y installed on the server
You also need python3-dev.
If using Debian based system :

```bash
PSQL_VERION='9.6'
apt-get install postgresql-server-dev-${PSQL_VERION} python3-dev
```

You also need to create a PostgreSQL Role to be able to write to the specific database.
As the postgres user on the server :

```bash
psql
CREATE ROLE freshdesk_to_3cx NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT LOGIN PASSWORD 'password' VALID UNTIL 'infinity';
GRANT CONNECT ON DATABASE database_single TO freshdesk_to_3cx;
exit

psql database_single
GRANT USAGE ON SCHEMA public TO freshdesk_to_3cx;
GRANT ALL ON public.extdevice TO freshdesk_to_3cx;
```

## Installation

The easiest way to install is inside a virtualenv

1. Create the virtualenv (Python 3!) and activate it:

```bash
git clone https://github.com/alkivi-sas/3cx-python-scripts
cd 3cx-python-scripts
pipenv install
```

2. Change the conf file :

```bash
cp .config-example .config
vim .config
```

## Usage
1. From a terminal :

```bash
pipenv shell
./scripts.py
```
