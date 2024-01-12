import json

class Query:
    def __init__(self, medicine: list[int], side_effects: list[int], encrypted_m: str) -> None:
        self.medicine = medicine
        self.side_effects = side_effects
        self.encrypted_m = encrypted_m

    @classmethod
    def deserialize(cls, serialized_query: str) -> 'Query':
        data = json.loads(serialized_query)

        return cls(
            medicine=data['medicine'],
            side_effects=data['side_effects'],
            encrypted_m=data['encrypted_m']
        )

    def serialize(self) -> str:
        return json.dumps({
            "medicine": self.medicine,
            "side_effects": self.side_effects,
            "encrypted_m": self.encrypted_m
        })

