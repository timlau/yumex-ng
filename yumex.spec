%global app_id dk.yumex.Yumex
%global app_build release
%global app_name yumex

Name:     %{app_name}
Version:  5.3.1
Release:  %autorelease %{?gitdate}
Summary:  Yum Extender graphical package management tool

Group:    Applications/System
License:  GPLv3+
URL:      http://yumex.dk
Source0:  https://github.com/timlau/yumex-ng/releases/download/%{name}-%{version}/%{name}-%{version}.tar.gz

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

Obsoletes: yumex-dnf <= 4.5.1



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

%find_lang %{app_name}

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database %{_datadir}/applications &> /dev/null || :
glib-compile-schemas /usr/share/glib-2.0/schemas/ &> /dev/null || :

%post -n %{name}-updater
%systemd_user_post yumex-updater.service

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :
fi
update-desktop-database %{_datadir}/applications &> /dev/null || :

%files -f  %{app_name}.lang
%doc README.md
%license LICENSE
%{_datadir}/%{app_name}/yumex.gresource
%{_bindir}/%{app_name}
%{python3_sitelib}/%{app_name}
%{_datadir}/applications/%{app_id}*.desktop
%{_datadir}/icons/hicolor/scalable/apps/dk.yumex.Yumex.svg
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/glib-2.0/schemas/%{app_id}.gschema.xml

%files -n %{name}-updater
%{_userunitdir}/*.service
%{_prefix}/lib/systemd/user-preset/*.preset
%{_bindir}/yumex_updater
%{_datadir}/icons/hicolor/scalable/apps/yumex-update-*.svg

%posttrans
/usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :

%posttrans -n %{name}-updater
/usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :
%systemd_user_post yumex-updater.service

# Iterate over all user sessions
for session in $(loginctl list-sessions --no-legend | awk '{print $1}'); do
    uid=$(loginctl show-session $session -p User --value)
    user=$(getent passwd $uid | cut -d: -f1)

    # Debug statement to verify user and UID
    # echo "Applying preset and restarting service for user $user with UID $uid"

    # Set environment variables for the user session
    XDG_RUNTIME_DIR="/run/user/$uid"
    DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"

    # Apply the preset for the user session
    su - $user -c "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS systemctl --user preset yumex-updater.service" || echo "Failed to apply preset for user $user"

    # Reload the user daemon and restart the service
    su - $user -c "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS systemctl --user daemon-reload" || echo "Failed to perform daemon-reload for user $user"
    su - $user -c "XDG_RUNTIME_DIR=$XDG_RUNTIME_DIR DBUS_SESSION_BUS_ADDRESS=$DBUS_SESSION_BUS_ADDRESS systemctl --user restart yumex-updater.service" || echo "Failed to restart service for user $user"
done

%preun -n %{name}-updater
%systemd_user_preun yumex-updater.service

%changelog

* Sat Apr 26 2025 Tim Lauridsen <timlau@fedoraproject.org> 5.3.1-1
- bump version to 5.3.1
- use autorelease for easier setting gitdate for git builds
* Tue Apr 15 2025 Tim Lauridsen <timlau@fedoraproject.org> 5.3.0-1
- bump version to 5.3.0

* Tue Apr 15 2025 Tim Lauridsen <timlau@fedoraproject.org> 5.2.0-1
- the 5.2.0 stable release

* Mon Mar 31 2025 Tim Lauridsen <timlau@fedoraproject.org> 5.1.0-1
- the 5.1.0 release
- cleanup requirement for only using dnf5daemon for everything

* Thu Mar 27 2025 Tim Lauridsen <timlau@fedoraproject.org> 5.0.3-2
- remove support for dnf4

* Thu Nov 7 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.3-1
- the 5.0.3 release

* Fri Jul 26 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.2-1
- the 5.0.2 release

* Sun Jul 7 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.1-3
- remove updater .conf file

* Thu Jun 27 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.1-2
- fix nameing for yumex-dnf5 build

* Thu Jun 27 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.1-1
- the 5.0.1 release

* Tue Jun 25 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.0-3
- split updater service into sub-package

* Tue Jun 11 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.0-2
- added updater service
- include all .desktop files
- add appstream requirement
- add version requirement to flatpak-libs.

* Tue Jun 11 2024 Tim Lauridsen <timlau@fedoraproject.org> 5.0.0-1
- the 5.0.0 release

* Thu Apr 20 2023 Tim Lauridsen <timlau@fedoraproject.org> 4.99.4-1
- the 4.99.4 release

* Sat Jan 21 2023 Tim Lauridsen <timlau@fedoraproject.org> 4.99.3-1
- the 4.99.3 release

* Wed Jan 4 2023 Tim Lauridsen <timlau@fedoraproject.org> 4.99.2-1
- add support for building with dnf5 backend

* Wed Jan 4 2023 Tim Lauridsen <timlau@fedoraproject.org> 4.99.2-1
- the 4.99.2 release

* Tue Dec 20 2022 Tim Lauridsen <timlau@fedoraproject.org> 4.99.1-1
- the 4.99.1 release

* Tue Dec 20 2022 Tim Lauridsen <timlau@fedoraproject.org> 4.99.0-1
- initial release (dev)

