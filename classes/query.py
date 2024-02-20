import json


class Query:
    def __init__(self, medicines: list[int], side_effects: list[int], encrypted_m: str) -> None:
        self.medicines = medicines
        self.side_effects = side_effects
        self.encrypted_m = encrypted_m

    @classmethod
    def deserialize(cls, serialized_query: str) -> "Query":
        """
        This class method is used to recreate a query object from the serialized POST
        data sent to the server.
        """

        data = json.loads(serialized_query)

        return cls(
            medicines=data["medicines"],
            side_effects=data["side_effects"],
            encrypted_m=data["encrypted_m"],
        )

    def serialize(self) -> str:
        """
        Serializes the query object into string using json library
        """

        return json.dumps(
            {
                "medicines": self.medicines,
                "side_effects": self.side_effects,
                "encrypted_m": self.encrypted_m,
            }
        )
