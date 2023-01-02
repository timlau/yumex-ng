configure_file(
  input: 'yumex.in',
  output: 'local-yumex',
  configuration: local_conf
)

configure_file(
  input:  meson.project_name() + '.in',
  output: meson.project_name(),
  configuration: conf,
  install_dir: get_option('bindir')
)

configure_file(
  input: 'constants.py.in',
  output: 'constants.py',
  configuration: configuration_data({
    'APP_ID': APPLICATION_ID,
    'VERSION': meson.project_version() + VERSION_SUFFIX,
    'BUILD_TYPE': get_option('buildtype'),
    'PKGDATA_DIR': PKGDATA_DIR,
    'LOCALE_DIR': conf.get('LOCALE_DIR'),
    'BACKEND': BACKEND,
  }),
  install: true,
  install_dir: PY_INSTALLDIR.get_install_dir() / 'yumex',
)

launcher = join_paths(meson.project_build_root(), 'yumex', 'local-' + meson.project_name())

run_target('run',
  command: [launcher]
)

# Install sources
yumex_sources = [
  '__init__.py',
  'main.py',
]
PY_INSTALLDIR.install_sources(yumex_sources, subdir: 'yumex')


# Install ui Python modules
yumex_ui_modules = [
'ui/__init__.py',
'ui/flatpak_installer.py',
'ui/flatpak_view.py',
'ui/pachage_view.py',
'ui/package_info.py',
'ui/package_settings.py',
'ui/preferences.py',
'ui/progress.py',
'ui/queue_view.py',
'ui/transaction_result.py',
'ui/window.py'
]
PY_INSTALLDIR.install_sources(yumex_ui_modules, subdir: 'yumex/ui')

yumex_backend_modules = [
'backend/__init__.py',
'backend/daemon.py',
'backend/dnf.py',
'backend/flatpak.py',
'backend/dnf5.py'
]
PY_INSTALLDIR.install_sources(yumex_backend_modules, subdir: 'yumex/backend')


yumex_utils_modules = [
'utils/__init__.py',
'utils/types.py'
]
PY_INSTALLDIR.install_sources(yumex_utils_modules, subdir: 'yumex/utils')

