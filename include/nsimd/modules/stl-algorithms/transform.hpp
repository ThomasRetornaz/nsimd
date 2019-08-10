/*

Copyright (c) 2019 Agenium Scale

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

*/

#ifndef NSIMD_CXX_STL_ALGORITHMS_TRANSFORM
#define NSIMD_CXX_STL_ALGORITHMS_TRANSFORM

#include <nsimd/modules/stl-algorithms/stl-algorithms-helpers.hpp>

namespace nsimd {

template <typename T, typename U, typename UnOp>
U *transform(T const *first, T const *last, U *out, UnOp f) {

  // todo check null ptr input ?

  typedef typename nsimd::pack<T> simd_type_T;
  typedef typename nsimd::pack<U> simd_type_U;

  static_assert(nsimd::max_len_t<T>::value == nsimd::max_len_t<U>::value,
                "mismatch length between T and U");

  const int alignment = NSIMD_MAX_ALIGNMENT;

  // Define loop counter
  const int simd_size = nsimd::len(simd_type_T());
  const ptrdiff_t size = std::distance(first, last);

  // note enforce that input is aligned when we start the main simd loop
  const std::pair<ptrdiff_t, ptrdiff_t> range =
      detail::nsimd_range(first, last);
  const ptrdiff_t size_prologue_loop = range.first;
  const ptrdiff_t size_simd_loop = range.second;

  ptrdiff_t i = 0;
  //---prologue
  for (; i < size_prologue_loop; ++i) {
    *out++ = f(*first++);
  }

  //---main simd loop
  if (detail::is_aligned(out, alignment)) {
    for (; i < size_simd_loop; i += simd_size) {
      simd_type_T element = nsimd::loada<simd_type_T>(first);
      nsimd::storea(out, f(element));
      first += simd_size;
      out += simd_size;
    }
  } else {
    for (; i < size_simd_loop; i += simd_size) {
      simd_type_T element = nsimd::loada<simd_type_T>(first);
      nsimd::storeu(out, f(element));
      first += simd_size;
      out += simd_size;
    }
  }

  //---epilogue
  for (; i < size; ++i) {
    *out++ = f(*first++);
  }
  return out;
}

template <typename T1, typename T2, typename U, typename BinOp>
U *transform(T1 const *first1, T1 const *last1, T2 const *first2, U *out,
             BinOp f)

{
  // todo check null ptr input ?

  typedef typename nsimd::pack<T1> simd_type_T1;
  typedef typename nsimd::pack<T2> simd_type_T2;
  typedef typename nsimd::pack<U> simd_type_U;

  static_assert(nsimd::max_len_t<T1>::value == nsimd::max_len_t<T2>::value,
                "mismatch length between T1 and T2");
  static_assert(nsimd::max_len_t<T1>::value == nsimd::max_len_t<U>::value,
                "mismatch length between T1 and U");
  static_assert(nsimd::max_len_t<T2>::value == nsimd::max_len_t<U>::value,
                "mismatch length between T2 and U");

  int alignment = NSIMD_MAX_ALIGNMENT;
  // Define loop counter

  const int simd_size = nsimd::len(simd_type_T1());
  const ptrdiff_t size = std::distance(first1, last1);
  const std::pair<ptrdiff_t, ptrdiff_t> range =
      detail::nsimd_range(first1, last1);
  const ptrdiff_t size_prologue_loop = range.first;
  const ptrdiff_t size_simd_loop = range.second;

  ptrdiff_t i = 0;
  //---prologue
  for (; i < size_prologue_loop; ++i) {
    *out++ = f(*first1++, *first2++);
  }

  //---main simd loop
  if (detail::is_aligned(first2, alignment) &&
      detail::is_aligned(out, alignment)) {
    for (; i < size_simd_loop; i += simd_size) {
      simd_type_T1 element1 = nsimd::loada<simd_type_T1>(first1);
      simd_type_T2 element2 = nsimd::loada<simd_type_T2>(first2);
      nsimd::storea(out, f(element1, element2));
      first1 += simd_size;
      first2 += simd_size;
      out += simd_size;
    }
  } else {
    for (; i < size_simd_loop; i += simd_size) {
      simd_type_T1 element1 = nsimd::loada<simd_type_T1>(first1);
      simd_type_T2 element2 = nsimd::loadu<simd_type_T2>(first2);
      nsimd::storeu(out, f(element1, element2));
      first1 += simd_size;
      first2 += simd_size;
      out += simd_size;
    }
  }

  //---epilogue
  for (; i < size; ++i) {
    *out++ = f(*first1++, *first2++);
  }
  return out;
}
} // namespace nsimd

#endif // NSIMD_CXX_STL_ALGORITHMS_TRANSFORM