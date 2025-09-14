def is_deleted_filter(alias=None):
    """
    Returns the SQL snippet to filter out soft-deleted rows.
    alias: optional table alias (default None)
    """
    if alias:
        return f"{alias}.deleted_at IS NULL", []
    return "deleted_at IS NULL", []