import enum
import os, sys
import importlib
import inspect
from logger import logger

def import_from_path(module_name, file_path):
    """Import a module given its name and file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
    
file_path = os.path.abspath(os.path.dirname(__file__))
validation_module_dir = f"{file_path}/validation_classes"
directory = os.fsencode(validation_module_dir)

classes = []
for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".py"): 
        try:
            filename_stripped = filename.replace(".py","")
            validation_module = import_from_path(filename_stripped, f"{validation_module_dir}/{filename}")
            module_classes = [{'name': cls_name, 'obj': cls_obj} for cls_name, cls_obj in inspect.getmembers(validation_module) if inspect.isclass(cls_obj) and cls_obj.__module__ == validation_module.__name__]
            classes.append(*module_classes)
        except Exception as err:
            logger.error(f"Couldn't get validation classes from validation plugin named {filename}.\nThe error was: {err}.")
            raise ValueError(f"Couldn't get validation classes from validation plugin named {filename}.\nThe error was: {err}.")
    else:
        continue