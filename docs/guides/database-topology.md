# Database topology and configuration contract

This guide is the current contract for the data stores of Diamant ID. It
describes the supported local MariaDB layout and the agreed target layout for a
future PostgreSQL/staging runtime. It is not a runbook for provisioning cloud
infrastructure and does not authorize a data migration.

## One logical model, two physical layouts

The ORM names three logical schemas explicitly. Their names and ownership do
not change between environments.

| Logical schema | Local MariaDB / XAMPP | Future PostgreSQL / cloud | Current ownership |
| --- | --- | --- | --- |
| `diamond_oltp` | one physical database | schema in one physical database | accounts, reports, lifecycle, media metadata, demo datasets and demo SOM artifacts |
| `diamond_market` | one physical database | schema in the same physical database | provider catalogue, terms/policies, snapshots, quotes, FX and operations |
| `diamond_analytics` | one physical database | schema in the same physical database | reserved `ml_results`; no active ML API or storage flow |

```mermaid
flowchart LR
  subgraph L[Local development: one MariaDB server]
    LO[(diamond_oltp)]
    LM[(diamond_market)]
    LA[(diamond_analytics)]
  end
  subgraph P[Future staging/cloud: one PostgreSQL database]
    PO[diamond_oltp schema]
    PM[diamond_market schema]
    PA[diamond_analytics schema]
  end
  LO --> PO
  LM --> PM
  LA --> PA
```

`public` is not a substitute for these schemas. Moving all tables to `public`,
renaming a logical schema, or splitting the future PostgreSQL schemas into
separate databases requires a separate ADR and migration plan.

## Connection variables and `DB_NAME`

The application accepts one of two connection forms:

1. `DATABASE_URL` has priority and is the required form for future PostgreSQL.
2. Local MariaDB can be assembled from `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
   `DB_PORT` and `DB_NAME`.

`DB_NAME` remains a compatibility variable. Its local value must stay
`diamond_oltp`, because a MariaDB URL needs a default database. It does **not**
limit the app to OLTP: every ORM table has an explicit logical schema, so the
same DB user must have the required rights on all three local databases.

```dotenv
# Local MariaDB default only; all three databases still need DB_USER grants.
DB_NAME=diamond_oltp

# Future PostgreSQL example is intentionally not enabled in .env.example.
# DATABASE_URL=postgresql+psycopg://app_runtime:...@host:5432/diamant_id
```

The committed `.env.example` contains no usable credentials. Never copy a
private `DATABASE_URL`, password, backup manifest, or provider secret to a
guide, test fixture, or Git history.

## Ownership boundaries

Demo SOM is operational demo data, not a completed ML system:

- `demo_som_artifacts` and `demo_som_assignments` belong to
  `diamond_oltp` alongside their demo dataset and reports;
- `diamond_analytics.ml_results` is deliberately reserved and may remain
  empty; it is not a fallback container for demo SOM, provider snapshots, or
  unapproved real-data analytics;
- `diamond_market` holds provider provenance/policy and immutable snapshots,
  but a provider value is not automatically licensed training data.

This keeps the demo mechanism compatible with a future authorized real-data
adapter without mixing synthetic, operational, provider, and model artifacts.

## Local MariaDB lifecycle

`scripts/bootstrap_mariadb_databases.py` creates only missing databases in the
canonical order `diamond_oltp`, `diamond_market`, `diamond_analytics`.
`alembic upgrade head` then owns table structure and keeps its version table in
`diamond_oltp`. Bootstrap and upgrade are different operations; upgrade needs a
backup and explicit user approval.

`scripts/seed_db.py` is destructive: it drops and recreates all three local
databases before running Alembic. It is only for disposable local data and is
never a repair, migration, or test fixture.

Logical backups and restore verification must cover all three MariaDB databases
together. A backup of only `diamond_oltp` is incomplete because the runtime has
cross-schema references and depends on market records. The recovery and
historical-synthetic guides contain the safe local backup/restore procedure.

## Least-privilege roles

The exact account names, authentication method, host restrictions, and managed
service syntax are deployment-specific. The role separation below is the
required contract rather than a command to execute on a current server.

| Role | Local MariaDB rights | Future PostgreSQL rights |
| --- | --- | --- |
| bootstrap owner | create the three empty databases only | create the one database and three schemas before the first migration |
| migration owner | DDL and migration metadata in all three databases | `CREATE`/`USAGE` and ownership in all three schemas; owns Alembic version metadata |
| runtime app user | only required `SELECT`, `INSERT`, `UPDATE`, `DELETE` on application tables in all three databases; no `DROP`/`CREATE DATABASE` | `USAGE` on all three schemas, table DML and sequence usage only; no schema ownership or DDL |
| backup/restore operator | logical dump/restore rights for all three databases | managed-backup/restore rights defined by the selected provider; never use the runtime account |

Seed is deliberately not assigned to the runtime role. Provider credentials and
environment secrets are separate from database grants.

## Mandatory input to task 161

Task 161 starts only with a disposable PostgreSQL instance and this order:

1. Create one empty PostgreSQL database and the three named schemas; establish
   migration-owner and runtime roles before application deployment.
2. Use one explicit PostgreSQL `DATABASE_URL`; do not retain MariaDB `DB_*`
   settings as hidden production fallbacks.
3. Generate and review Alembic SQL, then run migrations with the migration
   owner. Verify that the Alembic version table is in `diamond_oltp`.
4. Test cross-schema foreign keys, `DECIMAL`, timestamps, indexes, constraints,
   identifiers and sequence/autoincrement behavior on disposable data.
5. Import only approved source data with recorded row counts, checksums and
   referential-integrity checks for every logical schema.
6. Perform application/API smoke tests with the restricted runtime role, then
   test backup plus restore into a separate disposable database.

Rollback is an environment-level operation: stop writes, retain the failed
environment for diagnosis, restore the verified backup to a separate target,
compare counts/integrity, and switch only after approval. Alembic downgrade is
not a substitute for restoring imported data.

## Read-only repository check

Run the following command after changing ORM schema ownership, `.env.example`,
or topology configuration:

```powershell
.\.venv\Scripts\python.exe scripts\check_database_topology.py
```

It neither loads private `.env` values nor connects to MariaDB/PostgreSQL. It
only checks the committed configuration and model ownership; it cannot validate
a future PostgreSQL server.

Related documents: [database guide](./database-guide.md),
[schema map](../db-schema.md), [local start](../local-start.md),
[MariaDB recovery](./mariadb-local-recovery.md), and [task 161](../backlog/161-postgresql-migration-and-staging.md).
