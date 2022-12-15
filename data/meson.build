gnome = import('gnome')

subdir('ui')
subdir('icons')

gnome.compile_resources('yumex',
  'yumex.gresource.xml',
  gresource_bundle: true,
  source_dir: meson.current_build_dir(),
  install: true,
  install_dir: PKGDATA_DIR,
  dependencies: blueprints
)

configure_file(
  input: '@0@.gschema.xml.in'.format(APPLICATION_ID),
  output: '@0@.gschema.xml'.format(APPLICATION_ID),
  configuration: conf,
  install: true,
  install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas')
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
  test('Validate schema file', compile_schemas,
    args: ['--strict', '--dry-run', meson.current_source_dir()]
  )
endif

desktop_file = i18n.merge_file(
  input: configure_file(
    input: '@0@.desktop.in.in'.format(APPLICATION_ID),
    output: '@BASENAME@',
    configuration: conf
  ),
  output: '@0@.desktop'.format(APPLICATION_ID),
  type: 'desktop',
  po_dir: '../po',
  install: true,
  install_dir: join_paths(get_option('datadir'), 'applications')
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
  test('Validate desktop file', desktop_utils,
    args: [desktop_file.full_path()]
  )
endif


