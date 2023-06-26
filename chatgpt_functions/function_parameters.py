from dataclasses import dataclass


@dataclass(init=False)
class Property:
    kwargs = []

    def __init__(self, property_name: str, prop_type: str, description: str, **kwargs):
        self.property_name = property_name
        self.prop_type = prop_type
        self.description = description
        self.kwargs = kwargs

    property_name: str
    prop_type: str
    description: str


class Parameters:
    result_properties: dict = {}
    result_required: list = []

    def __init__(
        self, properties: list[Property], required: list | bool = True
    ) -> None:
        self.properties = properties
        self.required = required

    def prepare(self) -> dict:
        for prop in self.properties:
            self.result_properties[prop.property_name] = {
                "type": prop.prop_type,
                "description": prop.description,
            }
            for key, value in prop.kwargs.items():
                self.result_properties[prop.property_name][key] = value
        if self.required == True:
            self.result_required = [prop.property_name for prop in self.properties]

        return {
            "type": "object",
            "properties": self.result_properties,
            "required": self.result_required,
        }
