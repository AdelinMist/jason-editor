import enum
import os, sys
import importlib
from logger import logger

def import_from_path(module_name, file_path):
    """Import a module given its name and file path."""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

def create_variable(name, value):
    """Creates a variable, dynamically, given name and value."""
    globals()[name] = value
    
file_path = os.path.abspath(os.path.dirname(__file__))
data_module_dir = f"{file_path}/data_plugins"
directory = os.fsencode(data_module_dir)

for file in os.listdir(directory):
    filename = os.fsdecode(file)
    if filename.endswith(".py"): 
        try:
            filename_stripped = filename.replace(".py","")
            data_module = import_from_path(filename_stripped, f"{data_module_dir}/{filename}")
            data_values = data_module.main()
            data_dict = {f"{val}": val for val in data_values}
            data_enum = enum.Enum(filename_stripped, data_dict)
            create_variable(filename_stripped.capitalize(), data_enum)
        except Exception as err:
            logger.error(f"Couldn't get data from data plugin named {filename}.\nThe error was: {err}.")
            raise ValueError(f"Couldn't get data from data plugin named {filename}.\nThe error was: {err}.")
    else:
        continue