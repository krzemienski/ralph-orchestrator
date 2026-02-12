#!/bin/bash
# This script is called by Xcode as a pre-build phase
# It ensures the Ralph backend is running before building the iOS app

# Only run for Debug builds (not Archive/Release)
if [ "${CONFIGURATION}" != "Debug" ]; then
    echo "⏭️  Skipping backend auto-start for ${CONFIGURATION} build"
    exit 0
fi

# Run the backend startup script
"${SRCROOT}/scripts/start-backend.sh"
