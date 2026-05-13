def make_field(klass, operation, value, prev_op="and"):
    return {"field": str(klass.label), "operator": str(operation), "value": value, "prev_op": prev_op}
