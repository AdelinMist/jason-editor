# platform-ui

A simple ui for the platform project!

## Installation

Clone the repo and build the image!

## Usage
This application was created with modularity in mind! Each validation class will be made into a new page in the editor, with its own validation based on the class already defined, please see below for more information and an example!

You should build the image and add the data plugins and the validation classes to the image with volume mounts.

This application has the following plugin capabilities:
- Json Schema Templates:
    These are Jinja2 based templates for each object.
    In these files we can use the values we defined in the validation classes, to get the json object we want!
    All the template file need to be in the json_schema_templates folder.
    The files of the template should be named exactly as the validation class name you want to use it with.
    You can also specify the attribute __json_schema_template_name in the class to select a different template.
    Should the program fail to find any template file, the json will be based on the validation class attributes only (the columns).
    For example (notice the {{}} jinja2 variable access):
    ```python
    {
        "metadata": {
            "fqdn": "{{hostname}}.{{domain}}"
        },
        "spec": {
            "hostname": "{{hostname}}",
            "ipaddress": "{{ipaddress}}",
            "datacenter": "{{datacenter}}",
            "island": "{{island}}",
            "domain": "{{domain}}"
        }
    }
    ```
- Data Plugins:
    These are simple python files, with a main fucntion that should return the wanted values for a selectbox type field in the json editor.
    Each data plugin should return a dictionary with the values, each different key will be made into a different enum.
    The values of the dictionary need to be lists of the wanted enum values.
    Each file in the data_plugins folder will be used to make Enums (based on the dict it returns) that can be used in a validation class (will be explained later).
    In the example below, an Enum named Datacenter will be created with the values in the list.

    Simple example for a data plugin file (datacenters.py):
    ```python
    def main() -> dict:
        retDict = {'Datacenter': ['dc1', 'dc2', 'dc3', 'dc4', 'dc5']}
        return retDict
    ```
- Validation Classes:
    These are the actual types of object we want to edit, such as, linux machine, windows machine, mongo db, and so on...
    These need to be written in the pydantic format, and with pydantic we can add any validation logic we like!
    For example we could add an API call to the VMWare Vcenter, to see that we don't create an illegal machine.
    Here, we can use the data plugins from before to set a known set of values for a field, please see an example below.
    When an Enum is used, the editor automatically makes that field into a selectbox with the Enum values.
    This can be used to restrict the users to certain values!
    The __icon hidden attribute sets the icon in the sidebar of the application for the page with this specific edited object.
    The __json_schema_template_name hidden attribute sets name of the jinja2 template to use for the json object we download for this class.
    Both hidden attributes are OPTIONAL!
    The class must inherit from CustomBaseModel

    Simple example for a validation class file (windows_machine.py):

    ```python
    from pydantic import field_validator, Field, BaseModel
    from utils.validation import CustomBaseModel
    import data_plugins as dp
        
    class LinuxMachine(CustomBaseModel):
        __icon: str = ':material/ac_unit:'
        
        __json_schema_template_name: str = 'linux_machine.jinja'
        
        hostname: str = Field(description="The machine hostname.")  # the previous defined Enum class
        
        ipAddress: str = Field(description="The machine ip address.")

        domain: str = Field(description="The domain of the machine.",)
        
        datacenter: dp.Datacenter = Field(description="The datacenter of the machine.",)
        
        island: str = Field(description="The network island of the machine.",)

        @field_validator('hostname', mode='after')  
        @classmethod
        def is_valid_hostname(cls, value: str) -> str:
            if len(value) > 15:
                raise ValueError(f'{value} is not valid hostname!')
            return value 

        @field_validator('ipAddress', mode='after')  
        @classmethod
        def is_valid_ip_address(cls, value: str) -> str:
            return value 
        
        @field_validator('domain', mode='after')  
        @classmethod
        def is_valid_domain(cls, value: str) -> str:
            return value 
        
        @field_validator('datacenter', mode='after')  
        @classmethod
        def is_valid_datacenter(cls, value: str) -> str:
            return value 
        
        @field_validator('island', mode='after')  
        @classmethod
        def is_valid_island(cls, value: str) -> str:
            return value 
    ```


The application structure for plugins is:

```md
src/json_schema_templates
├── LinuxMachine.jinja
├── WindowsMachine.jinja
└── NoOsMachine.jinja
```

```md
src/data_plugins
├── datacenters.py
└── islands.py
```

```md
src/validation_classes 
├── linux_machine.py
├── no_os_machine.py
└── windows_machine.py
```

## Logs

This application doesn't write many logs, but the logger is defined in the 'logger.py' file.
Logs are written for an incorrect parsing of the data plugins and the validation classes.
The logs are written to the stdout and to a log file named 'logs.txt'.

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)