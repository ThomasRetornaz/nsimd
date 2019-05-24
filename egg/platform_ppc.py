# Copyright (c) 2019 Agenium Scale
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# This file gives the implementation for the Power PC platform.

import common

# -----------------------------------------------------------------------------
# Helpers

## Returns the 64 bits vector associated to a data type (eg:float32x2 for float32_t)

fmtspec = {}

## Returns the power pc type corresponding to the nsimd type
def ppc_vec_type(typ):
    if typ == 'u8':
        return '__vector unsigned char'
    elif typ == 'i8':
        return '__vector signed char'
    elif typ == 'u16':
        return '__vector unsigned short'
    elif typ == 'i16':
        return '__vector signed short'
    elif typ == 'u32':
        return '__vector unsigned int'
    elif typ == 'i32':
        return '__vector signed int'
    elif typ == 'f32':
        return '__vector float'
    else:
        raise ValueError('Unaivalble type "{}" for ppc'.format(typ))

## Returns the logical power pc type corresponding to the nsimd type
def ppc_vec_typel(typ):
    if typ[1:] == '8':
        return '__vector __bool char'
    elif typ == 'f16':
        return 'struct {__vector __bool int v1; __vector __bool int v2;}'
    elif typ[1:] == '16':
        return '__vector __bool short'
    elif typ[1:] == '32':
        return '__vector __bool int'
    else:
        raise ValueError('Unknown type "{}"'.format(typ))


## Whether or not the half float are emulated
def emulate_fp16(simd_ext):
    return True

## Emulate 64 bits types (for power7)
def emulate_64(op, simd_ext, typ, arity, logical_return):
    tmpl = ', '.join(['{{in{}}}.v{{{{i}}}}'.format(i).format(**fmtspec) \
                      for i in range(0, arity)])
    args1 = tmpl.format(i='1')
    args2 = tmpl.format(i='2')

    l='l' if logical_return else ''

    return '''nsimd_{simd_ext}_v{l}{typ} ret;
              ret.v1 = nsimd_{op}_cpu_{typ}({args1});
              ret.v2 = nsimd_{op}_cpu_{typ}({args2});
              return ret;'''. \
          format(l=l, op=op, args1=args1, args2=args2, **fmtspec)

## Emulate f16 bits types (for power7)
def emulate_16(op, simd_ext, arity, logical_return):
    tmpl = ', '.join(['{{in{}}}.v{{{{i}}}}'.format(i).format(**fmtspec) \
                      for i in range(0, arity)])
    args1 = tmpl.format(i='1')
    args2 = tmpl.format(i='2')

    l='l' if logical_return else ''

    return '''nsimd_{simd_ext}_v{l}f16 ret;
              ret.v1 = nsimd_{op}_{simd_ext}_f32({args1});
              ret.v2 = nsimd_{op}_{simd_ext}_f32({args2});
              return ret;'''. \
          format(l=l, op=op, args1=args1, args2=args2, **fmtspec)


# -----------------------------------------------------------------------------
# Implementation of mandatory functions for this module

def get_simd_exts():
    return ['power7', 'power8']

def get_type(simd_ext, typ):
    # TODO: power8
    if simd_ext in get_simd_exts():
        if typ == 'f64':
            return 'struct {double v1; double v2;}'
        elif typ == 'i64':
            return 'struct {i64 v1; i64 v2;}'
        elif typ == 'u64':
            return 'struct {u64 v1; u64 v2;}'
        elif typ == 'f16':
            return 'struct {__vector float v1; __vector float v2;}'
        else:
            return ppc_vec_type(typ)
    else:
        raise ValueError('Unknown SIMD extension "{}"'.format(simd_ext))

def get_logical_type(simd_ext, typ):
    if typ not in common.types:
        raise ValueError('Unknown type "{}"'.format(typ))
    elif typ == 'i64':
        return 'struct {i64 v1; i64 v2;}'
    elif typ == 'u64':
        return 'struct {u64 v1; u64 v2;}'
    elif typ == 'f64':
        return 'struct {u64 v1; u64 v2;}'
    else:
        return ppc_vec_typel(typ)

def get_nb_registers(simd_ext):
    if simd_ext in 'power7':
        #TODO
        return '32'
    elif simd_ext == 'power8':
        #TODO
        return '64'
    else:
        raise ValueError('Unknown SIMD extension "{}"'.format(simd_ext))

def get_SoA_type(simd_ext, typ, deg):
    if simd_ext != 'sve':
        raise ValueError('Unknown SIMD extension "{}"'.format(simd_ext))
    return '{}x{}_t'.format(sve_typ(typ)[0:-2], deg)

def has_compatible_SoA_types(simd_ext):
    if simd_ext in get_simd_exts():
        return False
    else:
        raise ValueError('Unknown SIMD extension "{}"'.format(simd_ext))

def get_additional_include(func, platform, simd_ext):
    ret = '''#include <nsimd/cpu/cpu/{}.h>
             '''.format(func)
    ret +='''#include <nsimd/ppc/{simd_ext}/put.h>
             '''.format(simd_ext=simd_ext)

    if func == 'neq':
        ret +='''#include <nsimd/ppc/{simd_ext}/eq.h>
                 #include <nsimd/ppc/{simd_ext}/notl.h>
            '''.format(simd_ext=simd_ext)

    if func in ['loadlu', 'loadla']:
        ret += '''#include <nsimd/ppc/{simd_ext}/eq.h>
                  #include <nsimd/ppc/{simd_ext}/set1.h>
                  #include <nsimd/ppc/{simd_ext}/{load}.h>
                  #include <nsimd/ppc/{simd_ext}/notl.h>
                  '''.format(load='load' + func[5], **fmtspec)

    if func in ['storelu']:
        ret += '''#include <nsimd/ppc/{simd_ext}/if_else1.h>
                  #include <nsimd/ppc/{simd_ext}/set1.h>
                  '''.format(**fmtspec)

    if func in ['shr', 'shl']:
        ret += '''#include <nsimd/ppc/{simd_ext}/set1.h>
                  '''.format(**fmtspec)

    if func == 'nbtrue':
        ret +='''#include <nsimd/ppc/{simd_ext}/addv.h>
            '''.format(simd_ext=simd_ext)

    return ret

# -----------------------------------------------------------------------------
# Get SoA types

def get_soa_typ(simd_ext, typ, deg):
    ntyp = get_type(simd_ext, typ) if typ != 'f16' else 'float16x8_t'
    return '{}x{}_t'.format(ntyp[:-2], deg)

# -----------------------------------------------------------------------------

## Loads of degree 1, 2, 3 and 4, aligned

def load1234a(simd_ext, typ, deg):
    if deg == 1:
        if typ[1:] == '64':
            return '''nsimd_{simd_ext}_v{typ} ret;
                      ret.v1 = {in0}[0];
                      ret.v2 = {in0}[1];
                      return ret;'''.format (**fmtspec)
        elif typ == 'f16':
            return '''
                 /* Note that we can do much better but is it useful? */
                 nsimd_{simd_ext}_vf16 ret;
                 f32 buf[4];
                 buf[0] = nsimd_u16_to_f32(*(u16*){in0});
                 buf[1] = nsimd_u16_to_f32(*((u16*){in0} + 1));
                 buf[2] = nsimd_u16_to_f32(*((u16*){in0} + 2));
                 buf[3] = nsimd_u16_to_f32(*((u16*){in0} + 3));
                 ret.v1 = vec_ld(0, buf);
                 buf[0] = nsimd_u16_to_f32(*((u16*){in0} + 4));
                 buf[1] = nsimd_u16_to_f32(*((u16*){in0} + 5));
                 buf[2] = nsimd_u16_to_f32(*((u16*){in0} + 6));
                 buf[3] = nsimd_u16_to_f32(*((u16*){in0} + 7));
                 ret.v2 = vec_ld(0, buf);
                 return ret;;
               '''.format(**fmtspec)
        else:
            return 'return vec_ld(0, {in0});'.format(**fmtspec)
    else:
        #TODO
        return ''

## Stores of degree 1, 2, 3 and 4 aligned

def store1234a(simd_ext, typ, deg):
    #TODO
    if deg == 1:
        if typ[1:]=='64':
            return '''{in0}[0] = {in1}.v1;
                      {in0}[1] = {in1}.v2; '''.format (**fmtspec)
        elif typ=='f16':
                return \
                  '''/* Note that we can do much better but is it useful? */
                     f32 buf[4];
                     vec_st({in1}.v1, 0, buf);
                     *((u16*){in0}    ) = nsimd_f32_to_u16(buf[0]);
                     *((u16*){in0} + 1) = nsimd_f32_to_u16(buf[1]);
                     *((u16*){in0} + 2) = nsimd_f32_to_u16(buf[2]);
                     *((u16*){in0} + 3) = nsimd_f32_to_u16(buf[3]);
                     vec_st({in1}.v2, 0, buf);
                     *((u16*){in0} + 4) = nsimd_f32_to_u16(buf[0]);
                     *((u16*){in0} + 5) = nsimd_f32_to_u16(buf[1]);
                     *((u16*){in0} + 6) = nsimd_f32_to_u16(buf[2]);
                     *((u16*){in0} + 7) = nsimd_f32_to_u16(buf[3]);
                   '''.format(**fmtspec)
        else:
            return 'vec_st({in1}, 0, {in0});'.format(**fmtspec)
    else:
        return ''

## Loads of degree 1, 2, 3 and 4, unaligned
def load1234u(simd_ext, typ, deg):
    if deg == 1:
        if typ == 'f16':
            return \
             '''/* Note that we can do much better but is it useful? */
                 nsimd_{simd_ext}_vf16 ret;
                 f32 buf[4];
                 buf[0] = nsimd_u16_to_f32(*(u16*){in0});
                 buf[1] = nsimd_u16_to_f32(*((u16*){in0} + 1));
                 buf[2] = nsimd_u16_to_f32(*((u16*){in0} + 2));
                 buf[3] = nsimd_u16_to_f32(*((u16*){in0} + 3));
                 ret.v1 = *((__vector float*)buf);
                 buf[0] = nsimd_u16_to_f32(*((u16*){in0} + 4));
                 buf[1] = nsimd_u16_to_f32(*((u16*){in0} + 5));
                 buf[2] = nsimd_u16_to_f32(*((u16*){in0} + 6));
                 buf[3] = nsimd_u16_to_f32(*((u16*){in0} + 7));
                 ret.v2 = *((__vector float*)buf);
                 return ret;'''.format(**fmtspec)
        elif typ[1:] == '64':
            return '''nsimd_{simd_ext}_v{typ} ret;
                      ret.v1 = {in0}[0];
                      ret.v2 = {in0}[1];
                      return ret;'''.format (**fmtspec)
        elif typ in common.types:
            return 'return *(({ppc_typ}*) {in0});'.\
                    format(ppc_typ=ppc_vec_type(typ), **fmtspec)
        else:
            raise ValueError('Unknown type "{}"'.format(typ))
    else:
        #TODO
        return ''

## Stores of degree 1, 2, 3 and 4 unaligned

def store1234u(simd_ext, typ, deg):
    if deg == 1:
        if typ == 'f16':
            return \
             '''f32 buf[4];
                 *((__vector float*)buf) = {in1}.v1;
                 *((u16*){in0}    ) = nsimd_f32_to_u16(buf[0]);
                 *((u16*){in0} + 1) = nsimd_f32_to_u16(buf[1]);
                 *((u16*){in0} + 2) = nsimd_f32_to_u16(buf[2]);
                 *((u16*){in0} + 3) = nsimd_f32_to_u16(buf[3]);
                 *((__vector float*)buf) = {in1}.v2;
                 *((u16*){in0} + 4) = nsimd_f32_to_u16(buf[0]);
                 *((u16*){in0} + 5) = nsimd_f32_to_u16(buf[1]);
                 *((u16*){in0} + 6) = nsimd_f32_to_u16(buf[2]);
                 *((u16*){in0} + 7) = nsimd_f32_to_u16(buf[3]);
               '''.format( **fmtspec)
        elif typ[1:] == '64':
            return '''{in0}[0] = {in1}.v1;
                      {in0}[1] = {in1}.v2;'''.format (**fmtspec)
        elif typ in common.types:
            return '*(({ppc_typ}*) {in0}) = {in1};'.\
                    format(ppc_typ=ppc_vec_type(typ), **fmtspec)
        else:
            raise ValueError('Unknown type "{}"'.format(typ))
    else:
        #TODO
        return ''

## Length
def len1(simd_ext, typ):
    return 'return (128 / {});'.format(int(typ[1:]))

## Function for all the operators that take 2 operands and whose Altivec
## function is vec_opname()
def simple_op2(op, simd_ext, typ):
    cpuop = {'mul': '*', 'div': '/', 'add': '+', 'sub': '-'}
    if simd_ext == 'power7':
        if typ in ['f64', 'i64', 'u64'] :
            return emulate_64(op, simd_ext, typ, 2, False)

    if typ == 'f16' :
        return emulate_16(op, simd_ext, 2, False)

    return 'return {in0} {op} {in1};'.format(op=cpuop[op], **fmtspec)

## Binary operators: and, or, xor, andnot

def bop2(op, simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64(op, simd_ext, typ, 2, False)
    elif typ == 'f16':
        return emulate_16(op, simd_ext, 2, False)
    else:
        ppcop = {'orb': 'or', 'xorb': 'xor', 'andb': 'and', 'andnotb': 'andc'}
        return 'return vec_{op}({in0}, {in1});'. \
               format(op=ppcop[op], **fmtspec)

## Logical operators: and, or, xor, andnot

def lop2(op, simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64(op, simd_ext, typ, 2, True)
    elif typ == 'f16':
        return emulate_16(op, simd_ext, 2, True)
    else:
        ppcop = {'orl': 'or', 'xorl': 'xor', 'andl': 'and', 'andnotl': 'andc'}
        return 'return vec_{op}({in0}, {in1});'. \
               format(op=ppcop[op], **fmtspec)

## Binary not

def notb1(simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64('notb', simd_ext, typ, 1, False)
    elif typ == 'f16':
        return emulate_16('notb', simd_ext, 1, False)
    else:
        return 'return vec_nor({in0}, {in0});'.format(**fmtspec)

## Logical not

def lnot1(simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64('notl', simd_ext, typ, 1, True)
    elif typ == 'f16':
        return emulate_16('notl', simd_ext, 1, True)
    else:
        return 'return vec_nor({in0}, {in0});'.format(**fmtspec)

## Square root

def sqrt1(simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64('sqrt', simd_ext, typ, 1, False)
    elif typ == 'f16':
        return emulate_16('sqrt', simd_ext, 1, False)
    else:
        return '''
                /* Can't use vec_rsqrte because the precision is too low */
                nat i;
                {typ} buf[{size}];
                vec_st({in0}, 0, buf);
                for (i=0; i<{size}; ++i) {{
                    buf[i] = nsimd_sqrt_cpu_{typ}(buf[i]);
                }}
                return vec_ld(0, buf);
                '''.format(size=128//int(typ[1:]), **fmtspec)

## Shifts

def shl_shr(op, simd_ext, typ):
    if typ[1:] == '64':
        return '''nsimd_{simd_ext}_v{typ} ret;
                  ret.v1 = nsimd_{op}_cpu_{typ}({in0}.v1, {in1});
                  ret.v2 = nsimd_{op}_cpu_{typ}({in0}.v2, {in1});
                  return ret;'''. \
              format(op=op, **fmtspec)
    elif typ == 'f16':
        return '''nsimd_{simd_ext}_v{typ} ret;
                  ret.v1 = nsimd_{op}_{nsimd_ext}_f32({in0}.v1, {in1});
                  ret.v2 = nsimd_{op}_{nsimd_ext}_f32({in0}.v2, {in1});
                  return ret;'''. \
              format(op=op, **fmtspec)
    else:
        ppcop = {'shl': 'sl', 'shr': 'sr'}
        return '''
             nsimd_{simd_ext}_vu{type_size} tmp;
             tmp = nsimd_set1_{simd_ext}_u{type_size}({in1});
             return vec_{op}({in0}, tmp);'''. \
                     format(op=ppcop[op], type_size=typ[1:], **fmtspec)

# Set1: splat functions
def set1(simd_ext, typ):
    if typ[1:] == '64':
        return '''nsimd_{simd_ext}_v{typ} ret;
                  ret.v1 = {in0};
                  ret.v2 = {in0};
                  return ret;'''.format(**fmtspec)
    elif typ == 'f16':
        return '''nsimd_{simd_ext}_vf16 ret;
                  f32 f = nsimd_f16_to_f32({in0});
                  ret.v1 = nsimd_set1_{simd_ext}_f32(f);
                  ret.v2 = nsimd_set1_{simd_ext}_f32(f);
                  return ret;'''.format(**fmtspec)
    else:
        nvar_in_vec = int(128 / (int)(typ[1:]))
        values = ', '.join(['{in0}'.format(**fmtspec) for i in range(0,nvar_in_vec)])
        return '''{vec} tmp = {{{val}}};
                  return tmp;''' \
                .format(val=values, vec=ppc_vec_type(typ), **fmtspec)

## Comparison operators: ==, <, <=, >, >=

def cmp2(op, simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64(op, simd_ext, typ, 2, True)
    elif typ == 'f16':
        return emulate_16(op, simd_ext, 2, True)
    else:
        return 'return vec_cmp{op}({in0}, {in1});'. \
                format(op=op, **fmtspec)

## Not equal

def neq2(simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64('ne', simd_ext, typ, 2, True)
    elif typ == 'f16':
        return emulate_16('ne', simd_ext, 2, True)
    else:
        return '''return nsimd_notl_{simd_ext}_{typ}(
                      nsimd_eq_{simd_ext}_{typ}({in0}, {in1}));'''. \
                      format(**fmtspec)

## If_else

def if_else3(simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64('if_else1', simd_ext, typ, 3, False)
    elif typ == 'f16':
        return emulate_16('if_else1', simd_ext, 3, False)
    else:
        return 'return vec_sel({in2}, {in1}, {in0});'.format(**fmtspec)


## Minimum and maximum

def minmax2(op, simd_ext, typ):
    if typ[1:] == '64':
        return emulate_64(op, simd_ext, typ, 2, False)
    elif typ == 'f16':
        return emulate_16(op, simd_ext, 2, False)
    else:
        return 'return vec_{op}({in0},{in1});'.format(op=op, **fmtspec)


## Abs

def abs1(simd_ext, typ):
    if typ == 'f16':
        return emulate_16('abs', simd_ext, 1, False)
    elif typ[0] == 'u':
        return 'return {in0};'.format(**fmtspec)
    elif typ[1:] == '64':
        return emulate_64('abs', simd_ext, typ, 1, False)
    else:
        return 'return vec_abs({in0});'.format(**fmtspec)

## Round, trunc, ceil and round_to_even

def round1(op, simd_ext, typ):
    ppcop = {'round': 'round', 'trunc': 'trunc', 'ceil': 'ceil',
            'floor':'floor', 'round_to_even': 'round'}
    if typ[0] == 'i' or typ[0] == 'u':
        return 'return {in0};'.format(**fmtspec)
    elif typ == 'f16':
        return emulate_16(op, simd_ext, 1, False)
    elif typ == 'f32':
        return 'return vec_{op}({in0});'.format(op=ppcop[op], **fmtspec)
    elif typ == 'f64':
        return emulate_64(op, simd_ext, typ, 1, False)
    else: 
        raise ValueError('Unknown round: "{}" for type : "{}"'. \
                format(op, typ))

## FMA
def fma(simd_ext, typ):
    if typ == 'f32':
        return 'return vec_madd({in0}, {in1}, {in2});'.format(**fmtspec)
    elif typ == 'f16':
        return emulate_16('fma', simd_ext, 3, False)
    elif typ[1:] == '64':
        return emulate_64('fma', simd_ext, typ, 3, False)
    else:
        return 'return {in0}*{in1}+{in2};'.format(**fmtspec)

## FNMA
def fnma(simd_ext, typ):
    if typ == 'f32':
        return 'return vec_nmsub({in0}, {in1}, {in2});'.format(**fmtspec)
    elif typ == 'f16':
        return emulate_16('fnma', simd_ext, 3, False)
    elif typ[1:] == '64':
        return emulate_64('fnma', simd_ext, typ, 3, False)
    else:
        return 'return -{in0}*{in1}+{in2};'.format(**fmtspec)

## FMS
def fms(op, simd_ext, typ):
    if typ == 'f32':
        return 'return vec_madd({in0}, {in1}, -{in2});'.format(**fmtspec)
    elif typ == 'f16':
        return emulate_16('fms', simd_ext, 3, False)
    elif typ[1:] == '64':
        return emulate_64('fms', simd_ext, typ, 3, False)
    else:
        return 'return {in0}*{in1}-{in2};'.format(**fmtspec)

## FNMS
def fnms(op, simd_ext, typ):
    if typ == 'f32':
        return 'return vec_nmsub({in0}, {in1}, -{in2});'.format(**fmtspec)
    elif typ == 'f16':
        return emulate_16('fnms', simd_ext, 3, False)
    elif typ[1:] == '64':
        return emulate_64('fnms', simd_ext, typ, 3, False)
    else:
        return 'return -{in0}*{in1}-{in2};'.format(**fmtspec)

## Neg

def neg1(simd_ext, typ):
    if typ[1] == 'u':
        return '''
            return nsimd_reinterpret_{simd_ext}_i{nbits}_u{nbits}(
                        nsimd_neg_{simd_ext}_i{nbits}(
                            nsimd_reinterpret_{simd_ext}_u{nbits}_i{nbits}({in0})));
e       '''.format(nbits=typ[1:], **fmtspec)

    elif typ[1:] == '64':
        return emulate_64('neg', simd_ext, typ, 1, False)
    elif typ == 'f16':
        return emulate_16('neg', simd_ext, 1, False)
    else:
        return 'return -{in0};'.format(**fmtspec)


## Reciprocals
def recs1(op, simd_ext, typ):
    if typ == 'f16':
        return emulate_16(op, simd_ext, 1, False)
    elif typ[1:] == '64':
        return emulate_64(op, simd_ext, typ, 1, False)
    elif op == 'rec11':
        return 'return vec_re({in0});'.format(**fmtspec)
    elif op == 'rec':
        return 'return ({typ})(1)/{in0};'.format(**fmtspec)
    elif op == 'rsqrt11':
        return 'return vec_rsqrte({in0});'.format(**fmtspec)

## Load of logicals
def loadl(aligned, simd_ext, typ):
    return \
    '''/* This can surely be improved but it is not our priority. */
       return nsimd_notl_{simd_ext}_{typ}(nsimd_eq_{simd_ext}_{typ}(
                nsimd_load{align}_{simd_ext}_{typ}(
                  {in0}), nsimd_set1_{simd_ext}_{typ}({zero})));'''. \
       format(align='a' if aligned else 'u',
              zero = 'nsimd_f32_to_f16(0.0f)' if typ == 'f16'
              else '({})0'.format(typ), **fmtspec)

## Store of logicals

def storel(aligned, simd_ext, typ):
    return \
    '''/* This can surely be improved but it is not our priority. */
       nsimd_store{align}_{simd_ext}_{typ}({in0},
         nsimd_if_else1_{simd_ext}_{typ}({in1},
           nsimd_set1_{simd_ext}_{typ}({one}),
           nsimd_set1_{simd_ext}_{typ}({zero})));'''. \
       format(align = 'a' if aligned else 'u',
              one = 'nsimd_f32_to_f16(1.0f)' if typ == 'f16'
              else '({})1'.format(typ),
              zero = 'nsimd_f32_to_f16(0.0f)' if typ == 'f16'
              else '({})0'.format(typ), **fmtspec)

## All and any
def allany1(op, simd_ext, typ):
    binop = '&&' if  op == 'all' else '||'

    if typ == 'f16':
        return \
        '''return nsimd_{op}_{simd_ext}_f32({in0}.v1) {binop}
                  nsimd_{op}_{simd_ext}_f32({in0}.v2);'''. \
                  format(op=op, binop=binop, **fmtspec)
    elif typ[1:] == '64':
        return 'return {in0}.v1 {binop} {in0}.v2;'. \
               format(binop=binop, **fmtspec)
    else:
        values = ', '.join(['0x0' for i in range(0,16)])
        return \
        '''nsimd_{simd_ext}_vu8 reg = {{{values}}};
           return vec_{op}_gt(({vec_type}){in0}, ({vec_type})reg);'''\
        .format(values=values, vec_type=ppc_vec_type('u'+typ[1:]), op=op, 
                **fmtspec)

## nbtrue

def nbtrue1(simd_ext, typ):
    if typ == 'f16':
        return \
        '''return nsimd_nbtrue_{simd_ext}_f32({in0}.v1) +
                  nsimd_nbtrue_{simd_ext}_f32({in0}.v2);'''. \
                  format(**fmtspec)
    elif typ[1:] == '64':
        return 'return -(int)((i64)({in0}.v1) + (i64)({in0}.v2));'. \
               format(**fmtspec)
    else:
        # TODO: see if their is a faster way to do it
        values = ', '.join(['0xFF' for i in range(0,16)])
        return \
        '''return nsimd_addv_{simd_ext}_u{type_size}(({ppc_typ}){in0} / ({ppc_typ})({in0}));
        '''.format(val=values,
                type_size=typ[1:], 
                ppc_typ=ppc_vec_type('u'+typ[1:]), 
                **fmtspec)

## Reinterpret logical

def reinterpretl1(simd_ext, from_typ, to_typ):
    if from_typ == to_typ:
        return 'return {in0};'.format(**fmtspec)
    elif from_typ[1:] == '64':
        return \
        '''nsimd_{simd_ext}_vl{to_typ} ret;
           ret.v1 = ({to_typ})({in0}.v1);
           ret.v2 = ({to_typ})({in0}.v2);
           return ret;'''.format(**fmtspec)
    elif from_typ == 'f16':
        return \
        '''nsimd_{simd_ext}_vf16 ret;
           {to_typ} buf[8];
           f32 buf_conv[4];

           vec_st((__vector float){in0}.v1, 0, buf_conv);
           buf[0] = ({to_typ})nsimd_f32_to_u16(buf_conv[0]);
           buf[1] = ({to_typ})nsimd_f32_to_u16(buf_conv[1]);
           buf[2] = ({to_typ})nsimd_f32_to_u16(buf_conv[2]);
           buf[3] = ({to_typ})nsimd_f32_to_u16(buf_conv[3]);

           vec_st((__vector float){in0}.v2, 0, buf_conv);
           buf[4] = ({to_typ})nsimd_f32_to_u16(buf_conv[0]);
           buf[5] = ({to_typ})nsimd_f32_to_u16(buf_conv[1]);
           buf[6] = ({to_typ})nsimd_f32_to_u16(buf_conv[2]);
           buf[7] = ({to_typ})nsimd_f32_to_u16(buf_conv[3]);

           return ({ppc_to_typ})vec_ld(0, buf);'''.\
           format(ppc_to_typ=ppc_vec_typel(to_typ), **fmtspec)
    elif to_typ == 'f16':
        return \
        '''nsimd_{simd_ext}_vlf16 ret;
           {from_typ} buf_conv[8];
           f32 buf[4];

           vec_st({in0}, 0, buf_conv);

           buf[0] = nsimd_u16_to_f32(buf_conv[0]);
           buf[1] = nsimd_u16_to_f32(buf_conv[1]);
           buf[2] = nsimd_u16_to_f32(buf_conv[2]);
           buf[3] = nsimd_u16_to_f32(buf_conv[3]);
           ret.v1 = (__vector __bool int) vec_ld(0, buf);

           buf[0] = nsimd_u16_to_f32(buf_conv[4]);
           buf[1] = nsimd_u16_to_f32(buf_conv[5]);
           buf[2] = nsimd_u16_to_f32(buf_conv[6]);
           buf[3] = nsimd_u16_to_f32(buf_conv[7]);
           ret.v2 = (__vector __bool int) vec_ld(0, buf);

           return ret;'''.format(**fmtspec)
    else:
        return 'return ({ppc_to_typ}) {in0};'. \
                format(ppc_to_typ=ppc_vec_typel(to_typ), **fmtspec)

## Convert

def convert1(simd_ext, from_typ, to_typ):
    if from_typ == to_typ:
        return 'return {in0};'.format(**fmtspec)
    elif from_typ == 'f16':
        if to_typ == 'u16':
            return \
            '''return vec_packsu(vec_ctu({in0}.v1, 0),
                                 vec_ctu({in0}.v2, 0));'''.\
            format(**fmtspec)
        elif to_typ == 'i16':
            return \
            '''return vec_packs(vec_cts({in0}.v1, 0), 
                                vec_cts({in0}.v2, 0));'''.\
            format(**fmtspec)

    elif to_typ == 'f16':
        if from_typ == 'u16':
            return \
            '''nsimd_{simd_ext}_vf16 ret;
               ret.v1=vec_ctf(vec_unpackh((__vector short){in0}), 0);
               ret.v2=vec_ctf(vec_unpackl((__vector short){in0}), 0);

               /* Unpack extends the sign, we need to remove the extra 1s */
               nsimd_{simd_ext}_vu32 mask = {{0xFFFF, 0xFFFF, 0xFFFF, 0xFFFF}};
               ret.v1 = vec_and(ret.v1, (__vector float)mask);
               ret.v2 = vec_and(ret.v2, (__vector float)mask);
               
               return ret;'''.format(**fmtspec)
        elif from_typ == 'i16':
            return \
            '''nsimd_{simd_ext}_vf16 ret;
               ret.v1=vec_ctf(vec_unpackh({in0}), 0);
               ret.v2=vec_ctf(vec_unpackl({in0}), 0);
               return ret;'''.format(**fmtspec)
    elif from_typ[1:] == '64':
        return \
        '''nsimd_{simd_ext}_v{to_typ} ret;
           ret.v1 = ({to_typ})({in0}.v1);
           ret.v2 = ({to_typ})({in0}.v2);
           return ret;'''.format(**fmtspec)
    elif from_typ == 'f32' and to_typ == 'i32':
        return 'return vec_cts({in0}, 0);'.format(**fmtspec)
    elif from_typ == 'f32' and to_typ == 'u32':
        return 'return vec_ctu({in0}, 0);'.format(**fmtspec)
    elif (from_typ == 'i32' or from_typ == 'u32') and to_typ == 'f32':
        return 'return vec_ctf({in0}, 0);'.format(**fmtspec)
    elif from_typ in common.iutypes and to_typ in common.iutypes:
        return 'return ({cast}) {in0};'. \
                format(cast=ppc_vec_type(to_typ), **fmtspec)
    else:
        raise ValueError('Unknown conversion: "{}" to "{}"'. \
                format(from_typ, to_typ))

## Reinterpret

def reinterpret1(simd_ext, from_typ, to_typ):
    if from_typ == to_typ:
        return 'return {in0};'.format(**fmtspec)
    elif from_typ[1:] == '64':
        return '''
            nsimd_{simd_ext}_v{to_typ} ret;
            ret.v1 = *({to_typ}*)(&{in0}.v1);
            ret.v2 = *({to_typ}*)(&{in0}.v2);
            return ret;
        '''.format(**fmtspec)
    elif from_typ == 'f16':
        return '''nsimd_{simd_ext}_vf16 ret;
                  {to_typ} buf[8];
                  f32 buf_conv[4];

                  vec_st({in0}.v1, 0, buf_conv);
                  buf[0] = ({to_typ})nsimd_f32_to_u16(buf_conv[0]);
                  buf[1] = ({to_typ})nsimd_f32_to_u16(buf_conv[1]);
                  buf[2] = ({to_typ})nsimd_f32_to_u16(buf_conv[2]);
                  buf[3] = ({to_typ})nsimd_f32_to_u16(buf_conv[3]);

                  vec_st({in0}.v2, 0, buf_conv);
                  buf[4] = ({to_typ})nsimd_f32_to_u16(buf_conv[0]);
                  buf[5] = ({to_typ})nsimd_f32_to_u16(buf_conv[1]);
                  buf[6] = ({to_typ})nsimd_f32_to_u16(buf_conv[2]);
                  buf[7] = ({to_typ})nsimd_f32_to_u16(buf_conv[3]);

                  return vec_ld(0, buf);'''.format(**fmtspec)
    elif to_typ == 'f16':
        return '''nsimd_{simd_ext}_vf16 ret;
                  {from_typ} buf_conv[8];
                  f32 buf[4];

                  vec_st({in0}, 0, buf_conv);

                  buf[0] = nsimd_u16_to_f32(buf_conv[0]);
                  buf[1] = nsimd_u16_to_f32(buf_conv[1]);
                  buf[2] = nsimd_u16_to_f32(buf_conv[2]);
                  buf[3] = nsimd_u16_to_f32(buf_conv[3]);
                  ret.v1 = vec_ld(0, buf);

                  buf[0] = nsimd_u16_to_f32(buf_conv[4]);
                  buf[1] = nsimd_u16_to_f32(buf_conv[5]);
                  buf[2] = nsimd_u16_to_f32(buf_conv[6]);
                  buf[3] = nsimd_u16_to_f32(buf_conv[7]);
                  ret.v2 = vec_ld(0, buf);
                  return ret;'''.format(**fmtspec)
    else:
        return 'return ({typ_ppc}) {in0};'. \
                format(typ_ppc=ppc_vec_type(to_typ), **fmtspec)

## reverse

def reverse1(simd_ext, typ):
    if typ == 'f16':
        return '''nsimd_{simd_ext}_vf16 ret;
                  ret.v1 = nsimd_reverse_{simd_ext}_f32({in0}.v2);
                  ret.v2 = nsimd_reverse_{simd_ext}_f32({in0}.v1);
                  return ret;'''.format(**fmtspec)
    elif typ[1:] == '8':
        return '''__vector unsigned char perm = 
                       {{0x0F, 0x0E, 0x0D, 0x0C, 0x0B, 0x0A, 0x09, 0x08,
                         0x07, 0x06, 0x05, 0x04, 0x03, 0x02, 0x01, 0x00}};
                  return vec_perm({in0}, perm, perm);'''.format (**fmtspec)
    elif typ[1:] == '16':
        return ''' __vector unsigned char perm = 
                       {{0x0E, 0x0F, 0x0C, 0x0D, 0x0A, 0x0B, 0x08, 0x09,
                         0x06, 0x07, 0x04, 0x05, 0x02, 0x03, 0x00, 0x01}};
                   return vec_perm({in0}, perm, perm);'''.format (**fmtspec)
    elif typ[1:] == '32':
        return ''' __vector unsigned char perm = 
                        {{0x0C, 0x0D, 0x0E, 0x0F, 0x08, 0x09, 0x0A, 0x0B,
                          0x04, 0x05, 0x06, 0x07, 0x00, 0x01, 0x02, 0x03}};
                   return vec_perm({in0}, perm, perm);'''.format (**fmtspec)
    elif typ[1:] == '64':
        return '''nsimd_{simd_ext}_v{typ} ret;
                  ret.v1 = {in0}.v2;
                  ret.v2 = {in0}.v1;
                  return ret;'''.format (**fmtspec)

## Horizontal sum

def addv(simd_ext, typ):
    if typ == 'f16':
        return '''return nsimd_f32_to_f16(nsimd_addv_{simd_ext}_f32({in0}.v1) 
                                        + nsimd_addv_{simd_ext}_f32({in0}.v2));'''. \
                             format(**fmtspec)
    elif typ[1:] == '64':
        return 'return {in0}.v1 + {in0}.v2;'.format(**fmtspec)
    else:
        return '''
                /* Can't use vec_sums because it uses saturate sum */
                nat i;
                {typ} ret = ({typ}) 0;
                {typ} buf[{size}];
                vec_st({in0}, 0, buf);
                for (i=0; i<{size}; ++i) {{
                    ret += buf[i];
                }}
                return ret;
                '''.format(size=128//int(typ[1:]), **fmtspec)


## get_impl function

def get_impl(func, simd_ext, from_typ, to_typ):
    global fmtspec

    fmtspec = {
      'simd_ext': simd_ext,
      'typ': from_typ,
      'styp': get_type(simd_ext, from_typ),
      'from_typ': from_typ,
      'to_typ': to_typ,
      'in0': common.in0,
      'in1': common.in1,
      'in2': common.in2,
      'in3': common.in3,
      'in4': common.in4,
      'in5': common.in5,
      'typnbits': from_typ[1:]
    }

    impls = {
        'loada': 'load1234a(simd_ext, from_typ, 1)',
        'load2a': 'load1234a(simd_ext, from_typ, 2)',
        'load3a': 'load1234a(simd_ext, from_typ, 3)',
        'load4a': 'load1234a(simd_ext, from_typ, 4)',
        'loadu': 'load1234u(simd_ext, from_typ, 1)',
        'load2u': 'load1234u(simd_ext, from_typ, 2)',
        'load3u': 'load1234u(simd_ext, from_typ, 3)',
        'load4u': 'load1234u(simd_ext, from_typ, 4)',
        'storea': 'store1234a(simd_ext, from_typ, 1)',
        'store2a': 'store1234a(simd_ext, from_typ, 2)',
        'store3a': 'store1234a(simd_ext, from_typ, 3)',
        'store4a': 'store1234a(simd_ext, from_typ, 4)',
        'storeu': 'store1234u(simd_ext, from_typ, 1)',
        'store2u': 'store1234u(simd_ext, from_typ, 2)',
        'store3u': 'store1234u(simd_ext, from_typ, 3)',
        'store4u': 'store1234u(simd_ext, from_typ, 4)',
        'andb': 'bop2("andb", simd_ext, from_typ)',
        #Binary => chaque bit du vecteur compte
        'xorb': 'bop2("xorb", simd_ext, from_typ)',
        'orb': 'bop2("orb", simd_ext, from_typ)',
        'andl': 'lop2("andl", simd_ext, from_typ)',
        # Logical => type de vecteur spéciale
        'xorl': 'lop2("xorl", simd_ext, from_typ)',
        'orl': 'lop2("orl", simd_ext, from_typ)',
        'notb': 'notb1(simd_ext, from_typ)',
        'notl': 'lnot1(simd_ext, from_typ)',
        'andnotb': 'bop2("andnotb", simd_ext, from_typ)',
        'andnotl': 'lop2("andnotl", simd_ext, from_typ)',
        'add': 'simple_op2("add", simd_ext, from_typ)',
        'sub': 'simple_op2("sub", simd_ext, from_typ)',
        'div': 'simple_op2("div", simd_ext, from_typ)',
        'sqrt': 'sqrt1(simd_ext, from_typ)',
        'len': 'len1(simd_ext, from_typ)',
        'mul': 'simple_op2("mul", simd_ext, from_typ)',
        'shl': 'shl_shr("shl", simd_ext, from_typ)',
        'shr': 'shl_shr("shr", simd_ext, from_typ)',
        'set1': 'set1(simd_ext, from_typ)',
        'eq': 'cmp2("eq", simd_ext, from_typ)',
        'lt': 'cmp2("lt", simd_ext, from_typ)',
        'le': 'cmp2("le", simd_ext, from_typ)',
        'gt': 'cmp2("gt", simd_ext, from_typ)',
        'ge': 'cmp2("ge", simd_ext, from_typ)',
        'ne': 'neq2(simd_ext, from_typ)',
        'if_else1': 'if_else3(simd_ext, from_typ)',
        'min': 'minmax2("min", simd_ext, from_typ)',
        'max': 'minmax2("max", simd_ext, from_typ)',
        'loadla': 'loadl(True, simd_ext, from_typ)',
        'loadlu': 'loadl(False, simd_ext, from_typ)',
        'storela': 'storel(True, simd_ext, from_typ)',
        'storelu': 'storel(False, simd_ext, from_typ)',
        'abs': 'abs1(simd_ext, from_typ)',
        'fma': 'fma(simd_ext, from_typ)',
        'fnma': 'fnma(simd_ext, from_typ)',
        'fms': 'fms("fms", simd_ext, from_typ)',
        'fnms': 'fnms("fnms", simd_ext, from_typ)',
        'ceil': 'round1("ceil", simd_ext, from_typ)',
        'floor': 'round1("floor", simd_ext, from_typ)',
        'trunc': 'round1("trunc", simd_ext, from_typ)',
        'round_to_even': 'round1("round_to_even", simd_ext, from_typ)',
        'all': 'allany1("all", simd_ext, from_typ)',
        'any': 'allany1("any", simd_ext, from_typ)',
        'reinterpret': 'reinterpret1(simd_ext, from_typ, to_typ)',
        'reinterpretl': 'reinterpretl1(simd_ext, from_typ, to_typ)',
        'cvt': 'convert1(simd_ext, from_typ, to_typ)',
        'rec11': 'recs1("rec11", simd_ext, from_typ)',
        'rsqrt11': 'recs1("rsqrt11", simd_ext, from_typ)',
        'rec': 'recs1("rec", simd_ext, from_typ)',
        'neg': 'neg1(simd_ext, from_typ)',
        'nbtrue': 'nbtrue1(simd_ext, from_typ)',
        'reverse': 'reverse1(simd_ext, from_typ)',
        'addv': 'addv(simd_ext, from_typ)'
    }
    if simd_ext not in get_simd_exts():
        raise ValueError('Unknown SIMD extension "{}"'.format(simd_ext))
    if not from_typ in common.types:
        raise ValueError('Unknown type "{}"'.format(from_typ))
    if not func in impls:
        return common.NOT_IMPLEMENTED
    else:
        return eval(impls[func])
