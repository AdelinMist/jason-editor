# jason-editor

A simple json editor with validation, created with streamlit.

## Installation

Clone the repo and build the image!

## Usage
This application was created with modularity in mind! Each validation class will be made into a new page in the editor, with its own validation based on the class already defined, please see below for more information and an example!

You should build the image and add the data plugins and the validation classes to the image with volume mounts.

This application has the following plugin capabilities:
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

    Simple example for a validation class file (windows_machine.py):

    ```python
    from pydantic import field_validator, Field, BaseModel
    from typing import Annotated
    import data_plugins as dp

    class WindowsMachine(BaseModel):
        __icon: str = ':material/sword_rose:'
        
        hostname: str = Field(description="The machine hostname.")
        
        ipAddress: str = Field(description="The machine ip address.")

        domain: str = Field(description="The domain of the machine.",)
        
        datacenter: dp.Datacenter = Field(description="The datacenter of the machine.",)  # the previously defined Enum class, from the data plugin
        
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

## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

[MIT](https://choosealicense.com/licenses/mit/)