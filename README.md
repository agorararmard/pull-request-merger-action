# pull-request-merger-action
This is a Pull Request Merger Action that works on repos with release branch structure. This will overwrite the master branch to match the latest release branch everytime.

This is mainly done for the google/skywater-pdk-libs-\* repositories.

# Workflow
In collaboration with @ax3ghazy, we created this workflow for the Pull Request Merger.

Current Workflow when the action is invoked:
- The Action will get the PR as a patch.
- The Action will apply the patch to all version branches merging upward whenever applying is possible.
- The Action will reset the master to the latest version branch.


Release branches should follow this structure: branch-\*.\*.\*

Each branch should have a tag with this strucutre: v\*.\*.\*

This action should only be invoked in case of a Pull Request. We don't handle corner cases at the moment.

# Usage:

In Pull-Request Invoked Workflow, add the following:


```yml
    steps:
      - uses: actions/checkout@v2
        with:
          ref: master
          fetch-depth: '50'

      - name: Run The Pull Request Merger
        uses: agorararmard/pull-request-merger-action@master
```

# Examples

There is an example [here](examples/pull_request_merger.yml)
