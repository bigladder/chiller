
from re import T
from chiller.fluid_properties import FluidState
from .energyplus_eir import EnergyPlusEIR
from ..util import calc_biquad, calc_bicubic
from ..units import to_u
from scipy import optimize

class EnergyPlusReformulatedEIR(EnergyPlusEIR):
  def __init__(self):
    super().__init__()
    self.condenser_leaving_temperature = None

  def net_evaporator_capacity(self, conditions):
    guess_capacity = self.system.rated_net_evaporator_capacity*self.part_load_ratio(conditions)
    guess_condenser_leaving_temperature = conditions.condenser_inlet.add_heat(guess_capacity).T
    self.condenser_leaving_temperature = optimize.newton(lambda x : self.calculate_condenser_capacity(conditions, x) - self.calculate_heat_added(conditions, x), guess_condenser_leaving_temperature)
    return self.calculate_evaporator_capacity(conditions, self.condenser_leaving_temperature)

  def input_power(self, conditions):
    cap = self.net_evaporator_capacity(conditions)
    coeffs = self.eir_temperature_coefficients
    eir_temperature_multiplier = calc_biquad(coeffs, to_u(conditions.evaporator_outlet.T,"°C"), to_u(self.condenser_leaving_temperature,"°C"))
    plr = self.part_load_ratio(conditions)
    eir_part_load_ratio_multiplier = calc_bicubic(self.eir_part_load_ratio_coefficients, to_u(self.condenser_leaving_temperature,"°C"), plr)
    eir = eir_temperature_multiplier*eir_part_load_ratio_multiplier/self.system.rated_cop
    return eir*cap

  def calculate_evaporator_capacity(self, conditions, condenser_leaving_temperature):
    capacity_temperature_multiplier = calc_biquad(self.capacity_temperature_coefficients, to_u(conditions.evaporator_outlet.T,"°C"), to_u(condenser_leaving_temperature,"°C"))
    return self.system.rated_net_evaporator_capacity*capacity_temperature_multiplier*self.part_load_ratio(conditions)

  def calculate_condenser_capacity(self, conditions, condenser_leaving_temperature):
    evaporator_capacity = self.calculate_evaporator_capacity(conditions, condenser_leaving_temperature)
    coeffs = self.eir_temperature_coefficients
    eir_temperature_multiplier = calc_biquad(coeffs, to_u(conditions.evaporator_outlet.T,"°C"), to_u(condenser_leaving_temperature,"°C"))
    plr = self.part_load_ratio(conditions)
    eir_part_load_ratio_multiplier = calc_bicubic(self.eir_part_load_ratio_coefficients, to_u(condenser_leaving_temperature,"°C"), plr)
    eir = eir_temperature_multiplier*eir_part_load_ratio_multiplier/self.system.rated_cop
    power = eir*evaporator_capacity
    return evaporator_capacity + power

  def calculate_heat_added(self, conditions, condenser_leaving_temperature):
    condenser_leaving_state = FluidState(temperature=condenser_leaving_temperature, mass_flow_rate=conditions.condenser_inlet.m_dot)
    return condenser_leaving_state.get_heat(conditions.condenser_inlet)

