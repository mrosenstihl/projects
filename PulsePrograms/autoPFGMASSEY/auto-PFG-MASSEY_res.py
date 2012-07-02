class ParameterSet:
    """
    From 
    http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/52308
    Alex Martelli
    """
    def __init__(self, **kwds):
        self.__dict__.update(kwds)

def result():
    for res in results:
        if not isinstance(res, ADC_Result):
            print "ERROR:", res
            continue
        descriptions = res.get_description_dictionary()
        # rebuild the dictionary because __init__ can't take unicode keys
        temp_description={}
        for key in descriptions:
            temp_description[str(key)] = descriptions[key]
        descriptions=temp_description
        desc = ParameterSet(**descriptions)
        data["test"] = res