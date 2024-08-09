import admin from "firebase-admin";
import { retry, startTestRun, timeout } from "../utils";
import { initializeFirebase } from "../firebaseSetup";

describe("TestLab (v2)", () => {
  const projectId = process.env.PROJECT_ID;
  const testId = process.env.TEST_RUN_ID;

  if (!testId || !projectId) {
    throw new Error("Environment configured incorrectly.");
  }

  beforeAll(async () => {
    await initializeFirebase();
    await timeout(120_000);
  }, 200_000);

  afterAll(async () => {
    await admin
      .firestore()
      .collection("testLabOnTestMatrixCompletedTests")
      .doc(testId)
      .delete();
  });

  describe("test matrix onComplete trigger", () => {
    let loggedContext: admin.firestore.DocumentData | undefined;

    beforeAll(async () => {
      const accessToken = await admin.credential
        .applicationDefault()
        .getAccessToken();
      await startTestRun(projectId, testId, accessToken.access_token);

      loggedContext = await retry(async () => {
        const logSnapshot = await admin
          .firestore()
          .collection("testLabOnTestMatrixCompletedTests")
          .doc(testId)
          .get();
        return logSnapshot.data();
      });

      if (!loggedContext) {
        throw new Error("loggedContext is undefined");
      }
    });

    it("should have event id", () => {
      expect(loggedContext?.id).toBeDefined();
    });

    it("should have right event type", () => {
      expect(loggedContext?.type).toEqual(
        "google.firebase.testlab.testMatrix.v1.completed",
      );
    });

    it("should be in state 'INVALID'", () => {
      expect(loggedContext?.state).toEqual("INVALID");
    });
  });
});
