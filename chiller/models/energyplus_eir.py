
from .base_model import ChillerModel
from ..util import calc_biquad, calc_cubic
from ..units import to_u

class EnergyPlusEIR(ChillerModel):
  def __init__(self):
    super().__init__()
    self.allowed_kwargs += [
      "eir_f_t",
      "eir_f_plr",
      "cap_f_t",
      "min_plr",
      "min_unload"
    ]

  def set_system(self, system):
    super().set_system(system)
    # set kwarg variables
    if self.system.number_of_compressor_speeds is None:
      self.system.number_of_compressor_speeds = 4
    if self.system.rated_net_condenser_capacity is None:
      self.system.rated_net_condenser_capacity = self.system.rated_net_evaporator_capacity*(1./self.system.rated_cop + 1.)

  def net_evaporator_capacity(self, conditions):
    coeffs = self.system.kwargs["cap_f_t"]
    cap_f_t = calc_biquad(coeffs, to_u(conditions.evaporator_outlet.T,"°C"), to_u(conditions.condenser_inlet.T,"°C"))
    return self.system.rated_net_evaporator_capacity*cap_f_t*self.part_load_ratio(conditions)

  def input_power(self, conditions):
    cap = self.net_evaporator_capacity(conditions)
    coeffs = self.system.kwargs["eir_f_t"]
    eir_f_t = calc_biquad(coeffs, to_u(conditions.evaporator_outlet.T,"°C"), to_u(conditions.condenser_inlet.T,"°C"))
    plr = self.part_load_ratio(conditions)
    if plr < self.system.kwargs["min_unload"]:
      effective_plr = self.system.kwargs["min_unload"]
    else:
      effective_plr = plr
    eir_f_plr = calc_cubic(self.system.kwargs["eir_f_plr"], effective_plr)
    eir = eir_f_t*eir_f_plr/self.system.rated_cop
    return eir*cap/self.part_load_ratio(conditions)*effective_plr

  def net_condenser_capacity(self, conditions):
    return self.input_power(conditions) + self.net_evaporator_capacity(conditions)

  def oil_cooler_heat(self, conditions):
    return 0.0

  def auxiliary_heat(self, conditions):
    return 0.0

  def part_load_ratio(self, conditions):
    min_plr = self.system.kwargs["min_plr"]
    min_speed = self.system.number_of_compressor_speeds - 1
    return min_plr + (1.0 - min_plr)*(min_speed - conditions.compressor_speed)/min_speed

