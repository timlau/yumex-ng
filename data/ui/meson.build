blueprints = custom_target('blueprints',
  input: files(
    'window.blp',
    'package_view.blp',
    'queue_view.blp',
    'queue_row.blp',
    'preferences.blp',
    'package_settings.blp'
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@']
)