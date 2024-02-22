def calc_biquad(coeff, in_1, in_2):
    return (
        coeff[0]
        + coeff[1] * in_1
        + coeff[2] * in_1 * in_1
        + coeff[3] * in_2
        + coeff[4] * in_2 * in_2
        + coeff[5] * in_1 * in_2
    )


def calc_cubic(coeff, in_1):
    return (
        coeff[0]
        + coeff[1] * in_1
        + coeff[2] * in_1 * in_1
        + coeff[3] * in_1 * in_1 * in_1
    )


def calc_bicubic(coeff, in_1, in_2):
    return (
        coeff[0]
        + coeff[1] * in_1
        + coeff[2] * in_1 * in_1
        + coeff[3] * in_2
        + coeff[4] * in_2 * in_2
        + coeff[5] * in_1 * in_2
        + coeff[6] * in_1 * in_1 * in_1
        + coeff[7] * in_2 * in_2 * in_2
        + coeff[8] * in_1 * in_1 * in_2
        + coeff[9] * in_1 * in_2 * in_2
    )
