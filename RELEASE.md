# How to release

#### **Important**
Before releasing a new version, **all changes must be commited** with no loose files
and unstaged changes.


1. Run `git-cliff --bump` to update the change log and bump the version.
2. Commit the changelog.
3. Tag the last commit using the bumped version `git tag v{v_number}`
4. Push changes and tags to initiate CI/CD.
