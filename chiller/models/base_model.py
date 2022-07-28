class ChillerModel:
  def __init__(self):
    self.system = None
    self.allowed_kwargs = []

  def set_system(self, system):
    self.system = system
    for kwarg in system.kwargs:
      if kwarg not in self.allowed_kwargs:
        raise Exception(f"Unrecognized key word argument: {kwarg}")

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
