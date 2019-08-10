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

#include <cerrno>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <nsimd/modules/stl-algorithms/transform.hpp>
#include <vector>

namespace {

#define CHECK(a)                                                               \
  {                                                                            \
    errno = 0;                                                                 \
    if (!(a)) {                                                                \
      fprintf(stderr, "ERROR: " #a ":%d: %s\n", __LINE__, strerror(errno));    \
      fflush(stderr);                                                          \
      exit(EXIT_FAILURE);                                                      \
    }                                                                          \
  }

#define CHECK_COLLECTIONS(a0, a1)                                              \
  {                                                                            \
    errno = 0;                                                                 \
    if (a0.size() != a1.size()) {                                              \
      fprintf(stderr, "ERROR: not same lenght:%d: %s\n", __LINE__,             \
              strerror(errno));                                                \
      fflush(stderr);                                                          \
      exit(EXIT_FAILURE);                                                      \
    }                                                                          \
    for (size_t i = 0; i < a0.size(); ++i) {                                   \
      CHECK(a0[i] == a1[i])                                                    \
    }                                                                          \
  }
/* ------------------------------------------------------------------------- */

const int SIZE = 1024;

//---UNARY
template <typename T> struct UnaryOpAddValue {
  const T m_val;
  typedef typename nsimd::pack<T> simd_type_T;
  const simd_type_T m_val_simd;

public:
  UnaryOpAddValue(T val) : m_val(val), m_val_simd(val) {}
  inline T operator()(T const &a) const // pass by value ?
  {
    return m_val + a;
  }
  template <typename U> inline U operator()(U const &a) const {
    return nsimd::add(a, m_val_simd);
  }
};

template <typename T> void test_transform_unary_arithmetics_for() {
  const int len_vec = SIZE / sizeof(T);
  const std::vector<T, nsimd::allocator<T>> input(len_vec, static_cast<T>(41));
  std::vector<T, nsimd::allocator<T>> output(len_vec);
  const std::vector<T> expected(len_vec, static_cast<T>(42));

  // define operator
  UnaryOpAddValue<T> PlusOne(static_cast<T>(1));

  nsimd::transform(input.data(), input.data() + input.size(), output.data(),
                   PlusOne);
  CHECK_COLLECTIONS(output, expected)
}

void test_transform_unary_arithmetics() {
  // aligned load/store
  test_transform_unary_arithmetics_for<i8>();
  test_transform_unary_arithmetics_for<u8>();
  test_transform_unary_arithmetics_for<i16>();
  test_transform_unary_arithmetics_for<u16>();
  test_transform_unary_arithmetics_for<i32>();
  test_transform_unary_arithmetics_for<u32>();
  test_transform_unary_arithmetics_for<i64>();
  test_transform_unary_arithmetics_for<u64>();
  test_transform_unary_arithmetics_for<f32>();
  test_transform_unary_arithmetics_for<f64>();
}

void test_transform_unary_unroll() {}

void test_transform_unary_fallback_std() {}

//---BINARY
template <typename T> struct BinaryOpAdd {

public:
  BinaryOpAdd() {}

  inline T operator()(T const &a0, T const &a1) const {

    return a0 + a1;
  } // namespace

  template <typename U> inline U operator()(U const &a0, U const &a1) const {

    return nsimd::add(a0, a1);
  }
};

template <typename T> void test_transform_binary_arithmetics_for() {
  const int len_vec = SIZE / sizeof(T);
  const std::vector<T, nsimd::allocator<T>> input1(len_vec, static_cast<T>(41));
  const std::vector<T, nsimd::allocator<T>> input2(len_vec, static_cast<T>(1));
  std::vector<T, nsimd::allocator<T>> output(len_vec);
  const std::vector<T> expected(len_vec, static_cast<T>(42));

  // define operator
  BinaryOpAdd<T> Add;

  nsimd::transform(input1.data(), input1.data() + input1.size(), input2.data(),
                   output.data(), Add);
  CHECK_COLLECTIONS(output, expected)
} // namespace

void test_transform_binary_arithmetics() {
  // aligned load/store
  test_transform_binary_arithmetics_for<i8>();
  test_transform_binary_arithmetics_for<u8>();
  test_transform_binary_arithmetics_for<i16>();
  test_transform_binary_arithmetics_for<u16>();
  test_transform_binary_arithmetics_for<i32>();
  test_transform_binary_arithmetics_for<u32>();
  test_transform_binary_arithmetics_for<i64>();
  test_transform_binary_arithmetics_for<u64>();
  test_transform_binary_arithmetics_for<f32>();
  test_transform_binary_arithmetics_for<f64>();
}
void test_transform_binary_unroll() {}

void test_transform_binary_fallback_std() {}
} // namespace
// ----------------------------------------------------------------------------

int main(void) {
  test_transform_unary_arithmetics();
  test_transform_unary_unroll();
  test_transform_unary_fallback_std();

  test_transform_binary_arithmetics();
  test_transform_binary_unroll();
  test_transform_binary_fallback_std();
  return 0;
}