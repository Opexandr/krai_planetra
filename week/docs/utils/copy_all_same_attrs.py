def copy_all_same_attrs(obj_for_record, obj_copy_from):
    for atr in obj_for_record.__dict__:
        if hasattr(obj_copy_from, atr):
            obj_for_record.__setattr__(atr, obj_copy_from.__getattribute__(atr))
