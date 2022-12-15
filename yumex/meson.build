configure_file(
  input: 'yumex.in',
  output: 'local-yumex',
  configuration: local_conf
)

configure_file(
  input: 'constants.py.in',
  output: 'constants.py',
  configuration: configuration_data({
    'APP_ID': APPLICATION_ID,
    'RELEASE_VER': meson.project_version(),
    'VERSION': meson.project_version() ,
    'BUILD_TYPE': get_option('buildtype'),
    'PKGDATA_DIR': PKGDATA_DIR,
    'LOCALE_DIR': conf.get('LOCALE_DIR'),
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
'ui/progress.py',
'ui/package_settings.py',
'ui/__init__.py',
'ui/pachage_view.py',
'ui/package_info.py',
'ui/queue_view.py',
'ui/window.py',
]
PY_INSTALLDIR.install_sources(yumex_ui_modules, subdir: 'yumex/ui')

yumex_backend_modules = [
'backend/__init__.py',
'backend/dnf.py'
]
PY_INSTALLDIR.install_sources(yumex_backend_modules, subdir: 'yumex/backend')


yumex_utils_modules = [
'utils/__init__.py'
]
PY_INSTALLDIR.install_sources(yumex_utils_modules, subdir: 'yumex/utils')

