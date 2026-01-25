
class Singleton(type):
    _instances = {}
    def __call__(cls, *args):
        if cls not in cls._instances:
            # we have not every built an istance before. Build one now.
            instance =  super().__call__(*args)
            cls._instances[cls] = instance
        else:
            # here we are going to call the __init__ and maybe reinitialize
            if hasattr(cls, '__allow_reinitialization') and cls.__allow_reinitialization:
                # if the class allows reinitialization, then do it
                instance.__init__(*args) # call the init again
        return instances
