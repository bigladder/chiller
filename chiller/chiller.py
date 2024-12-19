from enum import Enum

from .fluid_properties import LiquidState
from .psychrometrics import PsychrometricState
from .conditions import (
    AHRI_550_590_LIQUID_COOLED_CONDITIONS,
    AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET,
    AHRI_550_590_EVAPORATOR_INLET,
    OperatingConditions,
)
from koozie import fr_u
from numpy import linspace
import uuid
import datetime
from random import Random


class CondenserType(Enum):
    LIQUID = 1
    AIR = 2
    EVAPORATIVE = 3


class CompressorType(Enum):
    UNKNOWN = 0
    CENTRIFUGAL = 1
    POSITIVE_DISPLACEMENT = 2
    SCREW = 3
    SCROLL = 4


class ChillerMetadata:
    def __init__(
        self,
        description="",
        data_source="https://github.com/bigladder/chiller",
        notes="",
        has_hot_gas_bypass_installed=False,
        uuid_seed=None,
        data_version=1,
    ):

        self.description = description
        self.data_source = data_source
        self.notes = notes
        self.has_hot_gas_bypass_installed = has_hot_gas_bypass_installed
        self.uuid_seed = uuid_seed
        self.data_version = data_version


class Chiller:
    DEFAULT_CONDENSER_TEMPERATURE_RANGE: tuple[float, float]

    def __init__(
        self,
        rated_net_evaporator_capacity=fr_u(100.0, "ton_ref"),
        rated_cop=2.0,
        cycling_degradation_coefficient=0.0,
        standby_power=0.0,
        rated_net_condenser_capacity=None,
        number_of_compressor_speeds=None,
        evaporator_leaving_temperature_range=(
            fr_u(39.0, "°F"),  # fr_u(36.0, "°F"),
            fr_u(60.0, "°F"),  # fr_u(70.0, "°F"),
        ),  # AHRI 550/590 2023 Table 5
        condenser_entering_temperature_range=None,
        condenser_type=CondenserType.LIQUID,
        compressor_type=CompressorType.UNKNOWN,
    ):

        self.number_of_compressor_speeds = number_of_compressor_speeds
        self.rated_net_condenser_capacity = rated_net_condenser_capacity
        self.rated_net_evaporator_capacity = rated_net_evaporator_capacity
        self.rated_cop = rated_cop
        self.cycling_degradation_coefficient = cycling_degradation_coefficient
        self.standby_power = standby_power

        self.condenser_type = condenser_type
        self.compressor_type = compressor_type

        self.evaporator_leaving_temperature_range = evaporator_leaving_temperature_range
        self.condenser_entering_temperature_range = condenser_entering_temperature_range

        self.set_rated_evaporator_volumetric_flow_rate()
        self.set_rated_condenser_volumetric_flow_rate()

        self.metadata = ChillerMetadata()

    # TODO: Apply pressure corrections per 550/590 Appendix C

    def net_evaporator_capacity(self, conditions):
        raise NotImplementedError()

    def input_power(self, conditions):
        raise NotImplementedError()

    def net_condenser_capacity(self, conditions):
        raise NotImplementedError()

    def oil_cooler_heat(self, conditions):
        raise NotImplementedError()

    def auxiliary_heat(self, conditions):
        raise NotImplementedError()

    def cop(self, conditions=None):
        if conditions is None:
            conditions = self.get_default_conditions()
        return self.net_evaporator_capacity(conditions) / self.input_power(conditions)

    def condenser_liquid_leaving_state(self, conditions):
        raise NotImplementedError()

    def evaporator_liquid_entering_state(self, conditions):
        return conditions.evaporator_outlet.add_heat(
            self.net_evaporator_capacity(conditions)
        )

    def space_loss_heat(self, conditions):
        return (
            self.input_power(conditions) + self.net_evaporator_capacity(conditions)
        ) - (
            self.net_condenser_capacity(conditions)
            + self.oil_cooler_heat(conditions)
            + self.auxiliary_heat(conditions)
        )

    def set_rated_evaporator_volumetric_flow_rate(self):
        raise NotImplementedError()

    def set_rated_condenser_volumetric_flow_rate(self):
        raise NotImplementedError()

    def get_default_conditions(self):
        if self.condenser_type == CondenserType.LIQUID:
            return AHRI_550_590_LIQUID_COOLED_CONDITIONS

    def generate_205_representation(
        self,
        capacity_range: tuple[float | None, float | None] = (None, None),
    ) -> dict:
        # Metadata
        timestamp = datetime.datetime.now().isoformat("T", "minutes")
        rnd = Random()
        if self.metadata.uuid_seed is None:
            self.metadata.uuid_seed = hash(self)
        rnd.seed(self.metadata.uuid_seed)
        unique_id = str(uuid.UUID(int=rnd.getrandbits(128), version=4))

        metadata = {
            "data_model": "ASHRAE_205",
            "schema": "RS0001",
            "schema_version": "2.0.0",
            "description": self.metadata.description,
            "id": unique_id,
            "data_timestamp": f"{timestamp}Z",
            "data_version": self.metadata.data_version,
            "data_source": self.metadata.data_source,
            "disclaimer": "This data is synthetic and does not represent any physical products.",
            "notes": self.metadata.notes,
        }
        representation_description = {
            "product_information": {
                "liquid_data_source": "CoolProp",
                "hot_gas_bypass_installed": self.metadata.has_hot_gas_bypass_installed,
                "compressor_type": self.compressor_type.name,
            }
        }

        performance_map_cooling = self.make_performance_map()

        evaporator_liquid_volumetric_flow_rates = performance_map_cooling[
            "grid_variables"
        ]["evaporator_liquid_volumetric_flow_rate"]
        evaporator_liquid_leaving_temperatures = performance_map_cooling[
            "grid_variables"
        ]["evaporator_liquid_leaving_temperature"]

        performance = {
            "condesner_type": self.condenser_type.name,
            "evaporator_liquid_type": {  # TODO: Make consistent with model
                "liquid_components": [
                    {
                        "liquid_constituent": "WATER",
                        "concentration": 1.0,
                    }
                ],
                "concentration_type": "BY_VOLUME",
            },
            "evaporator_fouling_factor": 0.0,
            "compressor_speed_control_type": "CONTINUOUS",
            "cycling_degradation_coefficient": self.cycling_degradation_coefficient,
            "performance_map_cooling": performance_map_cooling,
            "performance_map_standby": {
                "grid_variables": {
                    "environment_dry_bulb_temperature": [fr_u(20.0, "°C")],
                },
                "lookup_variables": {
                    "input_power": [self.standby_power],
                },
            },
            "performance_map_evaporator_liquid_pressure_differential": {
                "grid_variables": {
                    "evaporator_liquid_volumetric_flow_rate": evaporator_liquid_volumetric_flow_rates,
                    "evaporator_liquid_leaving_temperature": evaporator_liquid_leaving_temperatures,
                },
                "lookup_variables": {
                    "evaporator_liquid_differential_pressure": [fr_u(15.0, "kPa")]
                    * (
                        len(evaporator_liquid_volumetric_flow_rates)
                        * len(evaporator_liquid_leaving_temperatures)
                    ),
                },
            },
        }

        if self.condenser_type == CondenserType.LIQUID:
            condenser_liquid_volumetric_flow_rates = performance_map_cooling[
                "grid_variables"
            ]["condenser_liquid_volumetric_flow_rate"]
            condenser_liquid_entering_temperatures = performance_map_cooling[
                "grid_variables"
            ]["condenser_liquid_entering_temperature"]
            performance["condenser_liquid_type"] = {  # TODO: Make consistent with model
                "liquid_components": [
                    {
                        "liquid_constituent": "WATER",
                        "concentration": 1.0,
                    }
                ],
                "concentration_type": "BY_VOLUME",
            }
            performance["condenser_fouling_factor"] = 0.0
            performance["performance_map_condenser_liquid_pressure_differential"] = {
                "grid_variables": {
                    "condenser_liquid_volumetric_flow_rate": condenser_liquid_volumetric_flow_rates,
                    "condenser_liquid_entering_temperature": condenser_liquid_entering_temperatures,
                },
                "lookup_variables": {
                    "condenser_liquid_differential_pressure": [fr_u(15.0, "kPa")]
                    * (
                        len(condenser_liquid_volumetric_flow_rates)
                        * len(condenser_liquid_entering_temperatures)
                    ),
                },
            }

        # Scaling
        if capacity_range[0] is not None or capacity_range[1] is not None:
            scaling = {}

            if capacity_range[0] is None:
                scaling["minimum"] = 1.0
            elif capacity_range[0] > 0.0:
                scaling["minimum"] = (
                    capacity_range[0] / self.rated_net_evaporator_capacity
                )

            if capacity_range[1] is None:
                scaling["maximum"] = 1.0
            elif capacity_range[1] != float("inf"):
                scaling["maximum"] = (
                    capacity_range[1] / self.rated_net_evaporator_capacity
                )

            performance["scaling"] = scaling

        representation = {
            "metadata": metadata,
            "description": representation_description,
            "performance": performance,
        }

        return representation

    def make_performance_map(self):
        raise NotImplementedError()


class LiquidCooledChiller(Chiller):
    DEFAULT_CONDENSER_TEMPERATURE_RANGE = (
        fr_u(55.0, "degF"),
        fr_u(104.0, "degF"),
    )  # (fr_u(55.0, "degF"), fr_u(115.0, "degF")) # AHRI 550/590 2023 Table 5

    def __init__(
        self,
        rated_net_evaporator_capacity=fr_u(100, "ton_ref"),
        rated_cop=2,
        cycling_degradation_coefficient=0,
        standby_power=0,
        rated_net_condenser_capacity=None,
        number_of_compressor_speeds=None,
        condenser_entering_temperature_range=DEFAULT_CONDENSER_TEMPERATURE_RANGE,
        compressor_type=CompressorType.UNKNOWN,
    ):
        super().__init__(
            rated_net_evaporator_capacity=rated_net_evaporator_capacity,
            rated_cop=rated_cop,
            cycling_degradation_coefficient=cycling_degradation_coefficient,
            standby_power=standby_power,
            rated_net_condenser_capacity=rated_net_condenser_capacity,
            number_of_compressor_speeds=number_of_compressor_speeds,
            condenser_entering_temperature_range=condenser_entering_temperature_range,
            condenser_type=CondenserType.LIQUID,
            compressor_type=compressor_type,
        )

    def net_evaporator_capacity(self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS):
        raise NotImplementedError()

    def input_power(self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS):
        raise NotImplementedError()

    def net_condenser_capacity(self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS):
        raise NotImplementedError()

    def oil_cooler_heat(self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS):
        raise NotImplementedError()

    def auxiliary_heat(self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS):
        raise NotImplementedError()

    def condenser_liquid_leaving_state(
        self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS
    ):
        return conditions.condenser_inlet.add_heat(
            self.net_condenser_capacity(conditions)
        )

    def evaporator_liquid_entering_state(
        self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS
    ):
        return super().evaporator_liquid_entering_state(conditions)

    def space_loss_heat(self, conditions=AHRI_550_590_LIQUID_COOLED_CONDITIONS):
        return super().space_loss_heat(conditions)

    def set_rated_evaporator_volumetric_flow_rate(self):
        delta_T = (
            AHRI_550_590_EVAPORATOR_INLET.T
            - AHRI_550_590_LIQUID_COOLED_CONDITIONS.evaporator_outlet.T
        )
        m_dot = self.rated_net_evaporator_capacity / (
            AHRI_550_590_LIQUID_COOLED_CONDITIONS.evaporator_outlet.get_cp() * delta_T
        )
        AHRI_550_590_LIQUID_COOLED_CONDITIONS.evaporator_outlet.set_m_dot(m_dot)
        AHRI_550_590_EVAPORATOR_INLET.set_m_dot(m_dot)
        self.rated_evaporator_volumetric_flow_rate = (
            AHRI_550_590_LIQUID_COOLED_CONDITIONS.evaporator_outlet.V_dot
        )

    def set_rated_condenser_volumetric_flow_rate(self):
        delta_T = (
            AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET.T
            - AHRI_550_590_LIQUID_COOLED_CONDITIONS.condenser_inlet.T
        )
        m_dot = self.rated_net_condenser_capacity / (
            AHRI_550_590_LIQUID_COOLED_CONDITIONS.condenser_inlet.get_cp() * delta_T
        )
        AHRI_550_590_LIQUID_COOLED_CONDITIONS.condenser_inlet.set_m_dot(m_dot)
        AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET.set_m_dot(m_dot)
        self.rated_condenser_volumetric_flow_rate = (
            AHRI_550_590_LIQUID_COOLED_CONDITIONS.condenser_inlet.V_dot
        )

    def make_performance_map(self) -> dict:
        # Create conditions
        evaporator_liquid_volumetric_flow_rates = [
            self.rated_evaporator_volumetric_flow_rate
        ]
        evaporator_liquid_leaving_temperatures = linspace(
            self.evaporator_leaving_temperature_range[0],
            self.evaporator_leaving_temperature_range[1],
            4,
        ).tolist()
        compressor_sequence_numbers = list(
            range(1, self.number_of_compressor_speeds + 1)
        )

        condenser_liquid_volumetric_flow_rates = [
            self.rated_condenser_volumetric_flow_rate
        ]
        condenser_liquid_entering_temperatures = linspace(
            self.condenser_entering_temperature_range[0],
            self.condenser_entering_temperature_range[1],
            4,
        ).tolist()
        grid_variables = {
            "evaporator_liquid_volumetric_flow_rate": evaporator_liquid_volumetric_flow_rates,
            "evaporator_liquid_leaving_temperature": evaporator_liquid_leaving_temperatures,
            "condenser_liquid_volumetric_flow_rate": condenser_liquid_volumetric_flow_rates,
            "condenser_liquid_entering_temperature": condenser_liquid_entering_temperatures,
            "compressor_sequence_number": compressor_sequence_numbers,
        }

        input_powers = []
        net_evaporator_capacities = []
        net_condenser_capacities = []
        oil_cooler_heats = []
        auxiliary_heats = []
        operation_states = []

        for v_evap in evaporator_liquid_volumetric_flow_rates:
            for t_evap in evaporator_liquid_leaving_temperatures:
                for v_cond in condenser_liquid_volumetric_flow_rates:
                    for t_cond in condenser_liquid_entering_temperatures:
                        for speed in [
                            self.number_of_compressor_speeds - n
                            for n in compressor_sequence_numbers
                        ]:
                            conditions = OperatingConditions(
                                evaporator_outlet=LiquidState(
                                    temperature=t_evap, volumetric_flow_rate=v_evap
                                ),
                                condenser_inlet=LiquidState(
                                    temperature=t_cond, volumetric_flow_rate=v_cond
                                ),
                                compressor_speed=speed,
                            )

                            input_powers.append(self.input_power(conditions))
                            net_evaporator_capacities.append(
                                self.net_evaporator_capacity(conditions)
                            )
                            net_condenser_capacities.append(
                                self.net_condenser_capacity(conditions)
                            )
                            oil_cooler_heats.append(self.oil_cooler_heat(conditions))
                            auxiliary_heats.append(self.auxiliary_heat(conditions))
                            operation_states.append("NORMAL")
        lookup_variables = {
            "input_power": input_powers,
            "net_evaporator_capacity": net_evaporator_capacities,
            "net_condenser_capacity": net_condenser_capacities,
            "oil_cooler_heat": oil_cooler_heats,
            "auxiliary_heat": auxiliary_heats,
            "operation_state": operation_states,
        }

        return {
            "grid_variables": grid_variables,
            "lookup_variables": lookup_variables,
        }


class AirCooledChiller(Chiller):
    DEFAULT_CONDENSER_TEMPERATURE_RANGE = (
        fr_u(55.0, "degF"),
        fr_u(104.0, "degF"),
    )  # (fr_u(55.0, "degF"), fr_u(115.0, "degF")) # AHRI 550/590 2023 Table 5

    def make_performance_map(self) -> dict:
        # Create conditions
        evaporator_liquid_volumetric_flow_rates = [
            self.rated_evaporator_volumetric_flow_rate
        ]
        evaporator_liquid_leaving_temperatures = linspace(
            self.evaporator_leaving_temperature_range[0],
            self.evaporator_leaving_temperature_range[1],
            4,
        ).tolist()
        compressor_sequence_numbers = list(
            range(1, self.number_of_compressor_speeds + 1)
        )

        condenser_air_entering_drybulb_temperatures = [
            self.rated_condenser_volumetric_flow_rate
        ]
        condenser_air_entering_relative_humidities = [0.4]
        ambient_pressures = [fr_u(1.0, "atm")]
        grid_variables = {
            "evaporator_liquid_volumetric_flow_rate": evaporator_liquid_volumetric_flow_rates,
            "evaporator_liquid_leaving_temperature": evaporator_liquid_leaving_temperatures,
            "condenser_air_entering_drybulb_temperature": condenser_air_entering_drybulb_temperatures,
            "condenser_air_entering_relative_humidity": condenser_air_entering_relative_humidities,
            "ambient_pressure": ambient_pressures,
            "compressor_sequence_number": compressor_sequence_numbers,
        }

        input_powers = []
        net_evaporator_capacities = []
        net_condenser_capacities = []
        oil_cooler_heats = []
        auxiliary_heats = []
        operation_states = []
        condenser_air_volumetric_flow_rates = []
        evaporation_rates = []

        for v_evap in evaporator_liquid_volumetric_flow_rates:
            for t_evap in evaporator_liquid_leaving_temperatures:
                for t_cond in condenser_air_entering_drybulb_temperatures:
                    for rh_cond in condenser_air_entering_relative_humidities:
                        for p_cond in ambient_pressures:
                            for speed in [
                                self.number_of_compressor_speeds - n
                                for n in compressor_sequence_numbers
                            ]:
                                conditions = OperatingConditions(
                                    evaporator_outlet=LiquidState(
                                        temperature=t_evap,
                                        volumetric_flow_rate=v_evap,
                                    ),
                                    condenser_inlet=PsychrometricState(
                                        temperature=t_cond,
                                        relative_humidity=rh_cond,
                                        ambient_pressure=p_cond,
                                    ),
                                    compressor_speed=speed,
                                )

                                input_powers.append(self.input_power(conditions))
                                net_evaporator_capacities.append(
                                    self.net_evaporator_capacity(conditions)
                                )
                                net_condenser_capacities.append(
                                    self.net_condenser_capacity(conditions)
                                )
                                condenser_air_volumetric_flow_rates.append(
                                    self.condenser_air_volumetric_flow_rates(conditions)
                                )
                                oil_cooler_heats.append(
                                    self.oil_cooler_heat(conditions)
                                )
                                evaporation_rates.append(
                                    self.evaporation_rate(conditions)
                                )
                                auxiliary_heats.append(self.auxiliary_heat(conditions))
                                operation_states.append("NORMAL")

        lookup_variables = {
            "input_power": input_powers,
            "net_evaporator_capacity": net_evaporator_capacities,
            "net_condenser_capacity": net_condenser_capacities,
            "condenser_air_volumetric_flow_rate": condenser_air_volumetric_flow_rates,
            "oil_cooler_heat": oil_cooler_heats,
            "evaporation_rate": evaporation_rates,
            "auxiliary_heat": auxiliary_heats,
            "operation_state": operation_states,
        }

        return {
            "grid_variables": grid_variables,
            "lookup_variables": lookup_variables,
        }
