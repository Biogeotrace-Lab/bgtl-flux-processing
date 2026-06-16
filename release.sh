#!/bin/bash
set -e # Exit immediately if any command fails

# 1. Ask git-cliff to calculate the next version number (e.g., "1.2.0")
#    and save it into a variable.
NEXT_VERSION=$(git cliff --bumped-version)

if [ -z "$NEXT_VERSION" ]; then
    echo "No relevant changes found. Nothing to release!"
    exit 0
fi

echo "Next version will be: $NEXT_VERSION"

# 2. Generate the changelog, using that exact version for the new header
git cliff --bump --output CHANGELOG.md

# 3. Commit the updated changelog (and pyproject.toml if you updated it)
git add CHANGELOG.md
git commit -m "chore(release): prepare for $NEXT_VERSION"

# 4. Tag the commit automatically using the variable
#    (Add a 'v' here if you want your tags formatted like v1.2.0)
git tag "v$NEXT_VERSION"

echo "Successfully created tag v$NEXT_VERSION!"

