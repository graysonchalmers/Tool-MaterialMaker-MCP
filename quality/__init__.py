"""quality/: the cookbook factory.

Builder scripts that regenerate the tracked cookbook/ graphs
(cookbook_<category>.py), the shared graph-surgery helpers they use
(author_helpers.py, author.py), the promote/--check regression baseline,
render helpers, the diagnostic swatches, and the vendored PNG reader.
Importable as a package (`from quality.author_helpers import ...`); run
scripts as `python -m quality.<module>` from the repo root. Not shipped in
the wheel: these need Godot and a Material Maker checkout.
"""
