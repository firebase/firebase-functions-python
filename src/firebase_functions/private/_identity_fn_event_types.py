"""
Identity function event types.
"""

# We need to import these from the identity_fn module, but due to circular import
# issues, we need to define them here.
event_type_before_create = "providers/cloud.auth/eventTypes/user.beforeCreate"
event_type_before_sign_in = "providers/cloud.auth/eventTypes/user.beforeSignIn"
event_type_before_email_sent = "providers/cloud.auth/eventTypes/user.beforeSendEmail"
event_type_before_sms_sent = "providers/cloud.auth/eventTypes/user.beforeSendSms"
