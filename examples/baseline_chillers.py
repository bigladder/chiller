import csv
from chiller import Chiller, fr_u

import yaml
import cbor2
import json
import uuid
import datetime


chillers = []

with open('examples/90.1-chillers.csv') as file:
  reader = csv.reader(file)
  for row in reader:
    if reader.line_num > 1:
      chillers.append(
        {
          "set": row[0],
          "path": row[1],
          "type": row[2],
          "subtype": row[3],
          "min_size": float(row[4]),
          "max_size": None if row[5] == "" else float(row[5]),
          "cop": float(row[6]),
          "eir_f_t": [float(c) for c in row[12:18]],
          "cap_f_t": [float(c) for c in row[18:24]],
          "eir_f_plr": [float(c) for c in row[24:28]]
        }
      )

for chiller in chillers:
  if chiller["type"] == "Liquid-cooled":
    if chiller["max_size"] is None:
      size_tons = chiller["min_size"]
    else:
      size_tons = (chiller["min_size"] + chiller["max_size"])*0.5
    size = fr_u(size_tons,"ton_ref")
    new_chiller = Chiller(
      rated_net_evaporator_capacity=size,
      rated_cop=chiller["cop"],
      min_plr=0.25,
      cap_f_t=chiller["cap_f_t"],
      eir_f_t=chiller["eir_f_t"],
      eir_f_plr=chiller["eir_f_plr"],
      cycling_degradation_coefficient=0.0)

    assert abs(new_chiller.cop() - chiller["cop"]) < 0.05
    assert abs(new_chiller.net_evaporator_capacity() - size) < 0.01*size

    performance = new_chiller.generate_205_performance()

    ch_type = chiller['type']
    subtype = " "
    if len(chiller['subtype']) > 0:
      subtype = f" ({chiller['subtype']}) "
    timestamp = datetime.datetime.now().isoformat("T","minutes")
    representation = {
      "metadata": {
        "data_model": "ASHRAE_205",
        "schema": "RS0001",
        "schema_version": "0.2.0",
        "description": f"{size_tons:.1f} ton, {chiller['cop']:.2f} COP {chiller['type']}{subtype}Chiller based on ASHRAE 90.1-2019 Addendum 'bd' curve set '{chiller['set']}'",
        "id": str(uuid.uuid4()),
        "data_timestamp": f"{timestamp}Z",
        "data_version": 1,
        "data_source": "Big Ladder Software",
        "disclaimer": "This data is synthetic and does not represent any physical products.",
        "notes": f"Based on ASHRAE 90.1-2019 Addendum 'bd' curve set '{chiller['set']}'",
      },
      "description": {
        "product_information":
        {
          "manufacturer": "ASHRAE SSPC 90.1",
          "compressor_type": "CENTRIFUGAL" if chiller['subtype'] == "Centrifugal" else "SCROLL",
          "liquid_data_source": "CoolProp",
          "hot_gas_bypass_installed": False
        }
      },
      "performance": performance
    }

    with open(f"output/ASHRAE90-1-2019-bd-Curve-Set-{chiller['set']}.RS0001.a205.yaml", "w") as file:
      yaml.dump(representation, file, sort_keys=False)

    with open(f"output/ASHRAE90-1-2019-bd-Curve-Set-{chiller['set']}.RS0001.a205.cbor", "wb") as file:
      cbor2.dump(representation, file)

    with open(f"output/ASHRAE90-1-2019-bd-Curve-Set-{chiller['set']}.RS0001.a205.json", "w") as file:
      json.dump(representation, file, indent=4)
