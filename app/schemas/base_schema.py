from marshmallow import Schema, pre_load

class BaseSchema(Schema):
    """Base schema for data validation, to be extended by other schemas."""

    @pre_load
    def remove_empty_values(self, data, **kwargs):
        """Removes keys with None or empty string values from incoming data."""
        if data is None:
            return {}
        return {k: v for k, v in data.items() if v is not None and v != ""}
