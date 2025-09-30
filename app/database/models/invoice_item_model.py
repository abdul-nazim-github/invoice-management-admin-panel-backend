from .base_model import BaseModel
from app.database.db_manager import DBManager

class InvoiceItem(BaseModel):
    _table_name = 'invoice_items'

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def find_by_invoice_id(cls, invoice_id):
        query = f"SELECT * FROM {cls._table_name} WHERE invoice_id = %s"
        params = (invoice_id,)
        rows = DBManager.execute_read_query(query, params)
        return [cls.from_row(row) for row in rows]

    @classmethod
    def delete_by_invoice_id(cls, invoice_id):
        query = f"DELETE FROM {cls._table_name} WHERE invoice_id = %s"
        params = (invoice_id,)
        DBManager.execute_write_query(query, params)
