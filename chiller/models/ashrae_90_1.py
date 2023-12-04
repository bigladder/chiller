from hashlib import sha256

from .energyplus_eir import EnergyPlusEIR
from enum import Enum
from koozie import to_u

class CondenserType(Enum):
  LIQUID_COOLED = 1
  AIR_COOLED = 2

condenser_type_text = {
  CondenserType.LIQUID_COOLED: "liquid-cooled",
  CondenserType.AIR_COOLED: "air-cooled",
}

class CompressorType(Enum):
  UNKNOWN = 0
  CENTRIFUGAL = 1
  POSITIVE_DISPLACEMENT = 2
  SCREW = 3
  SCROLL = 4

compressor_type_map = {
  CompressorType.UNKNOWN: None,
  CompressorType.CENTRIFUGAL: "CENTRIFUGAL",
  CompressorType.POSITIVE_DISPLACEMENT: "SCROLL",
  CompressorType.SCREW: "SCREW",
  CompressorType.SCROLL: "SCROLL"
}

compressor_type_text = {
  CompressorType.UNKNOWN: "",
  CompressorType.CENTRIFUGAL: "centrifugal",
  CompressorType.POSITIVE_DISPLACEMENT: "positive displacement",
  CompressorType.SCREW: "screw",
  CompressorType.SCROLL: "scroll"
}

class CompliancePathType(Enum):
  ECB_A = 1
  ECB_B = 2
  PRM = 3

compliance_path_text = {
  CompliancePathType.ECB_A: "Energy Cost Budget (ECB) Path A",
  CompliancePathType.ECB_B: "Energy Cost Budget (ECB) Path B",
  CompliancePathType.PRM: "Performance Rating Method (PRM)"
}


class ChillerCurveSet:
  def __init__(
    self,
    set_name,
    path_type,
    condenser_type,
    compressor_type,
    minimum_capacity,
    maximum_capacity,
    cop,
    iplv,
    capacity_temperature_coefficients,
    eir_temperature_coefficients,
    eir_part_load_ratio_coefficients):

    self.set_name = set_name
    self.path_type = path_type
    self.condenser_type = condenser_type
    self.compressor_type = compressor_type
    self.minimum_capacity = minimum_capacity
    self.maximum_capacity = maximum_capacity
    self.cop = cop
    self.iplv = iplv
    self.capacity_temperature_coefficients = capacity_temperature_coefficients
    self.eir_temperature_coefficients = eir_temperature_coefficients
    self.eir_part_load_ratio_coefficients = eir_part_load_ratio_coefficients

  def print_constructor(self):
    max_size_string = "float('inf')" if self.maximum_capacity == float('inf') else f"{self.maximum_capacity}"
    print(f"ChillerCurveSet('{self.set_name}',{self.path_type},{self.condenser_type},{self.compressor_type},{self.minimum_capacity},{max_size_string},{self.cop},{self.iplv},{self.capacity_temperature_coefficients},{self.eir_temperature_coefficients},{self.eir_part_load_ratio_coefficients}),")


class ASHRAE90_1(EnergyPlusEIR):

  chiller_curve_sets = [
    ChillerCurveSet('A',CompliancePathType.ECB_A,CondenserType.AIR_COOLED,CompressorType.UNKNOWN,0.0,527528.0,2.960018222222222,4.015074222222222,[0.686206, 0.057562, -0.001835, 0.01381, -0.000338, -0.000247],[0.825618, -0.025861, 0.001396, -0.002728, 0.000381, -0.000373],[0.087789, 0.185696, 1.561411, -0.832304]),
    ChillerCurveSet('B',CompliancePathType.ECB_A,CondenserType.AIR_COOLED,CompressorType.UNKNOWN,527528.0,float('inf'),2.960018222222222,4.102995555555555,[0.794185, 0.060199, -0.002016, 0.006203, -0.000229, -0.000183],[0.807832, -0.029452, 0.001431, -0.002832, 0.000399, -0.000278],[0.118081, 0.107477, 1.570838, -0.794051]),
    ChillerCurveSet('C',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,0.0,263764.0,4.689137777777779,5.861422222222224,[0.838337, 0.057024, -0.002117, 0.000793, -0.000175, 2e-05],[0.83688, -0.032383, 0.001568, -0.002806, 0.000544, -0.000407],[0.24373, 0.165972, 0.586099, 0.0]),
    ChillerCurveSet('D',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,263764.0,527528.0,4.88451851851852,6.280095238095239,[0.86184, 0.057837, -0.00217, -0.001391, -0.000136, 4e-05],[0.74092, -0.030144, 0.001479, 0.00385, 0.000416, -0.000404],[0.208982, 0.224001, 0.561479, 0.0]),
    ChillerCurveSet('E',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,527528.0,1055056.0,5.328565656565657,6.512691358024693,[0.800066, 0.035377, -0.001482, 0.006462, -0.000227, 0.000187],[0.620834, -0.023642, 0.0013, 0.013555, 0.000189, -0.000425],[0.246644, 0.184576, 0.566463, 0.0]),
    ChillerCurveSet('F',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,1055056.0,2110112.0,5.765333333333335,6.763179487179488,[0.863175, 0.023955, -0.001135, 0.004955, -0.000197, 0.000268],[0.636828, -0.029245, 0.001397, 0.018817, 8e-06, -0.000332],[0.244926, 0.21889, 0.532972, 0.0]),
    ChillerCurveSet('G',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,2110112.0,float('inf'),6.280095238095239,7.033706666666668,[0.830804, 0.01631, -0.000949, 0.008707, -0.000263, 0.000377],[0.544967, -0.030491, 0.001395, 0.027852, -0.000187, -0.000314],[0.264371, 0.263302, 0.47169, 0.0]),
    ChillerCurveSet('H',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,0.0,1055056.0,5.765333333333335,6.39427878787879,[0.83742, 0.038528, -0.002167, 0.004185, -0.000322, 0.000806],[0.447243, -0.033785, 0.000724, 0.040274, -0.000577, 0.000305],[0.304206, 0.073866, 0.621457, 0.0]),
    ChillerCurveSet('I',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,1055056.0,1406741.3333333335,6.280095238095239,6.763179487179488,[1.207878, 0.026951, -0.001148, -0.020576, 0.000202, 0.000479],[0.647193, -0.024484, 0.000426, 0.028764, -0.000421, 7.7e-05],[0.276961, 0.101749, 0.621383, 0.0]),
    ChillerCurveSet('J',CompliancePathType.ECB_A,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,1406741.3333333335,float('inf'),6.280095238095239,7.033706666666668,[0.896806, 0.056739, -0.002544, -0.005536, -0.000105, 0.00047],[0.489242, -0.028851, 0.000973, 0.035835, -0.000477, 9.6e-05],[0.290891, 0.059366, 0.649421, 0.0]),
    ChillerCurveSet('K',CompliancePathType.ECB_B,CondenserType.AIR_COOLED,CompressorType.UNKNOWN,0.0,527528.0,2.8427897777777775,4.6305235555555555,[0.709195, 0.059566, -0.001968, 0.010899, -0.000284, -0.000222],[0.891872, -0.029821, 0.001459, -0.006929, 0.000453, -0.000303],[0.036849, 0.100792, 1.614142, -0.748013]),
    ChillerCurveSet('L',CompliancePathType.ECB_B,CondenserType.AIR_COOLED,CompressorType.UNKNOWN,527528.0,float('inf'),2.8427897777777775,4.7184448888888895,[0.879844, 0.060415, -0.001994, 0.000937, -0.000156, -0.000155],[0.711589, -0.02952, 0.00139, 0.001554, 0.000353, -0.000272],[0.095711, 0.009903, 1.543396, -0.646737]),
    ChillerCurveSet('M',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,0.0,263764.0,4.508786324786326,7.033706666666668,[0.835803, 0.057057, -0.002119, 0.000903, -0.000176, 1.9e-05],[0.844064, -0.032504, 0.001571, -0.003076, 0.000545, -0.000402],[0.1072, 0.182611, 0.705182, 0.0]),
    ChillerCurveSet('N',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,263764.0,527528.0,4.689137777777779,7.177251700680273,[0.85071, 0.056037, -0.002077, -0.000147, -0.000153, 2.3e-05],[0.797371, -0.031361, 0.001514, 0.000419, 0.000473, -0.000398],[0.183811, -0.044417, 0.85566, 0.0]),
    ChillerCurveSet('O',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,527528.0,1055056.0,5.1718431372549025,7.992848484848486,[0.822519, 0.038968, -0.001588, 0.004048, -0.000188, 0.000164],[0.617871, -0.02011, 0.001175, 0.013623, 0.000172, -0.000439],[0.090936, 0.207812, 0.696735, 0.0]),
    ChillerCurveSet('P',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,1055056.0,2110112.0,5.6269653333333345,8.577691056910572,[0.877218, 0.028393, -0.001257, 0.003217, -0.000174, 0.000232],[0.656763, -0.027891, 0.001343, 0.016627, 5.6e-05, -0.000348],[0.103665, 0.148024, 0.744887, 0.0]),
    ChillerCurveSet('Q',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,2110112.0,float('inf'),6.011715099715102,9.254877192982459,[0.831828, 0.015657, -0.000928, 0.009067, -0.000272, 0.000376],[0.553694, -0.030347, 0.001412, 0.026568, -0.000153, -0.000325],[0.061706, 0.261711, 0.677017, 0.0]),
    ChillerCurveSet('R',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,0.0,527528.0,5.0602206235012,7.992848484848486,[0.972517, 0.040861, -0.001781, -0.008217, 1.3e-05, 0.000328],[0.62736, -0.028989, 0.001027, 0.027958, -0.00035, 2e-06],[0.072183, 0.10865, 0.818174, 0.0]),
    ChillerCurveSet('S',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,527528.0,1055056.0,5.538351706036747,8.792133333333336,[0.971699, 0.036192, -0.001858, -0.005224, -0.000134, 0.000709],[0.526475, -0.030843, 0.000735, 0.035532, -0.00051, 0.000216],[0.064979, 0.151829, 0.779131, 0.0]),
    ChillerCurveSet('T',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,1055056.0,1406741.3333333335,5.910677871148461,9.017572649572651,[1.023337, 0.033378, -0.001742, -0.005438, -0.000153, 0.000633],[0.54781, -0.02947, 0.000842, 0.032888, -0.000423, 4.8e-05],[0.082812, 0.152816, 0.764822, 0.0]),
    ChillerCurveSet('U',CompliancePathType.ECB_B,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,1406741.3333333335,float('inf'),6.011715099715102,9.254877192982459,[0.95358, 0.05301, -0.002387, -0.007165, -0.000104, 0.00051],[0.569569, -0.0247, 0.000727, 0.030569, -0.000409, 8.7e-05],[0.058583, 0.205486, 0.736345, 0.0]),
    ChillerCurveSet('V',CompliancePathType.PRM,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,0.0,527528.0,4.450023197941711,5.200138005815961,[0.840898, 0.059263, -0.002225, 0.000735, -0.000188, 2e-05],[0.817024, -0.034213, 0.001638, -0.00259, 0.000566, -0.000389],[0.276037, 0.253577, 0.466353, 0.0]),
    ChillerCurveSet('X',CompliancePathType.PRM,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,527528.0,1055056.0,4.899489179901552,5.600084925690022,[0.850133, 0.050234, -0.001951, 0.000606, -0.000161, 0.000118],[0.627193, -0.015646, 0.001067, 0.00827, 0.000331, -0.000515],[0.250801, 0.345915, 0.399138, 0.0]),
    ChillerCurveSet('Y',CompliancePathType.PRM,CondenserType.LIQUID_COOLED,CompressorType.POSITIVE_DISPLACEMENT,1055056.0,float('inf'),5.499379723742508,6.149420061782364,[0.87313, 0.033599, -0.001391, 0.000961, -0.000114, 0.000178],[0.664854, -0.029016, 0.001339, 0.017823, 8e-06, -0.000318],[0.320097, 0.074356, 0.602938, 0.0]),
    ChillerCurveSet('Z',CompliancePathType.PRM,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,0.0,527528.0,4.999791488958393,5.249818380852864,[0.97331, 0.040996, -0.001782, -0.00834, 1.6e-05, 0.000327],[0.628525, -0.028798, 0.001019, 0.027867, -0.000349, 2e-06],[0.281669, 0.202762, 0.515409, 0.0]),
    ChillerCurveSet('AA',CompliancePathType.PRM,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,527528.0,1055056.0,5.549713323865131,5.899770731980094,[0.909633, 0.03546, -0.001881, -0.001808, -0.000158, 0.000648],[0.46433, -0.033834, 0.000731, 0.040345, -0.000592, 0.000277],[0.339494, 0.04909, 0.611582, 0.0]),
    ChillerCurveSet('AB',CompliancePathType.PRM,CondenserType.LIQUID_COOLED,CompressorType.CENTRIFUGAL,1055056.0,float('inf'),6.099294716152158,6.400097057931454,[0.988289, 0.031128, -0.00155, -0.003349, -0.000147, 0.000503],[0.563967, -0.034331, 0.001015, 0.033941, -0.000432, -2.5e-05],[0.309752, 0.153649, 0.536462, 0.0])
  ]

  def __init__(self):
    super().__init__()
    self.required_kwargs += [
      "path_type",
      "condenser_type",
      "compressor_type"
    ]

  def set_system(self, system):
    # set kwarg variables
    self.path_type = system.kwargs["path_type"]
    self.condenser_type = system.kwargs["condenser_type"]
    self.compressor_type = system.kwargs["compressor_type"]

    # match curve set
    matches_found = []
    for curve_set in self.chiller_curve_sets:
      if curve_set.path_type == self.path_type:
        if curve_set.condenser_type == self.condenser_type:
          if (curve_set.compressor_type == CompressorType.CENTRIFUGAL) == (self.compressor_type == CompressorType.CENTRIFUGAL):
            if (system.rated_net_evaporator_capacity > curve_set.minimum_capacity) and (system.rated_net_evaporator_capacity <= curve_set.maximum_capacity):
              matches_found.append(curve_set)

    search_criteria_text = f"'path_type'={self.path_type}, 'condenser_type'={self.condenser_type}, 'compressor_type'={self.compressor_type}, 'rated_net_evaporator_capacity'={system.rated_net_evaporator_capacity}"

    if len(matches_found) == 0:
      raise Exception(f"Unable to find matching curve-set for {search_criteria_text}")
    elif len(matches_found) > 1:
      raise Exception(f"Multiple matching curve-sets found for {search_criteria_text}")
    else:
      self.curve_set = matches_found[0]

    # set baseclass kwargs
    system.kwargs["eir_temperature_coefficients"] = self.curve_set.eir_temperature_coefficients
    system.kwargs["eir_part_load_ratio_coefficients"] = self.curve_set.eir_part_load_ratio_coefficients
    system.kwargs["capacity_temperature_coefficients"] = self.curve_set.capacity_temperature_coefficients
    system.kwargs["minimum_part_load_ratio"] = 0.25
    system.kwargs["minimum_unloading_ratio"] = 0.25

    # set metadata
    system.metadata.notes = f"Based on ASHRAE 90.1-2019 Addendum 'bd' curve set '{self.curve_set.set_name}' for {compliance_path_text[self.curve_set.path_type]}"
    system.metadata.compressor_type = compressor_type_map[self.compressor_type]
    compressor_text = compressor_type_text[self.compressor_type]
    condenser_text = condenser_type_text[self.condenser_type]
    type_text = f"{condenser_text}"
    if compressor_text is not None:
      type_text += f", {compressor_text} compressor"
    type_text += f" chiller"
    system.metadata.description = f"ASHRAE 90.1-2019 Addendum 'bd' curve set '{self.curve_set.set_name}': {to_u(system.rated_net_evaporator_capacity,'ton_ref'):.1f} ton, {system.rated_cop:.2f} COP, {self.curve_set.iplv:.2f} IPLV {type_text}"
    unique_characteristics = (
      system.rated_net_evaporator_capacity,
      system.rated_cop,
      system.cycling_degradation_coefficient,
      system.standby_power,
      self.path_type,
      self.compressor_type,
      self.condenser_type
    )
    system.metadata.uuid_seed = sha256(f"{unique_characteristics}".encode()).hexdigest()


    return super().set_system(system)

  def __hash__(self):
    return hash((self.curve_set.set_name,self.system.rated_net_evaporator_capacity,self.system.rated_cop))
