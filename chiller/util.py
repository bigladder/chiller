def calc_biquad(coeff, in_1, in_2):
  return coeff[0] + coeff[1]*in_1 + coeff[2]*in_1*in_1 + coeff[3]*in_2 + coeff[4]*in_2*in_2 + coeff[5]*in_1*in_2

def calc_cubic(coeff, in_1):
  return coeff[0] + coeff[1]*in_1 + coeff[2]*in_1*in_1 + coeff[3]*in_1*in_1*in_1
