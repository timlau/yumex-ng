if (get_option('with_updater'))
    # Install systemd service file
    install_data(
        'yumex-updater-systray.service',
        install_dir: '/usr/lib/systemd/user/',
    )

    # Install systemd preset file
    install_data(
        '50-yumex-updater-systray.preset',
        install_dir: '/usr/lib/systemd/user-preset/',
    )

    # Install service config
    install_data('yumex-service.conf', install_dir: '/usr/share/yumex/')

    # Create a symlink in bindir to service/yumex_updater_systray.py
    install_symlink(
        'yumex_updater_systray',
        install_dir: get_option('bindir'),
        pointing_to: join_paths(
            PY_INSTALLDIR.get_install_dir(),
            'yumex',
            'yumex_updater_systray.py',
        ),
    )
endif