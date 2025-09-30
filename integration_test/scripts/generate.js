#!/usr/bin/env node

/**
 * Python Function Generator Script
 * Generates Python Firebase Functions from YAML configuration using templates
 */

import Handlebars from "handlebars";
import { readFileSync, writeFileSync, mkdirSync, existsSync, copyFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";
import { getSuiteConfig, getSuitesByPattern, listAvailableSuites } from "./config-loader.js";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const ROOT_DIR = dirname(__dirname);

// Register Handlebars helpers
Handlebars.registerHelper("eq", (a, b) => a === b);
Handlebars.registerHelper("or", (a, b) => a || b);
Handlebars.registerHelper("unless", function (conditional, options) {
  if (!conditional) {
    return options.fn(this);
  }
  return options.inverse(this);
});

// Python-specific trigger name mapping
const pythonTriggerMap = {
  "onCreate": "created",
  "onDelete": "deleted",
  "onUpdate": "updated",
  "onWrite": "written"
};

Handlebars.registerHelper("pythonTrigger", function(trigger) {
  return pythonTriggerMap[trigger] || trigger.replace(/^on/, "").toLowerCase();
});

/**
 * Generate Python Firebase Functions from templates
 * @param {string[]} suitePatterns - Array of suite names or patterns
 * @param {Object} options - Generation options
 * @param {string} [options.testRunId] - Test run ID to use
 * @param {string} [options.configPath] - Path to config file
 * @param {string} [options.projectId] - Override project ID
 * @param {string} [options.region] - Override region
 * @param {string} [options.sdkPackage] - Path to SDK package (wheel)
 * @param {boolean} [options.quiet] - Suppress console output
 * @returns {Promise<Object>} - Metadata about generated functions
 */
export async function generateFunctions(suitePatterns, options = {}) {
  const {
    testRunId = `t${Math.random().toString(36).substring(2, 10)}`,
    configPath: initialConfigPath = null,
    projectId: overrideProjectId = process.env.PROJECT_ID,
    region: overrideRegion = process.env.REGION,
    sdkPackage = process.env.SDK_PACKAGE || "file:firebase-functions-python-local.whl",
    quiet = false
  } = options;

  const log = quiet ? () => {} : console.log.bind(console);
  const error = quiet ? () => {} : console.error.bind(console);

  log(`🚀 Generating Python functions: ${suitePatterns.join(", ")}`);
  log(`   TEST_RUN_ID: ${testRunId}`);

  // Load suite configurations
  const suites = [];
  let projectId, region;
  let configPath = initialConfigPath;

  for (const pattern of suitePatterns) {
    try {
      let suitesToAdd = [];

      // Check if it's a pattern (contains * or ?)
      if (pattern.includes("*") || pattern.includes("?")) {
        // Use unified config file (Python only supports 2nd gen)
        if (!configPath) {
          configPath = join(ROOT_DIR, "config", "suites.yaml");
        }
        suitesToAdd = getSuitesByPattern(pattern, configPath);
      } else {
        // Single suite name
        if (!configPath) {
          // Use unified config file (Python only supports 2nd gen)
          configPath = join(ROOT_DIR, "config", "suites.yaml");
        }
        suitesToAdd = [getSuiteConfig(pattern, configPath)];
      }

      // Add suites and extract project/region from first suite
      for (const suite of suitesToAdd) {
        if (!projectId) {
          projectId = suite.projectId || overrideProjectId || "demo-test";
          region = suite.region || overrideRegion || "us-central1";
        }
        suites.push(suite);
      }

      // Reset configPath for next pattern (allows mixing v1 and v2)
      if (!initialConfigPath) {
        configPath = null;
      }
    } catch (err) {
      error(`❌ Error loading suite(s) '${pattern}': ${err.message}`);
      throw err;
    }
  }

  if (suites.length === 0) {
    throw new Error("No suites found to generate");
  }

  log(`   PROJECT_ID: ${projectId}`);
  log(`   REGION: ${region}`);
  log(`   Loaded ${suites.length} suite(s)`);

  // Helper function to generate from template
  function generateFromTemplate(templatePath, outputPath, context) {
    const fullTemplatePath = join(ROOT_DIR, "templates", templatePath);

    if (!existsSync(fullTemplatePath)) {
      error(`❌ Template not found: ${fullTemplatePath}`);
      return false;
    }

    const templateContent = readFileSync(fullTemplatePath, "utf8");
    const template = Handlebars.compile(templateContent);
    const output = template(context);

    const outputFullPath = join(ROOT_DIR, "generated", outputPath);
    mkdirSync(dirname(outputFullPath), { recursive: true });
    writeFileSync(outputFullPath, output);
    log(`   ✅ Generated: ${outputPath}`);
    return true;
  }

  // Template mapping for service types and versions
  const templateMap = {
    firestore: {
      v1: "functions/src/v1/firestore_tests.py.hbs",
      v2: "functions/src/v2/firestore_tests.py.hbs",
    },
    database: {
      v1: "functions/src/v1/database_tests.py.hbs",
      v2: "functions/src/v2/database_tests.py.hbs",
    },
    pubsub: {
      v1: "functions/src/v1/pubsub_tests.py.hbs",
      v2: "functions/src/v2/pubsub_tests.py.hbs",
    },
    storage: {
      v1: "functions/src/v1/storage_tests.py.hbs",
      v2: "functions/src/v2/storage_tests.py.hbs",
    },
    auth: {
      v1: "functions/src/v1/auth_tests.py.hbs",
      v2: "functions/src/v2/auth_tests.py.hbs",
    },
    tasks: {
      v1: "functions/src/v1/tasks_tests.py.hbs",
      v2: "functions/src/v2/tasks_tests.py.hbs",
    },
    remoteconfig: {
      v1: "functions/src/v1/remoteconfig_tests.py.hbs",
      v2: "functions/src/v2/remoteconfig_tests.py.hbs",
    },
    testlab: {
      v1: "functions/src/v1/testlab_tests.py.hbs",
      v2: "functions/src/v2/testlab_tests.py.hbs",
    },
    scheduler: {
      v2: "functions/src/v2/scheduler_tests.py.hbs",
    },
    identity: {
      v2: "functions/src/v2/identity_tests.py.hbs",
    },
    eventarc: {
      v2: "functions/src/v2/eventarc_tests.py.hbs",
    },
    alerts: {
      v2: "functions/src/v2/alerts_tests.py.hbs",
    },
  };

  log(`\n📁 Generating Python functions...`);

  // Collect all dependencies from all suites
  const allDependencies = {};
  const allDevDependencies = {};

  // Generate test files for each suite
  const generatedSuites = [];
  for (const suite of suites) {
    const { name, service, version } = suite;

    // Select the appropriate template
    const templatePath = templateMap[service]?.[version];
    if (!templatePath) {
      error(`❌ No template found for service '${service}' version '${version}'`);
      error(`Available templates:`);
      Object.entries(templateMap).forEach(([svc, versions]) => {
        Object.keys(versions).forEach((ver) => {
          error(`  - ${svc} ${ver}`);
        });
      });
      continue; // Skip this suite but continue with others
    }

    log(`   📋 ${name}: Using service: ${service}, version: ${version}`);

    // Create context for this suite's template
    const context = {
      ...suite,
      testRunId,
      sdkPackage,
      timestamp: new Date().toISOString(),
      projectId: "functions-integration-tests-v2",
    };

    // Generate the test file for this suite
    const outputPath = `functions/${version}/${service}_tests.py`;

    if (generateFromTemplate(templatePath, outputPath, context)) {
      // Collect dependencies
      Object.assign(allDependencies, suite.dependencies || {});
      Object.assign(allDevDependencies, suite.devDependencies || {});

      // Track generated suite info for main file
      generatedSuites.push({
        name,
        service,
        version,
        projectId: suite.projectId,
        region: suite.region,
        functions: suite.functions.map((f) => `${f.name}_${testRunId}`),
      });
    }
  }

  if (generatedSuites.length === 0) {
    throw new Error("No functions were generated");
  }

  // Generate shared files (only once)
  const sharedContext = {
    projectId,
    region,
    testRunId,
    sdkPackage,
    timestamp: new Date().toISOString(),
    dependencies: allDependencies,
    devDependencies: allDevDependencies,
  };

  // Create __init__ files for packages
  mkdirSync(join(ROOT_DIR, "generated", "functions", "v1"), { recursive: true });
  mkdirSync(join(ROOT_DIR, "generated", "functions", "v2"), { recursive: true });

  writeFileSync(join(ROOT_DIR, "generated", "functions", "__init__.py"), "");
  writeFileSync(join(ROOT_DIR, "generated", "functions", "v1", "__init__.py"), "");
  writeFileSync(join(ROOT_DIR, "generated", "functions", "v2", "__init__.py"), "");

  // Generate utils.py
  generateFromTemplate("functions/src/utils.py.hbs", "functions/utils.py", sharedContext);

  // Generate main.py with all suites
  const mainContext = {
    projectId,
    testRunId,
    suites: generatedSuites.map((s) => ({
      name: s.name,
      service: s.service,
      version: s.version,
    })),
  };

  generateFromTemplate("functions/src/main.py.hbs", "functions/main.py", mainContext);

  // Generate requirements.txt
  const requirementsContext = {
    ...sharedContext,
    sdkPackage: sdkPackage.startsWith("file:")
      ? sdkPackage.replace("file:", "./")
      : sdkPackage,
    dependencies: [
      // Add any additional Python dependencies here
    ]
  };

  generateFromTemplate("functions/requirements.txt.hbs", "functions/requirements.txt", requirementsContext);

  // Generate firebase.json
  generateFromTemplate("functions/firebase.json.hbs", "firebase.json", sharedContext);

  // Write metadata for cleanup and reference
  const metadata = {
    projectId,
    region,
    testRunId,
    language: "python",
    generatedAt: new Date().toISOString(),
    suites: generatedSuites,
  };

  writeFileSync(join(ROOT_DIR, "generated", ".metadata.json"), JSON.stringify(metadata, null, 2));

  // Copy the SDK package into the functions directory if using local SDK
  if (sdkPackage.startsWith("file:")) {
    const packageFileName = sdkPackage.replace("file:", "");
    const packageSourcePath = join(ROOT_DIR, packageFileName);
    const packageDestPath = join(ROOT_DIR, "generated", "functions", packageFileName);

    if (existsSync(packageSourcePath)) {
      copyFileSync(packageSourcePath, packageDestPath);
      log(`   ✅ Copied SDK package to functions directory`);
    } else {
      error(`   ⚠️  Warning: SDK package not found at ${packageSourcePath}`);
      error(`      Run './scripts/pack-for-integration-tests.sh' from the root directory first`);
    }
  }

  log("\n✨ Generation complete!");
  log(
    `   Generated ${generatedSuites.length} suite(s) with ${generatedSuites.reduce(
      (acc, s) => acc + s.functions.length,
      0
    )} function(s)`
  );

  log("\nNext steps:");
  log("  1. cd generated/functions");
  log("  2. python -m venv venv && source venv/bin/activate");
  log("  3. pip install -r requirements.txt");
  log(`  4. firebase deploy --project ${projectId}`);

  return metadata;
}

// CLI interface when run directly
if (import.meta.url === `file://${process.argv[1]}`) {
  const args = process.argv.slice(2);

  // Handle help
  if (args.length === 0 || args.includes("--help") || args.includes("-h")) {
    console.log("Usage: node generate.js <suite-names...> [options]");
    console.log("\nExamples:");
    console.log("  node generate.js v1_firestore                     # Single suite");
    console.log("  node generate.js v1_firestore v1_database         # Multiple suites");
    console.log("  node generate.js 'v1_*'                          # All v1 suites (pattern)");
    console.log("  node generate.js 'v2_*'                          # All v2 suites (pattern)");
    console.log("  node generate.js --list                          # List available suites");
    console.log("  node generate.js --config config/suites.yaml v1_firestore");
    console.log("\nOptions:");
    console.log("  --config <path>    Path to configuration file (default: auto-detect)");
    console.log("  --list            List all available suites");
    console.log("  --help, -h        Show this help message");
    console.log("\nEnvironment variables:");
    console.log("  TEST_RUN_ID       Override test run ID (default: auto-generated)");
    console.log("  PROJECT_ID        Override project ID from config");
    console.log("  REGION           Override region from config");
    console.log("  SDK_PACKAGE      Path to Firebase Functions SDK package (wheel)");
    process.exit(0);
  }

  // Handle --list option
  if (args.includes("--list")) {
    const configPath = join(ROOT_DIR, "config", "suites.yaml");

    console.log("\nAvailable test suites:");

    if (existsSync(configPath)) {
      console.log("\n📁 All Suites (config/suites.yaml):");
      const suites = listAvailableSuites(configPath);
      suites.forEach((suite) => console.log(`  - ${suite}`));
    } else {
      console.error("❌ Config file not found:", configPath);
    }

    process.exit(0);
  }

  // Parse options
  const options = {
    testRunId: process.env.TEST_RUN_ID,
    projectId: process.env.PROJECT_ID,
    region: process.env.REGION,
    sdkPackage: process.env.SDK_PACKAGE
  };

  // Extract config path if provided
  const configIndex = args.indexOf("--config");
  if (configIndex !== -1 && configIndex < args.length - 1) {
    options.configPath = args[configIndex + 1];
    args.splice(configIndex, 2);
  }

  // Remaining args are suite patterns
  const suitePatterns = args.filter((arg) => !arg.startsWith("--"));

  if (suitePatterns.length === 0) {
    console.error("Error: No suite names provided");
    console.log("Run with --help for usage information");
    process.exit(1);
  }

  generateFunctions(suitePatterns, options).catch((err) => {
    console.error("Generation failed:", err.message);
    process.exit(1);
  });
}