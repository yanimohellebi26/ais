import importlib
import pkgutil
import inspect

import etl.extract
import etl.transform
import etl.load

FUNC_REGISTRY = {}

def register_functions_from_module(module):
    """"
    Browse modul and submodules and register function in FUNC_REGISTRY
    """

    for _, modname, ispkg in pkgutil.walk_packages(module.__path__, module.__name__ + "."):
        if not ispkg:
            submod = importlib.import_module(modname)
            for name, obj in inspect.getmembers(submod):
                if inspect.isfunction(obj):
                    FUNC_REGISTRY[name] = obj

for m in [etl.extract, etl.transform, etl.load]:
    register_functions_from_module(m)
