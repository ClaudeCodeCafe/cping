#!/usr/bin/env bash
# Smoke tests for cping
set -euo pipefail

CPING="./cping"
PASS=0
FAIL=0
SKIP=0

pass() {
    echo "  PASS: $1"
    PASS=$((PASS + 1))
}

fail() {
    echo "  FAIL: $1"
    FAIL=$((FAIL + 1))
}

skip() {
    echo "  SKIP: $1"
    SKIP=$((SKIP + 1))
}

echo "Running cping smoke tests..."
echo

# Test 1: --version outputs version string
echo "Test: --version"
VERSION_OUTPUT=$($CPING --version 2>&1)
if echo "$VERSION_OUTPUT" | grep -q "cping 0\.1\.0"; then
    pass "--version outputs 'cping 0.1.0'"
else
    fail "--version output unexpected: $VERSION_OUTPUT"
fi

# Test 2: --help shows usage
echo "Test: --help"
HELP_OUTPUT=$($CPING --help 2>&1)
if echo "$HELP_OUTPUT" | grep -q "usage:"; then
    pass "--help shows usage"
elif echo "$HELP_OUTPUT" | grep -qi "usage"; then
    pass "--help shows usage"
else
    fail "--help output missing 'usage': $HELP_OUTPUT"
fi

# Test 3: --json outputs valid JSON (network required)
echo "Test: --json"
set +e
JSON_OUTPUT=$($CPING --json 2>&1)
JSON_EXIT=$?
set -e
if [ "$JSON_EXIT" -eq 1 ]; then
    skip "--json: network unavailable"
elif echo "$JSON_OUTPUT" | python3 -m json.tool > /dev/null 2>&1; then
    pass "--json outputs valid JSON"
else
    fail "--json output is not valid JSON"
fi

# Test 4: Default run exits 0 or 2 (network required)
echo "Test: default exit code"
set +e
$CPING --no-color > /dev/null 2>&1
EXIT_CODE=$?
set -e
if [ "$EXIT_CODE" -eq 0 ] || [ "$EXIT_CODE" -eq 2 ]; then
    pass "default run exits with $EXIT_CODE (0 or 2 expected)"
elif [ "$EXIT_CODE" -eq 1 ]; then
    skip "default exit code: network unavailable"
else
    fail "default run exited with $EXIT_CODE (expected 0 or 2)"
fi

# Test 5: --no-color output contains no ANSI escape codes (network required)
echo "Test: --no-color"
set +e
NOCOLOR_OUTPUT=$($CPING --no-color 2>&1)
NOCOLOR_EXIT=$?
set -e
if [ "$NOCOLOR_EXIT" -eq 1 ]; then
    skip "--no-color: network unavailable"
elif echo "$NOCOLOR_OUTPUT" | grep -qP '\033\[' 2>/dev/null; then
    fail "--no-color output contains ANSI escape codes"
elif echo "$NOCOLOR_OUTPUT" | grep -q $'\033\['; then
    fail "--no-color output contains ANSI escape codes"
else
    pass "--no-color output is free of ANSI escape codes"
fi

# Test 6: python -m cping --version (package entry point)
echo "Test: python -m cping --version"
if [ -d "src/cping" ]; then
    MODULE_OUTPUT=$(PYTHONPATH=src python3 -m cping --version 2>&1)
    if echo "$MODULE_OUTPUT" | grep -q "cping 0\.1\.0"; then
        pass "python -m cping --version outputs 'cping 0.1.0'"
    else
        fail "python -m cping --version output unexpected: $MODULE_OUTPUT"
    fi
else
    fail "src/cping directory not found"
fi

# Test 7: cping standalone script is in sync with src/cping/cli.py
echo "Test: cping standalone is in sync with src/cping/cli.py"
CPING_BODY=$(tail -n +2 ./cping)
CLI_BODY=$(cat src/cping/cli.py)
if [ "$CPING_BODY" = "$CLI_BODY" ]; then
    pass "cping (minus shebang) matches src/cping/cli.py"
else
    fail "cping and src/cping/cli.py are out of sync"
fi

# Summary
echo
echo "Results: $PASS passed, $FAIL failed, $SKIP skipped"
if [ "$FAIL" -gt 0 ]; then
    exit 1
fi
echo "All smoke tests passed."
