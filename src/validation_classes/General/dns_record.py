from pydantic import field_validator, Field, BaseModel

class DnsRecord(BaseModel):
    __icon: str = ':material/sword_rose:'
    
    hostname: str = Field(description="The machine hostname.")  # the previous defined Enum class
    
    ipAddress: str = Field(description="The machine ip address.")

    dns_zone: str = Field(description="The dns zone of the record.",)

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
    
    @field_validator('dns_zone', mode='after')  
    @classmethod
    def is_valid_domain(cls, value: str) -> str:
        return value 
    