from .fluid_properties import FluidState
from .units import fr_u

class OperatingConditions:
  def __init__(self, condenser_inlet, evaporator_outlet, compressor_speed=0):
    self.condenser_inlet = condenser_inlet
    self.evaporator_outlet = evaporator_outlet
    self.compressor_speed = compressor_speed

AHRI_550_590_WATER_COOLED_CONDITIONS  = OperatingConditions(condenser_inlet=FluidState(fr_u(85.0,"°F")), evaporator_outlet=FluidState(fr_u(44.0,"°F")))

AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET = FluidState(fr_u(94.3,"°F"))

AHRI_550_590_WATER_COOLED_EVAPORATOR_INLET = FluidState(fr_u(54.0,"°F"))
