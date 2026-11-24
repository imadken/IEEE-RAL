"""Exactly one frozen native row per OS process; no reset/repair implementation."""

import argparse
import faulthandler
import json
import lzma
import sys
import time

from rpd_isolation_common import BASE, PREFIX, jobs, verify_registration


def main(job_id):
    faulthandler.enable(all_threads=True)
    verify_registration()
    job = next(j for j in jobs() if j.job_id == job_id)
    print("IMPORT_FROZEN_NATIVE_WORKER", job_id, flush=True)
    from rpd_pilot_physics import execute, save_raw

    with lzma.open(job.original_continue_path, "rt") as stream:
        old = json.load(stream)
    n = PREFIX[job.row.parent.task]
    # Only predecision source data enter execute; all later old states stay evaluator-only.
    canonical = {
        "actions": old["actions"][:n],
        "records": old["records"][: n + 1],
        "root_controller_custom": old["root_controller_custom"],
        "source_runtime": old["source_runtime"],
    }
    print("EXECUTE_FROZEN_ROW", job.row.model_dump_json(), flush=True)
    result = execute(job.row, canonical, time.monotonic() + 1200)
    destination = BASE / "physics" / job.row.parent.task / job.job_id
    save_raw(destination / "native.json.xz", result)
    print(
        "FROZEN_ROW_RETURNED",
        result["status"],
        result["macro_end_success"],
        result["deadline_success"],
        flush=True,
    )
    return 0 if result["status"] == "COMPLETE" else 3


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--job-id", required=True)
    sys.exit(main(parser.parse_args().job_id))
