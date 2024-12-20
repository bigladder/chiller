from typing import Type
from copy import deepcopy

from koozie import to_u, fr_u

from ..chiller import (
    Chiller,
    LiquidCooledChiller,
    CondenserType,
    AirCooledChiller,
    AHRI_550_590_AIR_COOLED_CONDITIONS,
    AHRI_550_590_LIQUID_COOLED_CONDITIONS,
    AHRI_550_590_LIQUID_COOLED_CONDENSER_OUTLET,
    OperatingConditions,
)
from ..util import calc_biquad, calc_cubic


class EnergyPlusEIR(Chiller):
    def __init__(
        self,
        rated_net_evaporator_capacity,
        rated_cop,
        condenser_type: CondenserType,
        eir_temperature_coefficients,
        eir_part_load_ratio_coefficients,
        capacity_temperature_coefficients,
        minimum_part_load_ratio,
        minimum_unloading_ratio,
        cycling_degradation_coefficient=0.0,
        standby_power=0.0,
        space_gain_fraction=0.0,
        oil_cooler_fraction=0.0,
        auxiliary_fraction=0.0,
    ) -> None:
        self.capacity_temperature_coefficients = capacity_temperature_coefficients
        self.eir_temperature_coefficients = eir_temperature_coefficients
        self.eir_part_load_ratio_coefficients = eir_part_load_ratio_coefficients
        self.minimum_part_load_ratio = minimum_part_load_ratio
        self.minimum_unloading_ratio = minimum_unloading_ratio
        self.oil_cooler_fraction = oil_cooler_fraction
        self.auxiliary_fraction = auxiliary_fraction
        self.space_gain_fraction = space_gain_fraction

        # Check for sum of fractions > 1.0
        self.loss_fraction_sum = (
            self.oil_cooler_fraction
            + self.auxiliary_fraction
            + self.space_gain_fraction
        )

        if self.loss_fraction_sum > 1.0001:
            raise RuntimeError(
                f"Sum of 'oil_cooler_fraction' ({self.oil_cooler_fraction}), 'auxiliary_fraction' ({self.auxiliary_fraction}), and 'space_gain_fraction' ({self.space_gain_fraction}) is greater than 1.0 ({self.loss_fraction_sum})"
            )

        if self.minimum_unloading_ratio < self.minimum_part_load_ratio:
            raise RuntimeError(
                f"'minimum_unloading_ratio' ({self.minimum_unloading_ratio}) must be greater than 'minimum_part_load_ratio' ({self.minimum_part_load_ratio})"
            )

        energy_balance = rated_net_evaporator_capacity * (1.0 / rated_cop + 1.0)
        rated_net_condenser_capacity = energy_balance * (1.0 - self.loss_fraction_sum)

        if self.minimum_unloading_ratio > self.minimum_part_load_ratio:
            number_of_compressor_speeds = 5
        else:
            number_of_compressor_speeds = 4

        self.has_hot_gas_bypass_installed = (
            self.minimum_part_load_ratio < self.minimum_unloading_ratio
        )

        self.chiller_type: Type[Chiller]
        if condenser_type == CondenserType.LIQUID:
            self.chiller_type = LiquidCooledChiller
            self.rated_operating_conditions = deepcopy(
                AHRI_550_590_LIQUID_COOLED_CONDITIONS
            )
        else:
            self.chiller_type = AirCooledChiller
            self.rated_operating_conditions = deepcopy(
                AHRI_550_590_AIR_COOLED_CONDITIONS
            )

        super().__init__(
            rated_net_evaporator_capacity=rated_net_evaporator_capacity,
            rated_cop=rated_cop,
            condenser_type=condenser_type,
            rated_net_condenser_capacity=rated_net_condenser_capacity,
            number_of_compressor_speeds=number_of_compressor_speeds,
            condenser_entering_temperature_range=self.chiller_type.DEFAULT_CONDENSER_TEMPERATURE_RANGE,
            cycling_degradation_coefficient=cycling_degradation_coefficient,
            standby_power=standby_power
        )

        if condenser_type == CondenserType.LIQUID:
            self.rated_condenser_outlet_state = (
                AHRI_550_590_LIQUID_COOLED_CONDENSER_OUTLET
            )
            self.set_rated_condenser_volumetric_flow_rate()

    def net_evaporator_capacity(self, conditions=None):
        if conditions is None:
            conditions = self.rated_operating_conditions
        coeffs = self.capacity_temperature_coefficients
        capacity_temperature_multiplier = calc_biquad(
            coeffs,
            to_u(conditions.evaporator_outlet.T, "°C"),
            to_u(conditions.condenser_inlet.T, "°C"),
        )
        return (
            self.rated_net_evaporator_capacity
            * capacity_temperature_multiplier
            * self.part_load_ratio(conditions)
        )

    def input_power(self, conditions=None):
        if conditions is None:
            conditions = self.rated_operating_conditions
        cap = self.net_evaporator_capacity(conditions)
        coeffs = self.eir_temperature_coefficients
        eir_temperature_multplier = calc_biquad(
            coeffs,
            to_u(conditions.evaporator_outlet.T, "°C"),
            to_u(conditions.condenser_inlet.T, "°C"),
        )
        plr = self.part_load_ratio(conditions)
        if plr < self.minimum_unloading_ratio:
            effective_plr = self.minimum_unloading_ratio
        else:
            effective_plr = plr
        eir_part_load_ratio_multiplier = calc_cubic(
            self.eir_part_load_ratio_coefficients, effective_plr
        )
        eir = (
            eir_temperature_multplier * eir_part_load_ratio_multiplier / self.rated_cop
        )
        return eir * cap / self.part_load_ratio(conditions)

    def net_condenser_capacity(self, conditions=None):
        if conditions is None:
            conditions = self.rated_operating_conditions
        return (
            self.input_power(conditions) + self.net_evaporator_capacity(conditions)
        ) * (1.0 - self.loss_fraction_sum)

    def oil_cooler_heat(self, conditions=None):
        if conditions is None:
            conditions = self.rated_operating_conditions
        return (
            self.input_power(conditions) + self.net_evaporator_capacity(conditions)
        ) * self.oil_cooler_fraction

    def auxiliary_heat(self, conditions=None):
        if conditions is None:
            conditions = self.rated_operating_conditions
        return (
            self.input_power(conditions) + self.net_evaporator_capacity(conditions)
        ) * self.auxiliary_fraction

    def part_load_ratio(self, conditions=None):
        if conditions is None:
            conditions = self.rated_operating_conditions
        if self.minimum_part_load_ratio < self.minimum_unloading_ratio:
            minimum_speed = self.number_of_compressor_speeds - 2
        else:
            minimum_speed = self.number_of_compressor_speeds - 1
        if conditions.compressor_speed > minimum_speed:
            # Unloading / false loading / hot gas bypass
            return self.minimum_part_load_ratio
        else:
            return (
                self.minimum_unloading_ratio
                + (1.0 - self.minimum_unloading_ratio)
                * (minimum_speed - conditions.compressor_speed)
                / minimum_speed
            )

    def condenser_air_volumetric_flow_rate(
        self, conditions: OperatingConditions | None = None
    ) -> float:
        if self.condenser_type != CondenserType.LIQUID:
            return AirCooledChiller.condenser_air_volumetric_flow_rate(self, conditions)
        else:
            raise RuntimeError(f"Function not provided for this type of condenser.")

    def evaporation_rate(self, conditions: OperatingConditions | None = None) -> float:
        if self.condenser_type != CondenserType.LIQUID:
            return AirCooledChiller.evaporation_rate(self, conditions)
        else:
            raise RuntimeError(f"Function not provided for this type of condenser.")

    def set_rated_evaporator_volumetric_flow_rate(self):
        self.chiller_type.set_rated_evaporator_volumetric_flow_rate(self)

    def set_rated_condenser_volumetric_flow_rate(self):
        if self.condenser_type == CondenserType.LIQUID:
            LiquidCooledChiller.set_rated_condenser_volumetric_flow_rate(self)

    def make_performance_map(self):
        return self.chiller_type.make_performance_map(self)
