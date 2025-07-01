"""Cloud function samples for Firebase Alerts."""

from firebase_functions import alerts_fn
from firebase_functions.alerts import (
    app_distribution_fn,
    billing_fn,
    crashlytics_fn,
    performance_fn,
)


@alerts_fn.on_alert_published(alert_type=alerts_fn.AlertType.BILLING_PLAN_UPDATE)
def onalertpublished(
    alert: alerts_fn.AlertEvent[alerts_fn.FirebaseAlertData[billing_fn.PlanUpdatePayload]],
) -> None:
    print(alert)


@app_distribution_fn.on_in_app_feedback_published()
def appdistributioninappfeedback(alert: app_distribution_fn.InAppFeedbackEvent) -> None:
    print(alert)


@app_distribution_fn.on_new_tester_ios_device_published()
def appdistributionnewrelease(alert: app_distribution_fn.NewTesterDeviceEvent) -> None:
    print(alert)


@billing_fn.on_plan_automated_update_published()
def billingautomatedplanupdate(alert: billing_fn.BillingPlanAutomatedUpdateEvent) -> None:
    print(alert)


@billing_fn.on_plan_update_published()
def billingplanupdate(alert: billing_fn.BillingPlanUpdateEvent) -> None:
    print(alert)


@crashlytics_fn.on_new_fatal_issue_published()
def crashlyticsnewfatalissue(alert: crashlytics_fn.CrashlyticsNewFatalIssueEvent) -> None:
    print(alert)


@crashlytics_fn.on_new_nonfatal_issue_published()
def crashlyticsnewnonfatalissue(alert: crashlytics_fn.CrashlyticsNewNonfatalIssueEvent) -> None:
    print(alert)


@crashlytics_fn.on_new_anr_issue_published()
def crashlyticsnewanrissue(alert: crashlytics_fn.CrashlyticsNewAnrIssueEvent) -> None:
    print(alert)


@crashlytics_fn.on_regression_alert_published()
def crashlyticsregression(alert: crashlytics_fn.CrashlyticsRegressionAlertEvent) -> None:
    print(alert)


@crashlytics_fn.on_stability_digest_published()
def crashlyticsstabilitydigest(alert: crashlytics_fn.CrashlyticsStabilityDigestEvent) -> None:
    print(alert)


@crashlytics_fn.on_velocity_alert_published()
def crashlyticsvelocity(alert: crashlytics_fn.CrashlyticsVelocityAlertEvent) -> None:
    print(alert)


@performance_fn.on_threshold_alert_published()
def performancethreshold(alert: performance_fn.PerformanceThresholdAlertEvent) -> None:
    print(alert)
