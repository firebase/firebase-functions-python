from firebase_admin import initialize_app
from v2.database_tests import *
from v2.eventarc_tests import *
from v2.firestore_tests import *
from v2.https_tests import *
from v2.identity_tests import *
from v2.pubsub_tests import *
from v2.remote_config_tests import *
from v2.scheduler_tests import *
from v2.storage_tests import *
from v2.tasks_tests import *
from v2.test_lab_tests import *

initialize_app()
