"""
Example Function params & inputs.
"""

from firebase_admin import initialize_app

from firebase_functions import params, storage_fn

initialize_app()

bucket = params.StringParam(
    "BUCKET",
    label="storage bucket",
    description="The bucket to resize images from.",
    input=params.ResourceInput(type=params.ResourceType.STORAGE_BUCKET),
    default=params.STORAGE_BUCKET,
)

output_path = params.StringParam(
    "OUTPUT_PATH",
    label="storage bucket output path",
    description="The path of in the bucket where processed images will be stored.",
    input=params.TextInput(
        example="/images/processed",
        validation_regex=r"^\/.*$",
        validation_error_message="Must be a valid path starting with a forward slash",
    ),
    default="/images/processed",
)

image_type = params.ListParam(
    "IMAGE_TYPE",
    label="convert image to preferred types",
    description="The image types you'd like your source image to convert to.",
    input=params.MultiSelectInput(
        [
            params.SelectOption(value="jpeg", label="jpeg"),
            params.SelectOption(value="png", label="png"),
            params.SelectOption(value="webp", label="webp"),
        ]
    ),
    default=["jpeg", "png"],
)

delete_original = params.BoolParam(
    "DELETE_ORIGINAL_FILE",
    label="delete the original file",
    description="Do you want to automatically delete the original file from the Cloud Storage?",
    input=params.SelectInput(
        [
            params.SelectOption(value=True, label="Delete on any resize attempt"),
            params.SelectOption(value=False, label="Don't delete"),
        ],
    ),
    default=True,
)

image_resize_api_secret = params.SecretParam(
    "IMAGE_RESIZE_API_SECRET",
    label="image resize api secret",
    description="The fake secret key to use for the image resize API.",
)


@storage_fn.on_object_finalized(
    bucket=bucket,
    secrets=[image_resize_api_secret],
)
def resize_images(event: storage_fn.CloudEvent[storage_fn.StorageObjectData]):
    """
    This function will be triggered when a new object is created in the bucket.
    """
    print("Got a new image:", event)
    print("Selected image types:", image_type.value)
    print("Selected bucket resource:", bucket.value)
    print("Selected output location:", output_path.value)
    print("Testing a not so secret api key:", image_resize_api_secret.value)
    print("Should original images be deleted?:", delete_original.value)
    # TODO: Implement your image resize logic
