# How to release

**Important**: Before releasing a new version, **all changes must be commited** with no loose files and unstaged changes. If any changes are unstaged `setuptools-scp` will build a development release during CI builds, instead of an official build.


1. Run `git-cliff --bump` to update the change log and bump the version.
2. Commit the changelog.
3. Tag the last commit using the bumped version `git tag v{v_number}`
4. Push changes and tags to initiate CI/CD.
