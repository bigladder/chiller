from chiller.fluid_properties import FluidState
from .conditions import AHRI_550_590_WATER_COOLED_CONDITIONS, AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET, AHRI_550_590_WATER_COOLED_EVAPORATOR_INLET, OperatingConditions
from .models.energyplus_eir import EnergyPlusEIR
from koozie import fr_u
from numpy import linspace
import uuid
import datetime
from random import Random

class ChillerMetadata:
  def __init__(
    self,
    description="",
    data_source="https://github.com/bigladder/chiller",
    notes="",
    compressor_type="",
    has_hot_gas_bypass_installed=False,
    uuid_seed=None
    ):

    self.description = description
    self.data_source = data_source
    self.notes = notes
    self.compressor_type = compressor_type
    self.has_hot_gas_bypass_installed = has_hot_gas_bypass_installed
    self.uuid_seed = uuid_seed

class Chiller:
  def __init__(
    self,
    model=None,
    rated_net_evaporator_capacity=fr_u(100.0,"ton_ref"),
    rated_cop=2.0,
    cycling_degradation_coefficient=0.0,
    standby_power=0.0,
    rated_net_condenser_capacity=None,
    number_of_compressor_speeds=None,
    minimum_evaporator_leaving_temperature=fr_u(39.0,"°F"),
    maximum_evaporator_leaving_temperature=fr_u(60.0,"°F"),
    minimum_condenser_entering_temperature=fr_u(55.0,"°F"),
    maximum_condenser_entering_temperature=fr_u(104.0,"°F"),
    metadata=None,
    **kwargs):

    self.kwargs = kwargs

    if model is None:
      self.model = EnergyPlusEIR()
    else:
      self.model = model

    self.number_of_compressor_speeds = number_of_compressor_speeds
    self.rated_net_condenser_capacity = rated_net_condenser_capacity
    self.rated_net_evaporator_capacity = rated_net_evaporator_capacity
    self.rated_cop = rated_cop
    self.cycling_degradation_coefficient = cycling_degradation_coefficient
    self.standby_power = standby_power
    self.minimum_evaporator_leaving_temperature = minimum_evaporator_leaving_temperature
    self.maximum_evaporator_leaving_temperature = maximum_evaporator_leaving_temperature
    self.minimum_condenser_entering_temperature = minimum_condenser_entering_temperature
    self.maximum_condenser_entering_temperature = maximum_condenser_entering_temperature

    if metadata is None:
      self.metadata = ChillerMetadata()
    else:
      self.metadata = metadata

    self.model.set_system(self)

    self.set_rated_evaporator_volumetric_flow_rate()
    self.set_rated_condenser_volumetric_flow_rate()

  def net_evaporator_capacity(self, conditions=None):
    if conditions == None:
      conditions = AHRI_550_590_WATER_COOLED_CONDITIONS
    return self.model.net_evaporator_capacity(conditions)

  def input_power(self, conditions=None):
    if conditions == None:
      conditions = AHRI_550_590_WATER_COOLED_CONDITIONS
    return self.model.input_power(conditions)

  def net_condenser_capacity(self, conditions=None):
    if conditions == None:
      conditions = AHRI_550_590_WATER_COOLED_CONDITIONS
    return self.model.net_condenser_capacity(conditions)

  def oil_cooler_heat(self, conditions=None):
    if conditions == None:
      conditions = AHRI_550_590_WATER_COOLED_CONDITIONS
    return self.model.oil_cooler_heat(conditions)

  def auxiliary_heat(self, conditions=None):
    if conditions == None:
      conditions = AHRI_550_590_WATER_COOLED_CONDITIONS
    return self.model.auxiliary_heat(conditions)

  def cop(self, conditions=None):
    return self.net_evaporator_capacity(conditions)/self.input_power(conditions)

  def condenser_liquid_leaving_state(self, conditions=None):
    if conditions == None:
      conditions = AHRI_550_590_WATER_COOLED_CONDITIONS
    return conditions.condenser_inlet.add_heat(self.net_condenser_capacity(conditions))

  def evaporator_liquid_entering_state(self, conditions=None):
    if conditions == None:
      conditions = AHRI_550_590_WATER_COOLED_CONDITIONS
    return conditions.evaporator_outlet.add_heat(self.net_evaporator_capacity(conditions))

  def space_loss_heat(self, conditions=None):
    return (self.input_power(conditions) + self.net_evaporator_capacity(conditions)) - (self.net_condenser_capacity(conditions) + self.oil_cooler_heat(conditions) + self.auxiliary_heat(conditions))

  def set_rated_evaporator_volumetric_flow_rate(self):
    delta_T = AHRI_550_590_WATER_COOLED_EVAPORATOR_INLET.T - AHRI_550_590_WATER_COOLED_CONDITIONS.evaporator_outlet.T
    m_dot = self.rated_net_evaporator_capacity/(AHRI_550_590_WATER_COOLED_CONDITIONS.evaporator_outlet.get_cp()*delta_T)
    AHRI_550_590_WATER_COOLED_CONDITIONS.evaporator_outlet.set_m_dot(m_dot)
    AHRI_550_590_WATER_COOLED_EVAPORATOR_INLET.set_m_dot(m_dot)
    self.rated_evaporator_volumetric_flow_rate = AHRI_550_590_WATER_COOLED_CONDITIONS.evaporator_outlet.V_dot

  def set_rated_condenser_volumetric_flow_rate(self):
    delta_T = AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET.T - AHRI_550_590_WATER_COOLED_CONDITIONS.condenser_inlet.T
    m_dot = self.rated_net_condenser_capacity/(AHRI_550_590_WATER_COOLED_CONDITIONS.condenser_inlet.get_cp()*delta_T)
    AHRI_550_590_WATER_COOLED_CONDITIONS.condenser_inlet.set_m_dot(m_dot)
    AHRI_550_590_WATER_COOLED_CONDENSER_OUTLET.set_m_dot(m_dot)
    self.rated_condenser_volumetric_flow_rate = AHRI_550_590_WATER_COOLED_CONDITIONS.condenser_inlet.V_dot

  def generate_205_representation(self):
    # Metadata
    timestamp = datetime.datetime.now().isoformat("T","minutes")
    rnd = Random()
    if self.metadata.uuid_seed is None:
      self.metadata.uuid_seed = hash(self)
    rnd.seed(self.metadata.uuid_seed)
    unique_id = str(uuid.UUID(int=rnd.getrandbits(128), version=4))


    metadata = {
      "data_model": "ASHRAE_205",
      "schema": "RS0001",
      "schema_version": "1.0.0",
      "description": self.metadata.description,
      "id": unique_id,
      "data_timestamp": f"{timestamp}Z",
      "data_version": 1,
      "data_source": self.metadata.data_source,
      "disclaimer": "This data is synthetic and does not represent any physical products.",
      "notes": self.metadata.notes,
    }
    representation_description = {
      "product_information":
      {
        "liquid_data_source": "CoolProp",
        "hot_gas_bypass_installed": self.metadata.has_hot_gas_bypass_installed
      }
    }

    if self.metadata.compressor_type is not None:
      representation_description["product_information"]["compressor_type"] = self.metadata.compressor_type

    # Create conditions
    evaporator_liquid_volumetric_flow_rates = [self.rated_evaporator_volumetric_flow_rate]
    evaporator_liquid_leaving_temperatures = linspace(self.minimum_evaporator_leaving_temperature, self.maximum_evaporator_leaving_temperature, 4).tolist()
    condenser_liquid_volumetric_flow_rates = [self.rated_condenser_volumetric_flow_rate]
    condenser_liquid_entering_temperatures = linspace(self.minimum_condenser_entering_temperature, self.maximum_condenser_entering_temperature, 4).tolist()
    compressor_sequence_numbers = list(range(1,self.number_of_compressor_speeds + 1))

    grid_variables = {
      "evaporator_liquid_volumetric_flow_rate":
        evaporator_liquid_volumetric_flow_rates,
      "evaporator_liquid_leaving_temperature":
        evaporator_liquid_leaving_temperatures,
      "condenser_liquid_volumetric_flow_rate":
        condenser_liquid_volumetric_flow_rates,
      "condenser_liquid_entering_temperature":
        condenser_liquid_entering_temperatures,
      "compressor_sequence_number":
        compressor_sequence_numbers
    }

    input_powers = []
    net_evaporator_capacities = []
    net_condenser_capacities = []
    evaporator_liquid_entering_temperatures = []
    condenser_liquid_leaving_temperatures = []
    evaporator_liquid_differential_pressures = []
    condenser_liquid_differential_pressures = []
    oil_cooler_heats = []
    auxiliary_heats = []

    for v_evap in evaporator_liquid_volumetric_flow_rates:
      for t_evap in evaporator_liquid_leaving_temperatures:
        for v_cond in condenser_liquid_volumetric_flow_rates:
          for t_cond in condenser_liquid_entering_temperatures:
            for speed in [self.number_of_compressor_speeds - n for n in compressor_sequence_numbers]:
              conditions = OperatingConditions(
                evaporator_outlet=FluidState(temperature=t_evap, volumetric_flow_rate=v_evap),
                condenser_inlet=FluidState(temperature=t_cond, volumetric_flow_rate=v_cond),
                compressor_speed=speed)

              input_powers.append(self.input_power(conditions))
              net_evaporator_capacities.append(self.net_evaporator_capacity(conditions))
              net_condenser_capacities.append(self.net_condenser_capacity(conditions))
              evaporator_liquid_entering_temperatures.append(self.evaporator_liquid_entering_state(conditions).T)
              condenser_liquid_leaving_temperatures.append(self.condenser_liquid_leaving_state(conditions).T)
              evaporator_liquid_differential_pressures.append(fr_u(15.,"kPa"))
              condenser_liquid_differential_pressures.append(fr_u(15.,"kPa"))
              oil_cooler_heats.append(self.oil_cooler_heat(conditions))
              auxiliary_heats.append(self.auxiliary_heat(conditions))

    performance_map_cooling = {
      "grid_variables": grid_variables,
      "lookup_variables": {
        "input_power":
          input_powers,
        "net_evaporator_capacity":
          net_evaporator_capacities,
        "net_condenser_capacity":
          net_condenser_capacities,
        "evaporator_liquid_entering_temperature":
          evaporator_liquid_entering_temperatures,
        "condenser_liquid_leaving_temperature":
          condenser_liquid_leaving_temperatures,
        "evaporator_liquid_differential_pressure":
          evaporator_liquid_differential_pressures,
        "condenser_liquid_differential_pressure":
          condenser_liquid_differential_pressures,
        "oil_cooler_heat":
          oil_cooler_heats,
        "auxiliary_heat":
          auxiliary_heats
      }
    }
    performance = {
      "evaporator_liquid_type": { # TODO: Make consistent with model
        "liquid_components": [
          {
            "liquid_constituent": "WATER",
            "concentration": 1.0,
          }
        ],
        "concentration_type": "BY_VOLUME"
      },
      "condenser_liquid_type": { # TODO: Make consistent with model
        "liquid_components": [
          {
            "liquid_constituent": "WATER",
            "concentration": 1.0,
          }
        ],
        "concentration_type": "BY_VOLUME"
      },
      "evaporator_fouling_factor": 0.0,
      "condenser_fouling_factor": 0.0,
      "compressor_speed_control_type": "CONTINUOUS",
      "maximum_power": max(input_powers),  # Do something else?
      "cycling_degradation_coefficient": self.cycling_degradation_coefficient,
      "performance_map_cooling": performance_map_cooling,
      "performance_map_standby": {
        "grid_variables": {
          "environment_dry_bulb_temperature": [fr_u(20.0, "°C")],
        },
        "lookup_variables": {
          "input_power": [self.standby_power],
        },
      }
    }

    representation = {"metadata": metadata, "description": representation_description, "performance": performance}

    return self.model.fixup_205_representation(representation)
