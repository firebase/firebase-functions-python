# Firebase Functions Python SDK Integration Tests

This directory contains integration tests for the Firebase Functions Python SDK. The framework allows testing Python Firebase Functions by deploying them to real Firebase projects and verifying their behavior through comprehensive test suites.

## Overview

The integration test framework:
- Generates Python functions from Handlebars templates with unique test IDs
- Deploys functions to Firebase projects for real-world testing
- Uses Jest tests to verify function behavior
- Supports all Firebase trigger types (Firestore, Database, Storage, Auth, etc.)

## Prerequisites

1. **Build the Python SDK**:
   ```bash
   # From the root firebase-functions-python directory
   ./scripts/pack-for-integration-tests.sh
   ```
   This creates `integration_test/firebase-functions-python-local.whl`

2. **Firebase Projects**: V1 and V2 tests run on separate Firebase projects:
   - **V1 functions**: `functions-integration-tests`
   - **V2 functions**: `functions-integration-tests-v2`

   These projects are completely isolated from each other.

3. **Dependencies**:
   - Node.js 18+ (for test runner and generation scripts)
   - Python 3.10+ (for Firebase Functions)
   - Firebase CLI (`npm install -g firebase-tools`)
   - uv (Python package manager)

## Quick Start

### 1. Generate Python Functions

```bash
cd integration_test

# Generate all v1 suites
npm run generate:v1

# Generate all v2 suites
npm run generate:v2

# Generate specific test suite
node scripts/generate.js v1_firestore

# List available suites
node scripts/generate.js --list
```

### 2. Deploy Functions

**For V1 Tests:**
```bash
npm run deploy:v1
# OR manually:
cd generated/functions
firebase deploy --only functions --project functions-integration-tests
```

**For V2 Tests:**
```bash
npm run deploy:v2
# OR manually:
cd generated/functions
firebase deploy --only functions --project functions-integration-tests-v2
```

### 3. Run Tests

**V1 Tests (uses functions-integration-tests project):**
```bash
# Run all V1 tests
npm run test:v1:all

# Run specific V1 test
npm run test:v1:firestore

# Run V1 tests in parallel
npm run test:v1:all:parallel
```

**V2 Tests (uses functions-integration-tests-v2 project):**
```bash
# Run all V2 tests
npm run test:v2:all

# Run V2 tests in parallel
npm run test:v2:all:parallel
```

### 4. Cleanup

```bash
# Clean up V1 deployed functions
npm run cleanup:v1

# Clean up V2 deployed functions
npm run cleanup:v2

# Remove generated files
npm run clean
```

## Project Structure

```
integration_test/
├── config/
│   ├── v1/suites.yaml           # V1 test suite configuration
│   └── v2/suites.yaml           # V2 test suite configuration
├── templates/
│   └── functions/               # Python function templates
│       ├── firebase.json.hbs
│       ├── requirements.txt.hbs
│       └── src/
│           ├── main.py.hbs
│           ├── utils.py.hbs
│           └── v1/v2/           # Trigger-specific templates
├── scripts/
│   ├── generate.js              # Function generator
│   ├── run-tests.js            # Test runner
│   ├── cleanup-suite.sh        # Cleanup script
│   └── pack-for-integration-tests.sh  # SDK build script
├── tests/                       # Jest test suites
│   ├── v1/                     # V1 function tests
│   └── v2/                     # V2 function tests
└── generated/                   # Generated functions (gitignored)
```

## Configuration

### Suite Configuration (`config/v[1|2]/suites.yaml`)

```yaml
defaults:
  projectId: functions-integration-tests
  region: us-central1
  timeout: 540
  dependencies:
    firebase-admin: "^6.0.1"
    firebase-functions: "{{sdkTarball}}"  # Replaced with wheel path
  devDependencies: {}

suites:
  - name: v1_firestore
    description: "V1 Firestore trigger tests"
    version: v1
    service: firestore
    functions:
      - name: firestoreDocumentOnCreateTests
        trigger: onCreate
        document: "tests/{testId}"
```

## How It Works

1. **Template Generation**: The `generate.js` script:
   - Reads YAML configuration for test suites
   - Generates Python functions from Handlebars templates
   - Injects unique `TEST_RUN_ID` for function isolation
   - Creates `requirements.txt` with local SDK wheel

2. **Function Structure**: Generated Python functions:
   ```python
   @firestore_fn.on_document_created(
       document="tests/{testId}",
       region="us-central1",
       timeout_sec=540
   )
   def firestoreDocumentOnCreateTests_t24vxpkcr(event):
       # Store event context for verification
       test_id = event.params.get("testId")
       context_data = {
           "eventId": event.id,
           "timestamp": event.time,
           # ... other context
       }
       firestore.client().collection("firestoreDocumentOnCreateTests").document(test_id).set(context_data)
   ```

3. **Test Execution**: Jest tests:
   - Trigger functions by manipulating Firebase resources
   - Verify function execution by checking stored context data
   - Wait for function completion using retry logic

## Adding New Trigger Types

To add support for a new trigger type:

1. **Create Template**: Add template in `templates/functions/src/v1/[service]_tests.py.hbs`
2. **Update Generator**: Add mapping in `generate.js`:
   ```javascript
   const templateMap = {
     // ... existing mappings
     newservice: {
       v1: "functions/src/v1/newservice_tests.py.hbs"
     }
   }
   ```
3. **Add Configuration**: Update `config/v1/suites.yaml`
4. **Add Tests**: Create Jest test file in `tests/v1/[service].test.ts`

## Environment Variables

- `TEST_RUN_ID` - Override test run ID (default: auto-generated)
- `PROJECT_ID` - Override project ID from config
- `REGION` - Override region from config
- `SDK_PACKAGE` - Path to SDK wheel file

## Supported Trigger Types

### V1 Functions
- ✅ Firestore (onCreate, onDelete, onUpdate, onWrite)
- 🚧 Realtime Database
- 🚧 Storage
- 🚧 Auth (blocking and non-blocking)
- 🚧 Pub/Sub
- 🚧 Remote Config
- 🚧 Test Lab
- 🚧 Task Queues

### V2 Functions
- 🚧 All V2 trigger types

## Troubleshooting

### Common Issues

1. **SDK not found**: Run `./scripts/pack-for-integration-tests.sh` first
2. **Import errors**: Ensure virtual environment is activated
3. **Deployment fails**: Check Firebase project permissions and quotas
4. **Tests fail**: Verify TEST_RUN_ID matches deployed functions
5. **Build failures**: Check Cloud Build logs in GCP Console
6. **Service account permissions**: Ensure service account has necessary permissions
7. **Project access**: Verify projects exist and are accessible

### Debug Commands

```bash
# Check generated functions
ls -la generated/functions/src/

# View function logs for V1
firebase functions:log --project functions-integration-tests

# View function logs for V2
firebase functions:log --project functions-integration-tests-v2

# Test locally (limited functionality)
cd generated/functions
functions-framework --target=main --debug

# Download artifacts from GCS bucket (V1)
gsutil ls gs://functions-integration-tests-test-results/

# Download artifacts from GCS bucket (V2)
gsutil ls gs://functions-integration-tests-v2-test-results/
```

### Cleanup Issues

If functions aren't cleaned up properly:
```bash
# For V1 project
firebase functions:delete --project functions-integration-tests --force

# For V2 project
firebase functions:delete --project functions-integration-tests-v2 --force
```

## Cloud Build Integration

The integration tests are run via Cloud Build with complete project separation. V1 and V2 tests run on different Firebase projects to ensure isolation.

### Available Configurations

#### 1. `cloudbuild-v1.yaml` - V1 Tests Only
- **Project**: `functions-integration-tests`
- **What it does**:
  - Builds the Python SDK wheel
  - Generates all V1 Python functions
  - Deploys to V1 project
  - Runs all V1 integration tests
  - Cleans up deployed functions

**Usage** (from repository root):
```bash
gcloud builds submit --config=integration_test/cloudbuild-v1.yaml .
```

#### 2. `cloudbuild-v2.yaml` - V2 Tests Only
- **Project**: `functions-integration-tests-v2`
- **What it does**:
  - Builds the Python SDK wheel
  - Generates all V2 Python functions
  - Deploys to V2 project
  - Runs all V2 integration tests
  - Cleans up deployed functions

**Usage** (from repository root):
```bash
gcloud builds submit --config=integration_test/cloudbuild-v2.yaml .
```

### Configuration Details

#### Build Environment
- **Machine Type**: `E2_HIGHCPU_8` (for faster builds)
- **Timeout**: 3600s (1 hour) per configuration
- **Python Version**: 3.11
- **Node Version**: 20

#### Build Steps

1. **SDK Build** (Python 3.11 container):
   - Installs `uv` package manager
   - Builds wheel from source
   - Copies to `integration_test/firebase-functions-python-local.whl`

2. **Test Execution** (Node 20 container):
   - Installs npm dependencies
   - Installs Firebase CLI
   - Generates Python functions from templates
   - Creates Python venv and installs dependencies
   - Deploys functions to Firebase
   - Runs Jest integration tests
   - Cleans up deployed functions

#### Artifacts
All builds store:
- Test logs in `integration_test/logs/**/*.log`
- Metadata in `integration_test/generated/.metadata.json`

Artifacts are uploaded to:
- V1: `gs://functions-integration-tests-test-results/${BUILD_ID}`
- V2: `gs://functions-integration-tests-v2-test-results/${BUILD_ID}`

### Automated Triggers

You can set up Cloud Build triggers to run on:
- **Pull requests**: Use `cloudbuild-v1.yaml` for quick feedback
- **Merges to main**: Run both `cloudbuild-v1.yaml` and `cloudbuild-v2.yaml` separately
- **Nightly builds**: Run both configurations for full regression testing

### Manual CI/CD Steps

For custom CI/CD pipelines, run V1 and V2 tests separately:

#### V1 Tests
```bash
# Build SDK
./scripts/pack-for-integration-tests.sh

# Generate, deploy, and test V1 functions
cd integration_test
node scripts/generate.js 'v1_*'
cd generated/functions
pip install -r requirements.txt
firebase deploy --project functions-integration-tests --token $FIREBASE_TOKEN
cd ../..
npm run test:v1:all:sequential
npm run cleanup:v1
```

#### V2 Tests
```bash
# Build SDK
./scripts/pack-for-integration-tests.sh

# Generate, deploy, and test V2 functions
cd integration_test
node scripts/generate.js 'v2_*'
cd generated/functions
pip install -r requirements.txt
firebase deploy --project functions-integration-tests-v2 --token $FIREBASE_TOKEN
cd ../..
npm run test:v2:all:sequential
npm run cleanup:v2
```

## Contributing

When adding new features:
1. Follow the existing template patterns
2. Ensure Python code follows PEP 8
3. Test with both local and deployed functions
4. Update this documentation

## License

Apache 2.0 - See LICENSE file in the root directory.