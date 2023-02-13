"""
Example Firebase Functions for RTDB written in Python
"""
from firebase_functions import db_fn
from firebase_admin import initialize_app

initialize_app()


@db_fn.on_value_written(reference="hello")
def onwriteexample(event: db_fn.Event[db_fn.Change[object]]) -> None:
    print("Hello from db write event:", event)


@db_fn.on_value_created(reference="hello/{foo}/bar")
def oncreatedexample(event: db_fn.Event[object]) -> None:
    print(event.params["foo"])
    print("Hello from db create event:", event)


@db_fn.on_value_deleted(reference="hello/{foo}/bar")
def ondeletedexample(event: db_fn.Event[object]) -> None:
    print(event.params["foo"])
    print("Hello from db delete event:", event)


@db_fn.on_value_updated(reference="hello")
def onupdatedexample(event: db_fn.Event[db_fn.Change[object]]) -> None:
    print("Hello from db updated event:", event)
