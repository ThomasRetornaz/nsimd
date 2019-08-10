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

#ifndef NSIMD_CXX_STL_ALGORITHMS_HELPERS
#define NSIMD_CXX_STL_ALGORITHMS_HELPERS

#include <cassert>
#include <cstddef>
#include <nsimd/nsimd-all.hpp>
#include <utility>

namespace nsimd {
namespace detail {
// todo where to put documentation?
NSIMD_INLINE bool
is_aligned(const void *ptr,
           std::size_t alignment =
               NSIMD_MAX_ALIGNMENT) // NSIMD_MAX_ALIGNMENT<- should be
                                    // relaxed for SSE,AVX,NEON cases ?
{
  assert(
      ((alignment & (alignment - 1)) == 0)); // may we need to define somewhere
                                             // an exception or nsimd_assert
  return ((std::size_t)ptr & (alignment - 1)) ==
         0; // from boost\align\detail\is_aligned.hpp
}

template <typename T>
NSIMD_INLINE T *
reach_next_aligned_ptr(T *ptr, std::size_t alignment = NSIMD_MAX_ALIGNMENT) {
  assert(((alignment & (alignment - 1)) == 0));
  return reinterpret_cast<T *>(
      ((std::size_t)ptr + alignment - 1) &
      ~(alignment - 1)); // from boost\align\detail\align_up.hpp
}

// todo where to put documentation?
template <typename T>
const std::pair<ptrdiff_t, ptrdiff_t> NSIMD_INLINE nsimd_range(const T *first,
                                                               const T *last) {
  const ptrdiff_t simd_size = nsimd::len(nsimd::pack<T>());
  const ptrdiff_t size = last - first;
  // get aligned adress from first
  const T *ptr_aligned_first =
      reach_next_aligned_ptr(first, NSIMD_MAX_ALIGNMENT);
  // Next aligned address may be out of range, so make sure size_prologue_loop
  // is not bigger than size
  const ptrdiff_t size_prologue_loop =
      std::min(size, std::distance(first, ptr_aligned_first));
  const ptrdiff_t size_simd_loop =
      (size >= size_prologue_loop)
          ? (simd_size * ((size - size_prologue_loop) / simd_size))
          : (0u);

  return std::make_pair(size_prologue_loop, size_simd_loop);
}
} // namespace detail
} // namespace nsimd
#endif // NSIMD_CXX_STL_ALGORITHMS_HELPERS