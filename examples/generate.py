from chiller import Chiller, fr_u
from chiller.models import EnergyPlusReformulatedEIR, EnergyPlusEIR

import yaml
import cbor2
import json
import uuid
import datetime

# From Large Office Reference Building
size_tons = 40.0
cop = 5.5
chiller_type = "Liquid-cooled"
subtype = " "
min_plr = 0.1
min_unload = 0.2
cap_f_t = [0.9061150, 0.0292277, -0.0003647, -0.0009709, -0.0000905, 0.0002527]
eir_f_t = [ 0.3617105, -0.0229833, -0.0009519, 0.0131889, 0.0003752, -0.0007059]
eir_f_plr = [ 4.602131E-02, 2.433945E-02, 6.394526E-05, -3.648563E-01, 1.854759E+00, -2.809346E-02, 0.000000E+00, -4.821515E-01, 0.000000E+00, 0.000000E+00,]


my_chiller = Chiller(
  model=EnergyPlusReformulatedEIR(),
  rated_net_evaporator_capacity=fr_u(size_tons,"ton_ref"),
  rated_cop=cop,
  min_plr=min_plr,
  cap_f_t=cap_f_t,
  eir_f_t=eir_f_t,
  eir_f_plr=eir_f_plr
  )

assert abs(my_chiller.net_evaporator_capacity() - my_chiller.rated_net_evaporator_capacity) < 0.01*my_chiller.rated_net_evaporator_capacity
# assert abs(my_chiller.cop() - my_chiller.rated_cop) < 0.05

performance = my_chiller.generate_205_performance()

timestamp = datetime.datetime.now().isoformat("T","minutes")
representation = {
  "metadata": {
    "data_model": "ASHRAE_205",
    "schema": "RS0001",
    "schema_version": "0.2.0",
    "description": f"{size_tons:.1f} ton, {cop:.2f} COP {chiller_type}{subtype}Chiller based on ASHRAE 90.1-2019 Addendum 'bd' curve set '{chiller['set']}'",
    "id": str(uuid.uuid4()),
    "data_timestamp": f"{timestamp}Z",
    "data_version": 1,
    "data_source": "Big Ladder Software",
    "disclaimer": "This data is synthetic and does not represent any physical products.",
    "notes": f"",
  },
  "description": {
    "product_information":
    {
      "compressor_type": "CENTRIFUGAL" if subtype == "Centrifugal" else "SCROLL",
      "liquid_data_source": "CoolProp",
      "hot_gas_bypass_installed": False
    }
  },
  "performance": performance
}

with open(f"output/Reformulated.RS0001.a205.yaml", "w") as file:
  yaml.dump(representation, file, sort_keys=False)

with open(f"output/Reformulated.RS0001.a205.cbor", "wb") as file:
  cbor2.dump(representation, file)

with open(f"output/Reformulated.RS0001.a205.json", "w") as file:
  json.dump(representation, file, indent=4)
