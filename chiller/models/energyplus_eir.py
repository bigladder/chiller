
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
      "min_plr"
    ]

  def set_system(self, system):
    super().set_system(system)
    self.system.number_of_compressor_speeds = 4

  def net_evaporator_capacity(self, conditions):
    coeffs = self.system.kwargs["cap_f_t"]
    evaporator_leaving_temperature = to_u(conditions.evaporator_outlet.T,"°C")
    condenser_leaving_temperature = to_u(conditions.condenser_inlet.T,"°C")
    cap_f_t = calc_biquad(coeffs, evaporator_leaving_temperature, condenser_leaving_temperature)
    return self.system.rated_net_evaporator_capacity*cap_f_t*self.part_load_ratio(conditions)

  def input_power(self, conditions):
    cap = self.net_evaporator_capacity(conditions)
    t_coeffs = self.system.kwargs["eir_f_t"]
    evaporator_leaving_temperature = to_u(conditions.evaporator_outlet.T,"°C")
    condenser_leaving_temperature = to_u(conditions.condenser_inlet.T,"°C")
    eir_f_t = calc_biquad(t_coeffs, evaporator_leaving_temperature, condenser_leaving_temperature)
    plr_coeffs = self.system.kwargs["eir_f_plr"]
    plr = self.part_load_ratio(conditions)
    eir_f_plr = calc_cubic(plr_coeffs, plr)
    eir = eir_f_t*eir_f_plr/self.system.rated_cop
    return eir*cap

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

