from chiller import Chiller
from chiller.models.ashrae_90_1 import ASHRAE90_1BaselineChiller, CondenserType
from hashlib import sha256

from koozie import fr_u

import yaml
import cbor2
import json

"""
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
        cop=1./fr_u(float(row[8]),"kW/ton_ref") if row[6] == "" else fr_u(float(row[6]),"Btu/(W*h)"),
        iplv=1./fr_u(float(row[9]),"kW/ton_ref") if row[7] == "" else fr_u(float(row[7]),"Btu/(W*h)"),
        eir_temperature_coefficients=[float(c) for c in row[10:16]],
        capacity_temperature_coefficients=[float(c) for c in row[16:22]],
        eir_part_load_ratio_coefficients=[float(c) for c in row[22:26]]
      ))

      chillers[-1].print_constructor()
"""


for chiller in ASHRAE90_1BaselineChiller.chiller_curve_sets:
    if chiller.maximum_capacity == float("inf"):
        size = chiller.minimum_capacity + fr_u(50.0, "ton_ref")
    else:
        size = (chiller.minimum_capacity + chiller.maximum_capacity) * 0.5
    new_chiller = ASHRAE90_1BaselineChiller(
        rated_net_evaporator_capacity=size,
        rated_cop=chiller.cop,
        path_type=chiller.path_type,
        condenser_type=chiller.condenser_type,
        compressor_type=chiller.compressor_type,
    )

    assert abs(new_chiller.cop() - new_chiller.rated_cop) < 0.05
    assert (
        abs(
            new_chiller.net_evaporator_capacity()
            - new_chiller.rated_net_evaporator_capacity
        )
        < 0.01 * size
    )

    new_chiller.metadata.data_version = 3  # TODO: Update when necessary
    unique_characteristics = (
        chiller.set_name,
        new_chiller.rated_net_evaporator_capacity,
    )
    new_chiller.metadata.uuid_seed = sha256(
        f"{unique_characteristics}".encode()
    ).hexdigest()

    representation = new_chiller.generate_205_representation()

    output_directory_path = "output"
    file_name = f"ASHRAE90-1-2022-AppJ-Curve-Set-{chiller.set_name}.RS0001.a205"

    # with open(f"{output_directory_path}/{file_name}.yaml", "w") as file:
    #   yaml.dump(representation, file, sort_keys=False)

    # with open(f"{output_directory_path}/{file_name}.cbor", "wb") as file:
    #   cbor2.dump(representation, file)

    with open(f"{output_directory_path}/{file_name}.json", "w") as file:
        json.dump(representation, file, indent=4)
