"""
Example Firebase Functions for RTDB written in Python
"""
from firebase_functions import db_fn, options
from firebase_admin import initialize_app

initialize_app()

options.set_global_options(region=options.SupportedRegion.EUROPE_WEST1)


@db_fn.on_value_written(reference="hello/world")
def onwriteexample(event: db_fn.Event[db_fn.Change]) -> None:
    print("Hello from db write event:", event)
    print("Reference path:", event.reference.path)


@db_fn.on_value_created(reference="hello/world")
def oncreatedexample(event: db_fn.Event) -> None:
    print("Hello from db create event:", event)
    print("Reference path:", event.reference.path)


@db_fn.on_value_deleted(reference="hello/world")
def ondeletedexample(event: db_fn.Event) -> None:
    print("Hello from db delete event:", event)
    print("Reference path:", event.reference.path)


@db_fn.on_value_updated(reference="hello/world")
def onupdatedexample(event: db_fn.Event[db_fn.Change]) -> None:
    print("Hello from db updated event:", event)
    print("Reference path:", event.reference.path)
