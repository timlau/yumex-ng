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
  'ui/window.py',
]
PY_INSTALLDIR.install_sources(yumex_ui_modules, subdir: 'yumex/ui')