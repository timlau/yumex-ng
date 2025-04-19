configure_file(input: 'yumex.in', output: 'local-yumex', configuration: local_conf)

configure_file(
    input: meson.project_name() + '.in',
    output: meson.project_name(),
    configuration: conf,
    install_dir: get_option('bindir'),
)

configure_file(
    input: 'constants.py.in',
    output: 'constants.py',
    configuration: configuration_data(
        {
            'APP_ID': APPLICATION_ID,
            'VERSION': meson.project_version() + VERSION_SUFFIX,
            'BUILD_TYPE': get_option('buildtype'),
            'PKGDATA_DIR': PKGDATA_DIR,
            'LOCALE_DIR': conf.get('LOCALE_DIR'),
            'BACKEND': BACKEND,
        },
    ),
    install: true,
    install_dir: PY_INSTALLDIR.get_install_dir() / 'yumex',
)

install_data('yumex_updater', install_dir: get_option('bindir'))

launcher = join_paths(meson.project_build_root(), 'yumex', 'local-' + meson.project_name())

run_target('run', command: [launcher])

# Install sources
yumex_sources = [
    '__init__.py',
    'main.py',
]
PY_INSTALLDIR.install_sources(yumex_sources, subdir: 'yumex')

# Install ui Python modules
yumex_ui_modules = [
    'ui/__init__.py',
    'ui/dialogs.py',
    'ui/flatpak_result.py',
    'ui/flatpak_view.py',
    'ui/flatpak_search.py',
    'ui/package_view.py',
    'ui/package_info.py',
    'ui/package_settings.py',
    'ui/preferences.py',
    'ui/progress.py',
    'ui/queue_view.py',
    'ui/transaction_result.py',
    'ui/window.py',
    'ui/search_settings.py',
    'ui/advanced_actions.py',
]
PY_INSTALLDIR.install_sources(yumex_ui_modules, subdir: 'yumex/ui')

yumex_backend_modules = [
    'backend/__init__.py',
    'backend/interface.py',
    'backend/cache.py',
    'backend/presenter.py',
]
PY_INSTALLDIR.install_sources(yumex_backend_modules, subdir: 'yumex/backend')

yumex_backend_dnf5daemon_modules = [
    'backend/dnf5daemon/__init__.py',
    'backend/dnf5daemon/client.py',
    'backend/dnf5daemon/filter.py',
]
PY_INSTALLDIR.install_sources(yumex_backend_dnf5daemon_modules, subdir: 'yumex/backend/dnf5daemon')

yumex_backend_flatpak_modules = [
    'backend/flatpak/__init__.py',
    'backend/flatpak/backend.py',
    'backend/flatpak/transaction.py',
    'backend/flatpak/search.py',
]
PY_INSTALLDIR.install_sources(yumex_backend_flatpak_modules, subdir: 'yumex/backend/flatpak')

yumex_backend_dnf_modules = [
    'backend/dnf/__init__.py',
]
PY_INSTALLDIR.install_sources(yumex_backend_dnf_modules, subdir: 'yumex/backend/dnf')

yumex_utils_modules = [
    'utils/__init__.py',
    'utils/enums.py',
    'utils/storage.py',
    'utils/types.py',
    'utils/updater.py',
    'utils/exceptions.py',
]
PY_INSTALLDIR.install_sources(yumex_utils_modules, subdir: 'yumex/utils')

yumex_service_modules = [
    'service/__init__.py',
    'service/dnf5daemon.py',
    'service/notification.py',
    'service/data.py',
]
PY_INSTALLDIR.install_sources(yumex_service_modules, subdir: 'yumex/service')