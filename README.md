# Yum Extender (NextGen)

This is repository contains the next generation of yum extender
with a more modern look & feel using gtk4/libadwaita etc.

Follow news in [Announcements](https://github.com/timlau/yumex-ng/discussions/categories/announcements)

## how to test

-   check out this repository
-   install deps `make inst-deps`
-   run `./local.sh`

## build and install local test rpms

-   check out this repository
-   install deps `make inst-deps`
-   install build deps `make inst-build-tools`
-   `make test-inst` ( if yumex is not installed )
-   `make test-update` ( if yumex is installed on a previous date )
-   `make test-reinst` ( if yumex is installed on the same date )

## Packages for Fedora 41,42 & Rawhide (COPR)

**Stable**
[yumex-ng](https://copr.fedorainfracloud.org/coprs/timlau/yumex-ng/)

**Development**
[yumex-ng-dev](https://copr.fedorainfracloud.org/coprs/timlau/yumex-ng-dev/)

## Troubleshooting

[Check Here](docs/debug.md)

## current look

### Packages Page

![packages](data/gfx/yumex-ng-main.png)

### package view settings

![package settings](data/gfx/yumex-ng-package-setting.png)

### package search

![package search](data/gfx/yumex-ng-search.png)

### Queue Page

![queue](data/gfx/yumex-ng-queue.png)

### flatpaks page

![flatpak](data/gfx/yumex-ng-flatpaks.png)

### flatpak installer

![flatpak-installer](data/gfx/yumex-ng-flatpaks-install.png)

[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
