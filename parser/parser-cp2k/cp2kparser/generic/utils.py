#===============================================================================
def try_to_add_value(backend, section, source_name, destination_name):
    original = section[source_name]
    if original is not None:
        backend.addValue(destination_name, original[0])


#===============================================================================
def try_to_add_array_values(backend, section, source_name, destination_name, unit=None):
    original = section[source_name]
    if original is not None:
        backend.addArrayValues(destination_name, original[0])
