# Operations Manual

## Pipeline Execution
1. Ensure the virtual environment is active.
2. Run `python main.py` for a full end-to-end test.
3. For production, deploy the DAG in `dags/dag.py` to an Airflow environment.

## Backfilling
To re-process a specific date:
```bash
# Example Airflow command simulation
airflow dags backfill banking_mission_critical_pipeline \
    --start-date 2023-12-01 --end-date 2023-12-01
```
The pipeline uses `overwrite` mode on partitions, ensuring that re-running the same date replaces existing data without duplicates (Idempotency).

## Troubleshooting
- **Logs**: Located in the `logs/` directory.
- **Quality Failures**: Inspect `logs/quality.log` for details on which Great Expectations rule failed.
- **SLA Alerts**: Defined in `config/pipeline_config.yaml`.
