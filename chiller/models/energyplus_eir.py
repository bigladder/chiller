
from .base_model import ChillerModel
from ..util import calc_biquad, calc_cubic
from koozie import to_u

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
    self.allowed_kwargs.update({
      "oil_cooler_fraction": 0.0,
      "auxiliary_fraction": 0.0,
      "space_gain_fraction": 0.0
    })

  def set_system(self, system):
    super().set_system(system)
    # set kwarg variables
    self.capacity_temperature_coefficients = self.system.kwargs["capacity_temperature_coefficients"]
    self.eir_temperature_coefficients = self.system.kwargs["eir_temperature_coefficients"]
    self.eir_part_load_ratio_coefficients = self.system.kwargs["eir_part_load_ratio_coefficients"]
    self.minimum_part_load_ratio = self.system.kwargs["minimum_part_load_ratio"]
    self.minimum_unloading_ratio = self.system.kwargs["minimum_unloading_ratio"]

    self.oil_cooler_fraction = self.system.kwargs["oil_cooler_fraction"]
    self.auxiliary_fraction = self.system.kwargs["auxiliary_fraction"]
    self.space_gain_fraction = self.system.kwargs["space_gain_fraction"]

    # Check for sum of fractions > 1.0
    self.loss_fraction_sum = self.oil_cooler_fraction + self.auxiliary_fraction + self.space_gain_fraction

    if self.loss_fraction_sum > 1.0001:
      raise Exception(f"Sum of 'oil_cooler_fraction' ({self.oil_cooler_fraction}), 'auxiliary_fraction' ({self.auxiliary_fraction}), and 'space_gain_fraction' ({self.space_gain_fraction}) is greater than 1.0 ({self.loss_fraction_sum})")

    if self.minimum_unloading_ratio < self.minimum_part_load_ratio:
      raise Exception(f"'minimum_unloading_ratio' ({self.minimum_unloading_ratio}) must be greater than 'minimum_part_load_ratio' ({self.minimum_part_load_ratio})")

    if self.system.number_of_compressor_speeds is None:
      if self.minimum_unloading_ratio > self.minimum_part_load_ratio:
        self.system.number_of_compressor_speeds = 5
      else:
        self.system.number_of_compressor_speeds = 4
    if self.system.rated_net_condenser_capacity is None:
      energy_balance = self.system.rated_net_evaporator_capacity*(1./self.system.rated_cop + 1.)
      self.system.rated_net_condenser_capacity = energy_balance*(1. - self.loss_fraction_sum)

    self.system.metadata.has_hot_gas_bypass_installed = self.minimum_part_load_ratio < self.minimum_unloading_ratio


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
    return eir*cap/self.part_load_ratio(conditions)

  def net_condenser_capacity(self, conditions):
    return (self.input_power(conditions) + self.net_evaporator_capacity(conditions))*(1. - self.loss_fraction_sum)

  def oil_cooler_heat(self, conditions):
    return (self.input_power(conditions) + self.net_evaporator_capacity(conditions))*self.oil_cooler_fraction

  def auxiliary_heat(self, conditions):
    return (self.input_power(conditions) + self.net_evaporator_capacity(conditions))*self.auxiliary_fraction

  def part_load_ratio(self, conditions):
    if self.minimum_part_load_ratio < self.minimum_unloading_ratio:
      minimum_speed = self.system.number_of_compressor_speeds - 2
    else:
      minimum_speed = self.system.number_of_compressor_speeds - 1
    if conditions.compressor_speed > minimum_speed:
      # Unloading / false loading / hot gas bypass
      return self.minimum_part_load_ratio
    else:
      return self.minimum_unloading_ratio + (1.0 - self.minimum_unloading_ratio)*(minimum_speed - conditions.compressor_speed)/minimum_speed

  def generate_energyplus_idf(self,output_path, indent=2):

    with open(output_path, "w") as file:
      file.write(
      )
