"""Firebase Cloud Functions for blocking auth functions example."""
from firebase_functions import identity_fn


@identity_fn.before_user_created(
    id_token=True,
    access_token=True,
    refresh_token=True,
)
def beforeusercreated(
    event: identity_fn.AuthBlockingEvent
) -> identity_fn.BeforeCreateResponse | None:
    print(event)
    if not event.data.email:
        return None
    if "@cats.com" in event.data.email:
        return identity_fn.BeforeCreateResponse(
            display_name="🐈",
            custom_claims={"meow": True},
        )
    if "@dogs.com" in event.data.email:
        return identity_fn.BeforeCreateResponse(
            display_name="🐕",
            custom_claims={"woof": True},
        )
    return None


@identity_fn.before_user_signed_in(
    id_token=True,
    access_token=True,
    refresh_token=True,
)
def beforeusersignedin(
    event: identity_fn.AuthBlockingEvent
) -> identity_fn.BeforeSignInResponse | None:
    print(event)
    if not event.data.email:
        return None

    if "@cats.com" in event.data.email:
        return {
            "display_name": "🐈",
            "session_claims": {
                "session_meow": True
            },
        }

    if "@dogs.com" in event.data.email:
        return {
            "display_name": "🐕",
            "session_claims": {
                "session_woof": True
            },
        }

    return None
