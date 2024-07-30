import { execSync } from "child_process";
import fs from "fs";
import path from "path";

const DIR = process.cwd();

/**
 * Build SDK, and Functions
 */
export default function setup(testRunId: string, firebaseAdmin: string) {
  buildSdk(testRunId);
  createRequirementsTxt(testRunId, firebaseAdmin);
  installDependencies();
}

function buildSdk(testRunId: string) {
  console.log("Building SDK...");
  process.chdir(path.join(DIR, "..")); // go up to root

  // remove existing build
  fs.rmSync("dist", { recursive: true, force: true });
  // remove existing venv
  fs.rmSync("venv", { recursive: true, force: true });

  // make virtual environment for building
  execSync("python3 -m venv venv", { stdio: "inherit" });

  // build the package
  execSync(
    "source venv/bin/activate && python -m pip install --upgrade build",
    { stdio: "inherit" },
  );
  execSync("source venv/bin/activate && python -m build -s", {
    stdio: "inherit",
  });

  // move the generated tarball package to functions
  const generatedFile = fs
    .readdirSync("dist")
    .find((file) => file.match(/^firebase_functions-.*\.tar\.gz$/));

  if (generatedFile) {
    const targetPath = path.join(
      "integration_tests",
      "functions",
      `firebase_functions.tar.gz`,
    );
    fs.renameSync(path.join("dist", generatedFile), targetPath);
    console.log("SDK moved to", targetPath);
  }

  process.chdir(DIR); // go back to integration_test
}

function createRequirementsTxt(testRunId: string, firebaseAdmin: string) {
  console.log("Creating package.json...");
  const requirementsTemplatePath = `${DIR}/requirements.txt.template`;
  const requirementsPath = `${DIR}/functions/requirements.txt`;

  fs.copyFileSync(requirementsTemplatePath, requirementsPath);

  let requirementsContent = fs.readFileSync(requirementsPath, "utf8");
  requirementsContent = requirementsContent.replace(
    /__LOCAL_FIREBASE_FUNCTIONS__/g,
    `firebase_functions.tar.gz`,
  );
  requirementsContent = requirementsContent.replace(
    /__FIREBASE_ADMIN__/g,
    firebaseAdmin,
  );

  fs.writeFileSync(requirementsPath, requirementsContent);
}

function installDependencies() {
  console.log("Installing dependencies...");
  const functionsDir = "functions";
  process.chdir(functionsDir); // go to functions

  const venvPath = path.join("venv");
  if (fs.existsSync(venvPath)) {
    execSync(`rm -rf ${venvPath}`, { stdio: "inherit" });
  }

  execSync("python3 -m venv venv", { stdio: "inherit" });
  execSync("source venv/bin/activate && python3 -m pip install -r requirements.txt", { stdio: "inherit" });
  process.chdir("../"); // go back to integration_test
}
