blueprints = custom_target('blueprints',
  input: files(
    'window.blp',
    'package_row.blp',
  ),
  output: '.',
  command: [find_program('blueprint-compiler'), 'batch-compile', '@OUTPUT@', '@CURRENT_SOURCE_DIR@', '@INPUT@']
)