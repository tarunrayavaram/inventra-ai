"""Python 3.14 + Pydantic compatibility patch.

Pydantic (up to 2.14.x) adds ``vars(model_class)`` to the locals namespace when
evaluating type annotations.  On Python 3.14 this causes class methods like
``dict()`` (added by Pydantic itself to BaseModel) to shadow the builtin ``dict``,
so an annotation like ``Optional[dict[str, Any]]`` raises::

    TypeError: 'function' object is not subscriptable

The fix is to strip Python builtin names from the class vars before they are used
as the locals namespace for annotation evaluation.

Import this module before any ``langchain`` / pydantic model import.
"""
import sys

if sys.version_info >= (3, 14):
    try:
        import builtins as _builtins
        import pydantic._internal._namespace_utils as _nu

        _builtin_names = frozenset(dir(_builtins))

        # Patch the cached_property by replacing it with a wrapper that filters
        # builtin names out of vars(typ) before they become annotation-eval locals.
        _orig_tp = _nu.NsResolver.__dict__["types_namespace"]

        class _PatchedTypesNamespace:
            """Descriptor that wraps the original cached_property."""

            def __set_name__(self, owner, name):
                self._name = name

            def __get__(self, obj, objtype=None):
                if obj is None:
                    return self
                # Check instance cache first (mimicking cached_property behaviour)
                try:
                    return obj.__dict__[self._name]
                except KeyError:
                    pass

                # Call the original to get the NamespacesTuple
                result = _orig_tp.__get__(obj, objtype)

                # Unwrap and re-wrap with filtered locals
                from pydantic._internal._namespace_utils import (
                    NamespacesTuple,
                    LazyLocalNamespace,
                )
                globalns = result.globals
                orig_locals = result.locals

                # Walk through all namespaces in LazyLocalNamespace and filter
                if isinstance(orig_locals, LazyLocalNamespace):
                    filtered_ns = []
                    for ns in orig_locals._namespaces:
                        # Filter out entries whose keys shadow builtins
                        if hasattr(ns, "items"):
                            ns = {k: v for k, v in ns.items()
                                  if k not in _builtin_names}
                        filtered_ns.append(ns)
                    result = NamespacesTuple(
                        globalns, LazyLocalNamespace(*filtered_ns)
                    )

                # Cache on the instance
                obj.__dict__[self._name] = result
                return result

        _patched = _PatchedTypesNamespace()
        _patched._name = "types_namespace"
        _nu.NsResolver.types_namespace = _patched  # type: ignore[assignment]

    except Exception:
        # If the patch can't be applied, carry on — the import may still fail
        # but at least startup is not broken.
        pass
