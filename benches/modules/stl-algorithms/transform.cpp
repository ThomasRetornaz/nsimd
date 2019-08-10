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
#include <nsimd/nsimd.h>

// Required for random generation
#include "../benches.hpp"

// Google benchmark
#include <benchmark/benchmark.h>

// std
#include <cmath>

static const int sz = 1024;

template <typename T>
std::vector<T, nsimd::allocator<T>> ConstructAlignedRandomVector() {
  std::vector<T, nsimd::allocator<T>> vect(sz);
  for (size_t i = 0; i < sz; i++) {
    vect[i] = nsimd::benches::rand<T>(std::numeric_limits<T>::min(),
                                      std::numeric_limits<T>::max());
  }
  return vect;
}

template <typename T>
class TransformUnaryFixture : public ::benchmark::Fixture {
public:
  void SetUp(const ::benchmark::State &st) {
    input = ConstructAlignedRandomVector();
    ouput.resize(sz);
  }
  void TearDown(const ::benchmark::State &) { m_vect.clear(); }
  std::vector<T, nsimd::allocator<T>> input;
  std::vector<T, nsimd::allocator<T>> ouput;
};

BENCHMARK_MAIN();