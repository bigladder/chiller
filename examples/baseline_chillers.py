from chiller import Chiller, fr_u
from chiller.models.ashrae_90_1 import ASHRAE90_1, CondenserType

import yaml
import cbor2
import json

'''
# Use to regenerate curve set constructors in ashrae_90_1.py
import csv
from chiller.models.ashrae_90_1 import ChillerCurveSet, compliance_path_text, condenser_type_text, compressor_type_text
chillers = []

with open('examples/90.1-chillers.csv') as file:
  reader = csv.reader(file)
  for row in reader:
    if reader.line_num > 1:
      chillers.append(ChillerCurveSet(
        set_name=row[0],
        path_type=next(k for k, v in compliance_path_text.items() if v == row[1]),
        condenser_type=next(k for k, v in condenser_type_text.items() if v == row[2]),
        compressor_type=next(k for k, v in compressor_type_text.items() if v == row[3]),
        minimum_capacity=fr_u(float(row[4]),"ton_ref"),
        maximum_capacity=float("inf") if row[5] == "" else fr_u(float(row[5]),"ton_ref"),
        cop=float(row[6]),
        iplv=float(row[7]),
        eir_temperature_coefficients=[float(c) for c in row[12:18]],
        capacity_temperature_coefficients=[float(c) for c in row[18:24]],
        eir_part_load_ratio_coefficients=[float(c) for c in row[24:28]]
      ))

      chillers[-1].print_constructor()
'''


for chiller in ASHRAE90_1.chiller_curve_sets:
  if chiller.condenser_type == CondenserType.LIQUID_COOLED:
    if chiller.maximum_capacity == float('inf'):
      size = chiller.minimum_capacity
    else:
      size = (chiller.minimum_capacity + chiller.maximum_capacity)*0.5
    new_chiller = Chiller(
      model=ASHRAE90_1(),
      rated_net_evaporator_capacity=size,
      rated_cop=chiller.cop,
      path_type=chiller.path_type,
      condenser_type=chiller.condenser_type,
      compressor_type=chiller.compressor_type)

    assert abs(new_chiller.cop() - new_chiller.rated_cop) < 0.05
    assert abs(new_chiller.net_evaporator_capacity() - new_chiller.rated_net_evaporator_capacity) < 0.01*size

    representation = new_chiller.generate_205_representation()

    output_directory_path = "output"
    file_name = f"ASHRAE90-1-2019-bd-Curve-Set-{chiller.set_name}.RS0001.a205"

    with open(f"{output_directory_path}/{file_name}.yaml", "w") as file:
      yaml.dump(representation, file, sort_keys=False)

    with open(f"{output_directory_path}/{file_name}.cbor", "wb") as file:
      cbor2.dump(representation, file)

    with open(f"{output_directory_path}/{file_name}.json", "w") as file:
      json.dump(representation, file, indent=4)
