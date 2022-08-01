
from .base_model import ChillerModel
from ..util import calc_biquad, calc_cubic
from ..units import to_u

class EnergyPlusEIR(ChillerModel):
  def __init__(self):
    super().__init__()
    self.required_kwargs += [
      "eir_temperature_coefficients",
      "eir_part_load_ratio_coefficients",
      "capacity_temperature_coefficients",
      "minimum_part_load_ratio",
      "minimum_unloading_ratio"
    ]

  def set_system(self, system):
    super().set_system(system)
    # set kwarg variables
    self.capacity_temperature_coefficients = self.system.kwargs["capacity_temperature_coefficients"]
    self.eir_temperature_coefficients = self.system.kwargs["eir_temperature_coefficients"]
    self.eir_part_load_ratio_coefficients = self.system.kwargs["eir_part_load_ratio_coefficients"]
    self.minimum_part_load_ratio = self.system.kwargs["minimum_part_load_ratio"]
    self.minimum_unloading_ratio = self.system.kwargs["minimum_unloading_ratio"]
    if self.system.number_of_compressor_speeds is None:
      self.system.number_of_compressor_speeds = 4
    if self.system.rated_net_condenser_capacity is None:
      self.system.rated_net_condenser_capacity = self.system.rated_net_evaporator_capacity*(1./self.system.rated_cop + 1.)

  def net_evaporator_capacity(self, conditions):
    coeffs = self.capacity_temperature_coefficients
    capacity_temperature_multiplier = calc_biquad(coeffs, to_u(conditions.evaporator_outlet.T,"°C"), to_u(conditions.condenser_inlet.T,"°C"))
    return self.system.rated_net_evaporator_capacity*capacity_temperature_multiplier*self.part_load_ratio(conditions)

  def input_power(self, conditions):
    cap = self.net_evaporator_capacity(conditions)
    coeffs = self.eir_temperature_coefficients
    eir_temperature_multplier = calc_biquad(coeffs, to_u(conditions.evaporator_outlet.T,"°C"), to_u(conditions.condenser_inlet.T,"°C"))
    plr = self.part_load_ratio(conditions)
    if plr < self.minimum_unloading_ratio:
      effective_plr = self.minimum_unloading_ratio
    else:
      effective_plr = plr
    eir_part_load_ratio_multiplier = calc_cubic(self.eir_part_load_ratio_coefficients, effective_plr)
    eir = eir_temperature_multplier*eir_part_load_ratio_multiplier/self.system.rated_cop
    return eir*cap/self.part_load_ratio(conditions)*effective_plr

  def net_condenser_capacity(self, conditions):
    return self.input_power(conditions) + self.net_evaporator_capacity(conditions)

  def oil_cooler_heat(self, conditions):
    return 0.0

  def auxiliary_heat(self, conditions):
    return 0.0

  def part_load_ratio(self, conditions):
    min_speed = self.system.number_of_compressor_speeds - 1
    return self.minimum_part_load_ratio + (1.0 - self.minimum_part_load_ratio)*(min_speed - conditions.compressor_speed)/min_speed

