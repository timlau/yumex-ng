prefixdir = get_option('prefix')
userunitdir = prefixdir / 'lib/systemd/user'
userpresetdir = prefixdir / 'lib/systemd/user-preset'
summary(
    {
        'prefixdir': prefixdir,
        'userunitdir': userunitdir,
        'userpresetdir': userpresetdir,

    },
)

# Install systemd service file
install_data(
    'yumex-updater.service',
    install_dir: userunitdir,
)

# Install systemd preset file
install_data(
    '50-yumex-updater.preset',
    install_dir: userpresetdir,
)
