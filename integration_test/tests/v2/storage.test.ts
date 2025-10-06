import { getFirestore, DocumentData } from "firebase-admin/firestore";
import { getStorage } from "firebase-admin/storage";
import { initializeFirebase } from "../firebaseSetup";
import { retry, timeout } from "../utils";

async function uploadBufferToFirebase(buffer: Buffer, fileName: string) {
  const bucket = getStorage().bucket();

  const file = bucket.file(fileName);
  await file.save(buffer, {
    metadata: {
      contentType: "text/plain",
    },
  });
}

describe("Firebase Storage (v2)", () => {
  const testId = process.env.TEST_RUN_ID;

  if (!testId) {
    throw new Error("Environment configured incorrectly.");
  }

  beforeAll(() => {
    initializeFirebase();
  });

  afterAll(async () => {
    await getFirestore().collection("storageOnObjectFinalizedTests").doc(testId).delete();
    await getFirestore().collection("storageOnObjectDeletedTests").doc(testId).delete();
    await getFirestore().collection("storageOnObjectMetadataUpdatedTests").doc(testId).delete();
  });

  describe("onObjectFinalized trigger", () => {
    let loggedContext: DocumentData | undefined;

    beforeAll(async () => {
      const testContent = testId;
      const buffer = Buffer.from(testContent, "utf-8");

      await uploadBufferToFirebase(buffer, testId + ".txt");

      loggedContext = await retry(() =>
        getFirestore()
          .collection("storageOnObjectFinalizedTests")
          .doc(testId)
          .get()
          .then((logSnapshot) => logSnapshot.data())
      );
    });

    afterAll(async () => {
      const file = getStorage()
        .bucket()
        .file(testId + ".txt");

      const [exists] = await file.exists();
      if (exists) {
        await file.delete();
      }
    });

    it("should have the right event type", () => {
      expect(loggedContext?.type).toEqual("google.cloud.storage.object.v1.finalized");
    });

    it("should have event id", () => {
      expect(loggedContext?.id).toBeDefined();
    });

    it("should have time", () => {
      expect(loggedContext?.time).toBeDefined();
    });
  });

  describe("onDeleted trigger", () => {
    let loggedContext: DocumentData | undefined;

    beforeAll(async () => {
      const testContent = testId;
      const buffer = Buffer.from(testContent, "utf-8");

      await uploadBufferToFirebase(buffer, testId + ".txt");

      await timeout(5000); // Short delay before delete

      const file = getStorage()
        .bucket()
        .file(testId + ".txt");
      await file.delete();

      loggedContext = await retry(() =>
        getFirestore()
          .collection("storageOnObjectDeletedTests")
          .doc(testId)
          .get()
          .then((logSnapshot) => logSnapshot.data())
      );
    });

    it("should have the right event type", () => {
      expect(loggedContext?.type).toEqual("google.cloud.storage.object.v1.deleted");
    });

    it("should have event id", () => {
      expect(loggedContext?.id).toBeDefined();
    });

    it("should have time", () => {
      expect(loggedContext?.time).toBeDefined();
    });
  });

  describe("onMetadataUpdated trigger", () => {
    let loggedContext: DocumentData | undefined;

    beforeAll(async () => {
      const testContent = testId;
      const buffer = Buffer.from(testContent, "utf-8");

      await uploadBufferToFirebase(buffer, testId + ".txt");

      // Trigger metadata update
      const file = getStorage()
        .bucket()
        .file(testId + ".txt");
      await file.setMetadata({ contentType: "application/json" });

      loggedContext = await retry(() =>
        getFirestore()
          .collection("storageOnObjectMetadataUpdatedTests")
          .doc(testId)
          .get()
          .then((logSnapshot) => logSnapshot.data())
      );
    });

    afterAll(async () => {
      const file = getStorage()
        .bucket()
        .file(testId + ".txt");

      const [exists] = await file.exists();
      if (exists) {
        await file.delete();
      }
    });

    it("should have the right event type", () => {
      expect(loggedContext?.type).toEqual("google.cloud.storage.object.v1.metadataUpdated");
    });

    it("should have event id", () => {
      expect(loggedContext?.id).toBeDefined();
    });

    it("should have time", () => {
      expect(loggedContext?.time).toBeDefined();
    });
  });
});
