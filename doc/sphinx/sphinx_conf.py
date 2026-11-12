# pylint: skip-file
# Additional project Sphinx configuration, executed at the end of the generated conf.py.

# Use the full window width with sphinx_rtd_theme (default max-width is 800px).
html_static_path.append(str(PROJECT_ROOT / 'doc' / 'sphinx' / '_static'))
html_css_files = ['wide.css']
