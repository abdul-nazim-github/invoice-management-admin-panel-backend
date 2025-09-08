class OutOfStockError(Exception):
    def __init__(self, product_id, message="Not enough stock"):
        self.product_id = product_id
        super().__init__(message)
