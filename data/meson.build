gnome = import('gnome')

METAINFO_DIR = join_paths(get_option('prefix'), get_option('datadir'), 'metainfo')

subdir('ui')
subdir('icons')
subdir('service')

gnome.compile_resources(
    'yumex',
    'yumex.gresource.xml',
    gresource_bundle: true,
    source_dir: meson.current_build_dir(),
    install: true,
    install_dir: PKGDATA_DIR,
    dependencies: blueprints,
)

configure_file(
    input: '@0@.gschema.xml.in'.format(APPLICATION_ID),
    output: '@0@.gschema.xml'.format(APPLICATION_ID),
    configuration: conf,
    install: true,
    install_dir: join_paths(get_option('datadir'), 'glib-2.0/schemas'),
)

compile_schemas = find_program('glib-compile-schemas', required: false)
if compile_schemas.found()
    test(
        'Validate schema file',
        compile_schemas,
        args: ['--strict', '--dry-run', meson.current_source_dir()],
    )
endif

desktop_file = i18n.merge_file(
    input: configure_file(
        input: '@0@.desktop.in.in'.format(APPLICATION_ID),
        output: '@BASENAME@',
        configuration: conf,
    ),
    output: '@0@.desktop'.format(APPLICATION_ID),
    type: 'desktop',
    po_dir: '../po',
    install: true,
    install_dir: join_paths(get_option('datadir'), 'applications'),
)

desktop_file_flatpakref = i18n.merge_file(
    input: configure_file(
        input: '@0@-flatpakref.desktop.in.in'.format(APPLICATION_ID),
        output: '@BASENAME@',
        configuration: conf,
    ),
    output: '@0@-flatpakref.desktop'.format(APPLICATION_ID),
    type: 'desktop',
    po_dir: '../po',
    install: true,
    install_dir: join_paths(get_option('datadir'), 'applications'),
)

desktop_file_rpm = i18n.merge_file(
    input: configure_file(
        input: '@0@-rpm.desktop.in.in'.format(APPLICATION_ID),
        output: '@BASENAME@',
        configuration: conf,
    ),
    output: '@0@-rpm.desktop'.format(APPLICATION_ID),
    type: 'desktop',
    po_dir: '../po',
    install: true,
    install_dir: join_paths(get_option('datadir'), 'applications'),
)

desktop_utils = find_program('desktop-file-validate', required: false)
if desktop_utils.found()
    test(
        'Validate desktop file',
        desktop_utils,
        args: [desktop_file.full_path()],
    )
    test(
        'Validate desktop file',
        desktop_utils,
        args: [desktop_file_flatpakref.full_path()],
    )
    test(
        'Validate desktop file',
        desktop_utils,
        args: [desktop_file_rpm.full_path()],
    )
endif

appstream_file = i18n.merge_file(
    input: configure_file(
        input: '@0@.metainfo.xml.in.in'.format(APPLICATION_ID),
        output: '@BASENAME@',
        configuration: conf,
    ),
    output: '@0@.metainfo.xml'.format(APPLICATION_ID),
    po_dir: '../po',
    install: true,
    install_dir: METAINFO_DIR,
)

appstream_util = find_program('appstream-util', required: false)
if appstream_util.found()
    test(
        'Validate appstream file',
        appstream_util,
        args: ['validate', appstream_file.full_path()],
    )
endif