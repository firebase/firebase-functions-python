import * as admin from "firebase-admin";
import { getFirestore, DocumentData } from "firebase-admin/firestore";
import { retry } from "../utils";
import { initializeFirebase } from "../firebaseSetup";

describe("Scheduler", () => {
  const projectId = process.env.PROJECT_ID;
  const region = process.env.REGION;
  const testId = process.env.TEST_RUN_ID;

  if (!testId || !projectId || !region) {
    throw new Error("Environment configured incorrectly.");
  }

  beforeAll(() => {
    initializeFirebase();
  });

  afterAll(async () => {
    await getFirestore().collection("schedulerOnScheduleV2Tests").doc(testId).delete();
  });

  describe("onSchedule trigger", () => {
    let loggedContext: DocumentData | undefined;

    beforeAll(async () => {
      const accessToken = await admin.credential.applicationDefault().getAccessToken();
      const jobName = `firebase-schedule-${testId}-v2-schedule-${region}`;
      const response = await fetch(
        `https://cloudscheduler.googleapis.com/v1/projects/${projectId}/locations/us-central1/jobs/firebase-schedule-${testId}-v2-schedule-${region}:run`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${accessToken.access_token}`,
          },
        }
      );
      if (!response.ok) {
        throw new Error(`Failed request with status ${response.status}!`);
      }

      loggedContext = await retry(() =>
        getFirestore()
          .collection("schedulerOnScheduleV2Tests")
          .doc(jobName)
          .get()
          .then((logSnapshot) => logSnapshot.data())
      );
    });

    it("should trigger when the scheduler fires", () => {
      expect(loggedContext?.success).toBeTruthy();
    });
  });
});
