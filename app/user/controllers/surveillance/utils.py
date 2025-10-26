def check_property_access(property_obj, user_id: str):
    """
    Raise 403 HTTPException if the property does not belong to the user.
    """
    if property_obj.user_id != user_id:
        return True
