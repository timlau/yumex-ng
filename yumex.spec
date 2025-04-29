%global app_id dk.yumex.Yumex
%global app_build release

Name:     yumex
Version:  5.3.2
Release:  %autorelease
Summary:  Yum Extender graphical package management tool

Group:    Applications/System
License:  GPL-3.0-or-later
URL:      https://github.com/timlau/yumex-ng
Source0:  %{url}/releases/download/%{name}-%{version}/%{name}-%{version}.tar.gz

BuildArch: noarch
BuildRequires: python3-devel
BuildRequires: meson
BuildRequires: blueprint-compiler >= 0.4.0
BuildRequires: gettext
BuildRequires: desktop-file-utils
BuildRequires: libappstream-glib
BuildRequires: pkgconfig(glib-2.0)
BuildRequires: pkgconfig(gtk4)
BuildRequires: pkgconfig(libadwaita-1)
BuildRequires: pkgconfig(pygobject-3.0)
BuildRequires: systemd-rpm-macros

Requires: python3-gobject
Requires: libadwaita >= 1.6
Requires: gtk4
Requires: python3-dbus
Requires: flatpak-libs > 1.15.0
Requires: appstream >= 1.0.2

Recommends: %{name}-updater

# dnf5 requirements
Requires: dnf5daemon-server >= 5.2.12
Provides: yumex-dnf5 = %{version}-%{release}
Obsoletes: yumex-dnf5 < %{version}-%{release}

%description
Graphical package tool for maintain packages on the system

%package -n %{name}-updater
Summary:  Yum Extender updater app
Requires: %{name} = %{version}-%{release}
Requires: python3-gobject
Requires: gtk3
Requires: python3-dbus
Requires: flatpak-libs > 1.15.0
Requires: libappindicator-gtk3

Provides: yumex-dnf5-updater-systray = %{version}-%{release}
Obsoletes: yumex-dnf5-updater-systray < %{version}-%{release}
Provides: yumex-updater-systray = %{version}-%{release}
Obsoletes: yumex-updater-systray < %{version}-%{release}

%description -n %{name}-updater
Service to check and notify about available updates

%prep
%setup -q

%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.metainfo.xml
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{app_id}.desktop

%build
%meson --buildtype=%{app_build}
%meson_build

%install
%meson_install

%find_lang %{name}

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
glib-compile-schemas /usr/share/glib-2.0/schemas/ &>/dev/null || :

%post -n %{name}-updater
%systemd_user_post  %{name}-updater.service

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi

%postun -n %{name}-updater
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache %{_datadir}/icons/hicolor &>/dev/null || :
fi
%systemd_user_postun_with_restart %{name}-updater.service
%systemd_user_postun_with_reload %{name}-updater.service
%systemd_user_postun %{name}-updater.service

%preun -n %{name}-updater
%systemd_user_preun %{name}-updater.service

%files -f  %{name}.lang
%doc README.md
%license LICENSE
%{_datadir}/%{name}/
%{_bindir}/%{name}
%{python3_sitelib}/%{name}/
%{_datadir}/applications/%{app_id}*.desktop
%{_datadir}/icons/hicolor/scalable/apps/dk.yumex.Yumex.svg
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/glib-2.0/schemas/%{app_id}.gschema.xml

%files -n %{name}-updater
%{_userunitdir}/%{name}-updater.service
%{_prefix}/lib/systemd/user-preset/*%{name}-updater.preset
%{_bindir}/yumex_updater
%{_datadir}/icons/hicolor/scalable/apps/yumex-update-*.svg

%changelog
%autochangelog
