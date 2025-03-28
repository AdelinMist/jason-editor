from pydantic import field_validator, Field, BaseModel
import data_plugins as dp
    
class LinuxMachine(BaseModel):
    __icon: str = ':material/ac_unit:'
    
    #__json_schema_template_name: str = 'linux_machine.jinja'
    
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