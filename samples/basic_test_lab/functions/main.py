"""Firebase Cloud Functions for Test Lab."""
from firebase_functions.test_lab_fn import (
    CloudEvent,
    TestMatrixCompletedData,
    on_test_matrix_completed,
)


@on_test_matrix_completed()
def testmatrixcompleted(
        event: CloudEvent[TestMatrixCompletedData]) -> None:
    print(f"Test Matrix ID: {event.data.test_matrix_id}")
    print(f"Test Matrix State: {event.data.state}")
    print(f"Test Matrix Outcome Summary: {event.data.outcome_summary}")

    print("Result Storage:")
    print(
        f"  Tool Results History: {event.data.result_storage.tool_results_history}"
    )
    print(f"  Results URI: {event.data.result_storage.results_uri}")
    print(f"  GCS Path: {event.data.result_storage.gcs_path}")
    print(
        f"  Tool Results Execution: {event.data.result_storage.tool_results_execution}"
    )

    print("Client Info:")
    print(f"  Client: {event.data.client_info.client}")
    print(f"  Details: {event.data.client_info.details}")
