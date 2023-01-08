blueprints = custom_target('blueprints',
  input: files(
    'window.blp',
    'package_view.blp',
    'queue_view.blp',
    'queue_row.blp',
    'preferences.blp',
    'package_settings.blp',
    'progress.blp',
    'repository.blp',
    'package_info.blp',
    'transaction_result.blp',
    'shortcuts.blp',
    'flatpak_view.blp',
    'flatpak_row.blp',
    'flatpak_installer.blp',
    'flatpak_result.blp'
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@']
)
