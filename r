%yaml
command:
  - gunicorn
  - --worker-class
  - gevent
  - --workers
  - '4'
  - --timeout
  - '300'
  - gallery_generator.app:application
env:
  - name: DATABRICKS_INSTANCE
    value: 'https://dbc-2224ee74-4555.cloud.databricks.com/'
  - name: DATABRICKS_TOKEN
    value: 6418da0b22d'
  - name: DATABRICKS_CATALOG
    value: 'workspace'
  - name: DATABRICKS_SCHEMA
    value: 'default'
  - name: DATABRICKS_VOLUME
    value: 'gallery_data'
