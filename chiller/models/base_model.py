class ChillerModel:
    def __init__(self):
        self.system = None
        self.allowed_kwargs = {}
        self.required_kwargs = []
        self.maximum_scaled_rated_capacity = None
        self.minimum_scaled_rated_capacity = None

    def set_system(self, system):
        self.system = system
        for kwarg in system.kwargs:
            if kwarg not in self.allowed_kwargs and kwarg not in self.required_kwargs:
                raise Exception(f"Unrecognized key word argument: {kwarg}")
        for kwarg in self.required_kwargs:
            if kwarg not in system.kwargs:
                raise Exception(f"Required key word argument not provided: {kwarg}")
        # Apply defaults
        for kwarg in self.allowed_kwargs:
            if kwarg not in system.kwargs:
                system.kwargs[kwarg] = self.allowed_kwargs[kwarg]

    def net_evaporator_capacity(self, conditions):
        raise NotImplementedError()

    def input_power(self, conditions):
        raise NotImplementedError

    def net_condenser_capacity(self, conditions):
        raise NotImplementedError()

    def oil_cooler_heat(self, conditions):
        raise NotImplementedError()

    def auxiliary_heat(self, conditions):
        raise NotImplementedError()

    def fixup_205_representation(self, representation):
        return representation
