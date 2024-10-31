from firebase_admin import firestore
from firebase_functions.https_fn import (on_call, CallableRequest, on_request,
                                         Request)

from region import REGION


@on_call(invoker="private", region=REGION)
def httpsOnCallV2Tests(request: CallableRequest):
    data = request.data
    firestore.client().collection("httpsOnCallV2Tests").document(
        data["testId"]).set(data)


@on_request(invoker="private", region=REGION)
def httpsOnRequestV2Tests(request: Request):
    data = request.json
    firestore.client().collection("httpsOnRequestV2Tests").document(
        data["testId"]).set(data)
