# Yum Extender (NextGen)

This is repository contains the first steps to create a future yum extender
with a more modern look & feel using gtk4/libadwaita etc.

The first steps is to build the GUI and later the real package handling functionality will be added

Follow news on the development on 

[X/Twitter](https://x.com/NerdyTim_666)

# how to test

- check out this repository
- install deps `make inst-deps`
- run `./local.sh`

# Packages for Fedora 39,40 & Rawhide

[Fedora Copr Repo](https://copr.fedorainfracloud.org/coprs/timlau/yumex-ng/)

# what is not working yet

- No group support
- No history support
- Changing enabled repositories in preferences

# current look

## Packages Page
![packages](data/gfx/yumex-ng-main.png) 

## package view settings
![package settings](data/gfx/yumex-ng-package-setting.png) 

## package search
![package search](data/gfx/yumex-ng-search.png) 

## Queue Page
![queue](data/gfx/yumex-ng-queue.png) 

## flatpaks page
![flatpak](data/gfx/yumex-ng-flatpaks.png) 

## flatpak installer
![flatpak-installer](data/gfx/yumex-ng-flatpaks-install.png) 


[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
