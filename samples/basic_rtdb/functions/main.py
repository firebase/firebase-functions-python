"""Basic RTDB triggers example."""

from firebase_functions import options, db
from firebase_admin import initialize_app

initialize_app()


@db.on_value_written(
    reference="hello",
    region=options.SupportedRegion.EUROPE_WEST1,
)
def on_write_example(event: db.DatabaseEvent[db.Change[object]]) -> None:
    """
    This function will be triggered when a value is written to the database.
    """
    print("Hello from db write event:", event)
