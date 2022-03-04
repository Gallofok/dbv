import vapoursynth as vs
from vapoursynth import core
import mvsfunc as mvf
import havsfunc as haf
import math

def scale(val, bits):
    return val * ((1 << bits) - 1) // 255


def m4(x):
    return 16 if x < 16 else math.floor(x / 4 + 0.5) * 4


def Levels(clip, input_low, gamma, input_high, output_low, output_high, planes=None, coring=True):
    if planes is None:
        planes = list(range(clip.format.num_planes))

    bits = clip.format.bits_per_sample
    neutral = 1 << (bits - 1)
    peak = (1 << bits) - 1

    gamma = 1 / gamma
    divisor = input_high - input_low + (input_high == input_low)
    
    tvLow = scale(16, bits)
    tvHigh = [scale(235, bits), scale(240, bits)]
    scaleUp = peak / scale(235 - 16, bits)
    scaleDown = scale(235 - 16, bits) / peak

    isGray = clip.format.color_family == vs.GRAY
    chroma_planes = []
    if not isGray:
        if 1 in planes:
            chroma_planes.append(1)
        if 2 in planes:
            chroma_planes.append(2)
        
    def get_lut1(x):
        p = ((x - tvLow) * scaleUp - input_low) / divisor if coring else (x - input_low) / divisor
        p = min(max(p, 0), 1) ** gamma * (output_high - output_low) + output_low
        return min(max(math.floor(p * scaleDown + tvLow + 0.5), tvLow), tvHigh[0]) if coring else min(max(math.floor(p + 0.5), 0), peak)

    def get_lut2(x):
        q = math.floor((x - neutral) * (output_high - output_low) / divisor + neutral + 0.5)
        return min(max(q, tvLow), tvHigh[1]) if coring else min(max(q, 0), peak)
    
    if 0 in planes:
        clip = core.std.Lut(clip, planes=[0], function=get_lut1)
    if chroma_planes:
        clip = core.std.Lut(clip, planes=chroma_planes, function=get_lut2)
    
    return clip


def dering_process(clip, r=2.0, darkstr=0.0, brightstr=1.0, lowsens=50, highsens=50, ss=1.5, predering=False, nrmode=1, dering_mask=None):
    bits = clip.format.bits_per_sample
    x = clip.width
    y = clip.height
    x2 = m4(x / r)
    y2 = m4(y / r)
    xs = m4(x * ss)
    ys = m4(y * ss)
    
    # ps1 is a clip with artificially made halo in the image
    ps1 = core.std.MaskedMerge(clip, haf.MinBlur(clip, nrmode), dering_mask) if predering and dering_mask is not None else clip
    
    # enchanced the halo and compare it to original image
    halo = core.resize.Bicubic(ps1, x2, y2, filter_param_a=1/3, filter_param_b=1/3).resize.Bicubic(x, y, filter_param_a=1, filter_param_b=0)
    expr = 'z a - {multiple} / x y - {multiple} / - z a - {multiple} / 0.001 + / 255 * {LOS} - z a - {multiple} / 256 + 512 / {HIS} + * {multiple} *'.format(multiple=scale(1, bits), LOS=lowsens, HIS=highsens / 100)
     
     # generate a halomask to separate halo by complex caculating
    halotomask = core.std.Expr([core.std.Maximum(halo), core.std.Minimum(halo), core.std.Maximum(ps1), core.std.Minimum(clip)], [expr])
    pshalo = core.std.MaskedMerge(halo, ps1, halotomask)
    
  
    # resize halo and make it obvious
    pshalo2 = core.resize.Spline36(ps1, xs, ys)
    pshalo2 = core.std.Expr([pshalo2, core.std.Maximum(pshalo).resize.Bicubic(xs, ys, filter_param_a=1/3, filter_param_b=1/3), core.std.Minimum(pshalo).resize.Bicubic(xs, ys, filter_param_a=1/3, filter_param_b=1/3)], ['x y min z max'])
    pshalo2 = core.resize.Spline36(pshalo2, x, y)
    
    # Through smoothing and subtraction of clips, the halo and ringing of the dark field and bright field are eliminated respectively
    return core.std.Expr([ps1, pshalo2], ['x y < x x y - {DRK} * - x x y - {BRT} * - ?'.format(DRK=darkstr, BRT=brightstr)])


def repair_process(clip, pro1, pro2, rpmode=[13]):
    pro1_diff = core.std.MakeDiff(clip, pro1)
    pro2_diff = core.std.MakeDiff(pro1, pro2)
    maskpro1 = core.rgvs.Repair(pro1_diff, pro2_diff, rpmode)
    return core.std.Expr([clip, pro1_diff, maskpro1], ['x y z - -'])


def SHDdering_mod(clip, r=2.0, dering_pass=1, source=None):
    if source is None:
        source = clip
    if source.format.color_family != vs.GRAY:
        source = mvf.GetPlane(source)
    
    if dering_pass > 0:
        for i in range(dering_pass):
            dering1 = dering_process(clip, r=r)
            dering2 = dering_process(dering1, r=r)
            clip = repair_process(source, dering1, dering2)
            r = r / 2 + 0.5
    else:
        clip = dering_process(clip, r=r)

    return clip


def SHDdering_mod2(input, r=2.0, dering_pass=1, source=None):
    # For 16bits Y plane only
    assert input.format.bits_per_sample == 16 and input.format.color_family == vs.GRAY

    gamma = 3.0

    def Transform(input, gamma):
        limited_input = core.fmtc.bitdepth(input, bits=16, fulls=True, fulld=False).std.Limiter(4096, 60160)
        transform = Levels(limited_input, 4096, 1/gamma, 60160, 4096, 60160, coring=False)
        return limited_input, transform

    def InverseTransform(dering, limited_input, gamma):
        limited_dering = core.std.Limiter(dering, 4096, 60160)
        inverse_transform = Levels(limited_dering, 4096, gamma, 60160, 4096, 60160, coring=False)
        deringed = core.std.Expr([limited_input, dering, inverse_transform], ['y 4096 - 1 > 60160 y - 1 > and z x ?']).fmtc.bitdepth(bits=16, fulls=False, fulld=True)
        return deringed

    limited_input, input_transform = Transform(input, gamma)

    if source is not None:
        _, source_transform = Transform(source, gamma)
    else:
        source_transform = None

    dering = SHDdering_mod(input_transform, r=r, dering_pass=dering_pass, source=source_transform)

    inverse_transform = InverseTransform(dering, limited_input, gamma)

    return inverse_transform

"""
Usage:

flt = SHDdering_mod2(gray16, dering_pass=1, r=2.0)

# dering_pass: the number of passes, 0 (heavy) or 1 (weak)
# r: strength, 1.0 ~ 4.0
"""
