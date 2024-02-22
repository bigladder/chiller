from chiller import Chiller
from chiller.models import EnergyPlusReformulatedEIR

from koozie import fr_u

import yaml
import cbor2
import json

from chiller.models.ashrae_90_1 import (
    ASHRAE90_1,
    CompliancePathType,
    CompressorType,
    CondenserType,
)

# From Large Office Reference Building
size_tons = 40.0
cop = 5.5
chiller_type = "Liquid-cooled"
subtype = " "
minimum_part_load_ratio = 0.1
minimum_unloading_ratio = 0.2
capacity_temperature_coefficients = [
    0.9061150,
    0.0292277,
    -0.0003647,
    -0.0009709,
    -0.0000905,
    0.0002527,
]
eir_temperature_coefficients = [
    0.3617105,
    -0.0229833,
    -0.0009519,
    0.0131889,
    0.0003752,
    -0.0007059,
]
eir_part_load_ratio_coefficients = [
    4.602131e-02,
    2.433945e-02,
    6.394526e-05,
    -3.648563e-01,
    1.854759e00,
    -2.809346e-02,
    0.000000e00,
    -4.821515e-01,
    0.000000e00,
    0.000000e00,
]


my_chiller = Chiller(
    model=EnergyPlusReformulatedEIR(),
    rated_net_evaporator_capacity=fr_u(size_tons, "ton_ref"),
    rated_cop=cop,
    minimum_part_load_ratio=minimum_part_load_ratio,
    minimum_unloading_ratio=minimum_unloading_ratio,
    capacity_temperature_coefficients=capacity_temperature_coefficients,
    eir_temperature_coefficients=eir_temperature_coefficients,
    eir_part_load_ratio_coefficients=eir_part_load_ratio_coefficients,
)

assert (
    abs(my_chiller.net_evaporator_capacity() - my_chiller.rated_net_evaporator_capacity)
    < 0.01 * my_chiller.rated_net_evaporator_capacity
)
# assert abs(my_chiller.cop() - my_chiller.rated_cop) < 0.05

my_chiller.metadata.description = (
    f"{size_tons:.1f} ton, {cop:.2f} COP {chiller_type}{subtype}Chiller"
)

representation = my_chiller.generate_205_representation()

output_directory_path = "output"
file_name = "Reformulated.RS0001.a205"

with open(f"{output_directory_path}/{file_name}.yaml", "w") as file:
    yaml.dump(representation, file, sort_keys=False)

with open(f"{output_directory_path}/{file_name}.cbor", "wb") as file:
    cbor2.dump(representation, file)

with open(f"{output_directory_path}/{file_name}.json", "w") as file:
    json.dump(representation, file, indent=4)

# For Large Office ASHRAE 90.1 Building

new_chiller = Chiller(
    model=ASHRAE90_1(),
    rated_net_evaporator_capacity=999070.745,
    rated_cop=5.33,
    path_type=CompliancePathType.PRM,
    compressor_type=CompressorType.POSITIVE_DISPLACEMENT,
    condenser_type=CondenserType.LIQUID_COOLED,
)

representation = new_chiller.generate_205_representation()

file_name = "CoolSys1-Chiller.RS0001.a205"

with open(f"{output_directory_path}/{file_name}.yaml", "w") as file:
    yaml.dump(representation, file, sort_keys=False)

with open(f"{output_directory_path}/{file_name}.cbor", "wb") as file:
    cbor2.dump(representation, file)

with open(f"{output_directory_path}/{file_name}.json", "w") as file:
    json.dump(representation, file, indent=4)

new_chiller2 = Chiller(
    model=ASHRAE90_1(),
    rated_net_evaporator_capacity=999070.745,
    rated_cop=5.33,
    cycling_degradation_coefficient=0.25,
    standby_power=500.0,
    space_gain_fraction=0.02,
    oil_cooler_fraction=0.01,
    auxiliary_fraction=0.01,
    path_type=CompliancePathType.PRM,
    compressor_type=CompressorType.POSITIVE_DISPLACEMENT,
    condenser_type=CondenserType.LIQUID_COOLED,
)

representation = new_chiller2.generate_205_representation()

file_name = "CoolSys1-Chiller-Detailed.RS0001.a205"

with open(f"{output_directory_path}/{file_name}.yaml", "w") as file:
    yaml.dump(representation, file, sort_keys=False)

with open(f"{output_directory_path}/{file_name}.cbor", "wb") as file:
    cbor2.dump(representation, file)

with open(f"{output_directory_path}/{file_name}.json", "w") as file:
    json.dump(representation, file, indent=4)
