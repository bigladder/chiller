from .fluid_properties import LiquidState
from .psychrometrics import PsychrometricState
from koozie import fr_u


class OperatingConditions:
    def __init__(
        self,
        condenser_inlet: LiquidState | PsychrometricState,
        evaporator_outlet,
        compressor_speed=0,
    ):
        self.condenser_inlet = condenser_inlet
        self.evaporator_outlet = evaporator_outlet
        self.compressor_speed = compressor_speed


AHRI_550_590_LIQUID_COOLED_CONDITIONS = OperatingConditions(
    condenser_inlet=LiquidState(fr_u(85.0, "°F")),
    evaporator_outlet=LiquidState(fr_u(44.0, "°F")),
)

AHRI_550_590_AIR_COOLED_CONDITIONS = OperatingConditions(
    condenser_inlet=PsychrometricState(fr_u(95.0, "°F"), wetbulb=fr_u(75.0, "°F")),
    evaporator_outlet=LiquidState(fr_u(44.0, "°F")),
)

AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET = LiquidState(fr_u(94.3, "°F"))

AHRI_550_590_EVAPORATOR_INLET = LiquidState(fr_u(54.0, "°F"))
