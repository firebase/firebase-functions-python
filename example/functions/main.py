"""
Example Firebase Functions written in Python
"""
from firebase_functions import db, options

options.set_global_options(
    region=options.SupportedRegion.EUROPE_WEST1,
    memory=options.MemoryOption.MB_256,
)


@db.on_value_written(
    reference="hello",
    region=options.SupportedRegion.EUROPE_WEST1,
)
def on_write_example(event: db.DatabaseEvent[db.Change[object]]) -> None:
    print("Hello from db write event:", event)


@db.on_value_created(reference="hello/{any_thing_here}/bar")
def on_created_example(event: db.DatabaseEvent[object]) -> None:
    print("Hello from db create event:", event)


@db.on_value_deleted(reference="hello/{any_thing_here}/bar")
def on_deleted_example(event: db.DatabaseEvent[object]) -> None:
    print("Hello from db delete event:", event)


@db.on_value_updated(reference="hello")
def on_updated_example(event: db.DatabaseEvent[db.Change[object]]) -> None:
    print("Hello from db updated event:", event)
