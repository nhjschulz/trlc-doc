# pylint: skip-file
# Additional project Sphinx configuration, executed at the end of the generated conf.py.

# Use the full window width with sphinx_rtd_theme (default max-width is 800px).
html_static_path.append(str(PROJECT_ROOT / 'doc' / 'sphinx' / '_static'))
html_css_files = ['wide.css']

autoapi_dirs = [str(PROJECT_ROOT / 'trlcdoc')]
autoapi_root = 'autoapi'
autoapi_add_toctree_entry = False
autoapi_options = ['members', 'undoc-members', 'show-inheritance', 'show-inheritance-diagram', 'show-module-summary']
autoapi_ignore = ['*/sphinx/conf.py']
#autoapi_ignore = ['*/sphinx/conf.py', '*/converters/*']

# sphinx.ext.inheritance_diagram configuration
# https://www.sphinx-doc.org/en/master/usage/extensions/inheritance.html
inheritance_graph_attrs = {
    'rankdir': 'TB',  # Top-to-bottom layout (use 'LR' for left-to-right)
    'size': '"8.0, 12.0"',
    'bgcolor': 'transparent',
}
inheritance_edge_attrs = {
    'arrowsize': '1.5',
}

# sphinx.ext.linkcode: link the [source] buttons of the API pages to the repository
# files at the built commit instead of copying the sources into the site (viewcode).
# trlcdoc provides the repository URL and commit in trlcdoc_links.
# https://www.sphinx-doc.org/en/master/usage/extensions/linkcode.html
import importlib
import inspect
from typing import Dict, Optional


def linkcode_resolve(domain: str, info: Dict[str, str]) -> Optional[str]:
    """Get the repository URL of the source code of a documented object.

    This version generates GitHub URLs for Python objects in the project,
    adapt return value for other repositories like GitLab or Bitbucket.

    Args:
        domain (str): Sphinx domain of the object, only 'py' is resolved.
        info (Dict[str, str]): Object description of the domain, for 'py' the
            'module' name and the 'fullname' of the object in the module.

    Returns:
        Optional[str]: URL of the object's source lines at the built commit, or None
            if the object has no Python source in the project or the repository
            or commit is not known.
    """
    repository = trlcdoc_links.get("repository")
    commit = trlcdoc_links.get("commit")
    if domain != "py" or not info.get("module") or not repository or not commit:
        return None

    try:
        obj = importlib.import_module(info["module"])
        for part in info["fullname"].split("."):
            obj = getattr(obj, part)
        obj = inspect.unwrap(obj)
        source_file = Path(inspect.getsourcefile(obj)).resolve()
        lines, start = inspect.getsourcelines(obj)
    except Exception:  # Not importable, no Python source (e.g. a constant), ...
        return None

    try:
        path = source_file.relative_to(PROJECT_ROOT.resolve()).as_posix()
    except ValueError:  # Object of an installed third party package.
        return None

    # Modules report line 0, they link to the whole file.
    anchor = "" if start == 0 else f"#L{start}-L{start + len(lines) - 1}"
    return f"{repository}/blob/{commit}/{path}{anchor}"