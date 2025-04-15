project(
    'yumex',
    version: '5.3.0',
    meson_version: '>= 0.61.0',
)

APPLICATION_ID = 'dk.yumex.Yumex'
BACKEND = get_option('dnf_backend')

# Import modules
gnome = import('gnome')
i18n = import('i18n')
python = import('python')

dependency('glib-2.0')
dependency('gtk4', version: '>= 4.8.0')
dependency('libadwaita-1', version: '>= 1.6')
dependency('pygobject-3.0', version: '>= 3.42.0')

if get_option('buildtype') == 'debug'
    VCS_TAG = run_command('date', '+%Y%m%d', check: true).stdout().strip()
    if VCS_TAG == ''
        VERSION_SUFFIX = '-devel'
    else
        VERSION_SUFFIX = '-git@0@'.format(VCS_TAG)
    endif
else
    VERSION_SUFFIX = ''
endif

# Python installation directory
PY_INSTALLDIR = python.find_installation('python3', required: true)

# Check if python3 is installed
if not PY_INSTALLDIR.found()
    error('No valid python3 binary found')
endif

PKGDATA_DIR = join_paths(
    get_option('prefix'),
    get_option('datadir'),
    meson.project_name(),
)

# Install configuration data
conf = configuration_data()
conf.set('PKGDATA_DIR', PKGDATA_DIR)
conf.set('APP_ID', APPLICATION_ID)
conf.set('DATA_DIR', join_paths(get_option('prefix'), get_option('datadir')))
conf.set(
    'LOCALE_DIR',
    join_paths(get_option('prefix'), get_option('localedir')),
)
conf.set('PYTHON', PY_INSTALLDIR.full_path())
conf.set('VERSION', meson.project_version())
conf.set('BUILD_TYPE', get_option('buildtype'))
conf.set('SCHEMAS_DIR', PKGDATA_DIR)
conf.set('SOURCE_DIR', meson.current_source_dir())
conf.set('BUILD_DIR', meson.current_build_dir())

conf.set('local_build', 'False')

# Local install configuration data
local_conf = configuration_data()
local_conf.set('PKGDATA_DIR', join_paths(meson.current_build_dir(), 'data'))
local_conf.set('APP_ID', APPLICATION_ID)
local_conf.set(
    'LOCALE_DIR',
    join_paths(get_option('prefix'), get_option('datadir'), 'locale'),
)
local_conf.set('PYTHON', meson.current_source_dir())
local_conf.set('VERSION', meson.project_version())
local_conf.set('BUILD_TYPE', get_option('buildtype'))
local_conf.set(
    'SCHEMAS_DIR',
    join_paths(meson.current_build_dir(), get_option('datadir')),
)
local_conf.set('SOURCE_DIR', meson.current_source_dir())
local_conf.set('BUILD_DIR', meson.current_build_dir())

local_conf.set('local_build', 'True')

subdir('data')
subdir('yumex')
subdir('po')

gnome.post_install(
    glib_compile_schemas: true,
    gtk_update_icon_cache: true,
    update_desktop_database: true,
)