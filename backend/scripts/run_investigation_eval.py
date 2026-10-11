import argparse
import json

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]

if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(BACKEND_ROOT),
    )


from app.evals.evaluator import (
    evaluate_investigation,
)

from app.evals.repository import (
    create_eval_run,
    finish_eval_run,
    save_eval_result,
)

from app.investigations.repository import (
    get_investigation_by_id,
)


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Run deterministic evaluation "
            "against a saved AegisOps investigation."
        )
    )

    parser.add_argument(
        "investigation_id",
        type=int,
    )

    parser.add_argument(
        "--suite",
        default="manual-investigation-eval",
    )

    args = parser.parse_args()


    investigation = (
        get_investigation_by_id(
            args.investigation_id
        )
    )

    if investigation is None:
        raise SystemExit(
            (
                "Investigation "
                f"{args.investigation_id} "
                "was not found."
            )
        )


    eval_run_id = create_eval_run(
        suite_name=args.suite,
        total_cases=1,
        metadata={
            "investigation_id":
                args.investigation_id,

            "model":
                investigation["model"],
        },
    )


    try:
        result = evaluate_investigation(
            investigation
        )

        eval_result_id = (
            save_eval_result(
                eval_run_id=eval_run_id,
                result=result,
            )
        )

        finish_eval_run(
            eval_run_id=eval_run_id,
            passed_cases=(
                1
                if result["passed"]
                else 0
            ),
            failed_cases=(
                0
                if result["passed"]
                else 1
            ),
        )

    except Exception:
        finish_eval_run(
            eval_run_id=eval_run_id,
            passed_cases=0,
            failed_cases=1,
            status="FAILED",
        )

        raise


    output = {
        "eval_run_id":
            eval_run_id,

        "eval_result_id":
            eval_result_id,

        **result,
    }


    print(
        json.dumps(
            output,
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    main()