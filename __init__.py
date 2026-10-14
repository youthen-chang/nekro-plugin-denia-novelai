import sys

for _stale in [name for name in sys.modules if name.startswith(f"{__name__}.")]:
    sys.modules.pop(_stale, None)

plugin = None
# Standalone test collection can import this file as a top-level module when
# the Git checkout name contains hyphens. NekroAgent loads it as a package.
if __package__:
    try:
        from .plugin import plugin
    except ModuleNotFoundError as exc:
        optional_runtime_modules = ("nekro_agent", "httpx")
        if not (exc.name or "").startswith(optional_runtime_modules):
            raise

__all__ = ["plugin"]
