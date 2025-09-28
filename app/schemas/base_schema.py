from marshmallow import Schema, post_dump
from app.database.db_manager import normalize_row

class BaseSchema(Schema):
    """Base schema with common post-dump data normalization."""
    
    @post_dump
    def normalize_data(self, data, **kwargs):
        """
        After serializing, run the whole dictionary through the central
        database normalizer to handle types like Decimal and datetime.
        """
        # The `normalize_row` function from db_manager is expecting a dictionary
        # similar to a database row, and our serialized `data` fits that structure.
        if data:
            return normalize_row(data)
        return data
