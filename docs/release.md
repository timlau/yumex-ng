# Create a new release check list

-   run tests
    -   run `make run-tests`
    -   run `make tun-tests-live`
-   update the code
    -   bump the version number in .\meson.build
    -   bump the version number in .\yumex.spec
    -   add changelog entry in .\yumex.spec
    -   add new release in data/dk.yumex.Yumex.metainfo.xml.in.in
-   build the release
    -   run `make rpm` to test tha rpm builds without issues
    -   run `make release`
        -   this will do the following:
            -   commit the changes above to git
            -   make a git release tag
            -   push it to github
            -   make source archive
            -   build the src.rpm
            -   create a Fedora Copr build of the src.rpm
-   make a new github release
    -   https://github.com/timlau/yumex-ng/releases/new
    -   select the release tag
    -   add title and description
    -   add the source archive from ./build/SOURCES
    -   add the yumex-**version**.src.rpm from ./build/SRPMS
    -   add the yumex-dnf5-**version**.src.rpm from ./build/SRPMS
    -   publish the release
-   create a stable branch (5.y.x) and publish it for future fix to the stable branch

## Prepare for a next release development

-   bump the version (secord digit MUST be uneven)
    -   update the version number in .\meson.build
    -   update the version number in .\yumex.spec
