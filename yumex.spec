%global app_id dk.yumex.Yumex

Name:     yumex
Version:  4.9.0
Release:  1%{?dist}
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


Requires: python3-dnfdaemon
Requires: python3-gobject
Requires: python3-dnf
Requires: libadwaita
Requires: gtk4

Obsoletes: yumex-dnf <= 4.5.1



%description
Graphical package tool for maintain packages on the system


%prep
%setup -q

%check
appstream-util validate-relax --nonet %{buildroot}%{_metainfodir}/*.metainfo.xml
desktop-file-validate %{buildroot}/%{_datadir}/applications/%{app_id}.desktop

%build
%meson
%meson_build 

%install
%meson_install

%find_lang %name

%post
/bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null || :
update-desktop-database %{_datadir}/applications &> /dev/null || :

%postun
if [ $1 -eq 0 ] ; then
    /bin/touch --no-create %{_datadir}/icons/hicolor &>/dev/null
    /usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :
fi
update-desktop-database %{_datadir}/applications &> /dev/null || :

%posttrans
/usr/bin/gtk-update-icon-cache -f %{_datadir}/icons/hicolor &>/dev/null || :

%files -f  %{name}.lang
%doc README.md 
%license LICENSE
%{_datadir}/%{name}
%{_bindir}/%{name}
%{python3_sitelib}/%{name}/
%{_datadir}/applications/%{app_id}.desktop
%{_datadir}/icons/hicolor/
%{_metainfodir}/%{app_id}.metainfo.xml
%{_datadir}/glib-2.0/schemas/%{app_id}.gschema.xml

%changelog

* Tue Dec 20 2022 Tim Lauridsen <timlau@fedoraproject.org> 4.9.0-1
- initial release (dev)

