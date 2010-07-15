#ifndef FEM_UTILS_STRING_HPP
#define FEM_UTILS_STRING_HPP

#include <fem/size_t.hpp>
#include <fem/utils/char.hpp>
#include <boost_adaptbx/error_utils.h>
#include <algorithm>
#include <cstring>

namespace fem { namespace utils {

  inline
  bool
  starts_with(
    char const* str,
    unsigned start,
    unsigned stop,
    char const* substr)
  {
    for(unsigned j=start;j<stop;) {
      if (*substr == '\0') break;
      if (str[j++] != *substr++) return false;
    }
    return (start != stop);
  }

  inline
  bool
  ends_with_char(
    std::string const& str,
    int c)
  {
    unsigned i = str.size();
    if (i == 0) return false;
    return (str[i-1] == c);
  }

  // compare with fable/__init__.py
  inline
  int
  unsigned_integer_scan(
    char const* code,
    unsigned start,
    unsigned stop)
  {
    unsigned i = start;
    for(;i<stop;i++) {
      int c = code[i];
      if (!is_digit(c)) break;
    }
    if (i == start) return -1;
    return i;
  }

  //! Assumes ASCII or similar.
  inline
  unsigned
  unsigned_integer_value(
    char const* str,
    unsigned start,
    unsigned stop)
  {
    unsigned result = 0;
    unsigned i = start;
    for(;i<stop;i++) {
      result *= 10;
      result += (str[i] - '0');
    }
    return result;
  }

  inline
  unsigned
  unsigned_integer_value(
    char const* str,
    unsigned stop)
  {
    return unsigned_integer_value(str, 0, stop);
  }

  inline
  int
  signed_integer_value(
    char const* str,
    unsigned start,
    unsigned stop)
  {
    bool negative;
    if (str[start] == '-') {
      negative = true;
      start++;
    }
    else {
      negative = false;
      if (str[start] == '+') start++;
    }
    int result = unsigned_integer_value(str, start, stop);
    if (negative) result *= -1;
    return result;
  }

  inline
  void
  copy_with_blank_padding(
    char const* src,
    size_t src_size,
    char* dest,
    size_t dest_size)
  {
    if (dest_size < src_size) {
      std::memmove(dest, src, dest_size);
    }
    else {
      std::memmove(dest, src, src_size);
      for (size_t i=src_size;i<dest_size;i++) {
        dest[i] = ' ';
      }
    }
  }

  inline
  void
  copy_with_blank_padding(
    char const* src,
    char* dest,
    size_t dest_size)
  {
    size_t i;
    for (i=0; i < dest_size && src[i] != '\0'; i++) {
      dest[i] = src[i];
    }
    for (; i < dest_size; i++) {
      dest[i] = ' ';
    }
  }

  inline
  bool
  string_eq(
    char const* lhs,
    size_t lhs_size,
    char const* rhs,
    size_t rhs_size)
  {
    static const char blank = ' ';
    if (lhs_size < rhs_size) {
      return string_eq(rhs, rhs_size, lhs, lhs_size);
    }
    if (std::memcmp(lhs, rhs, rhs_size) != 0) return false;
    for(size_t i=rhs_size;i<lhs_size;i++) {
      if (lhs[i] != blank) return false;
    }
    return true;
  }

  inline
  bool
  string_eq(
    char const* lhs,
    size_t lhs_size,
    char const* rhs)
  {
    static const char blank = ' ';
    size_t i = 0;
    for(;i<lhs_size;i++) {
      if (rhs[i] == '\0') {
        for(;i<lhs_size;i++) {
          if (lhs[i] != blank) return false;
        }
        return true;
      }
      if (rhs[i] != lhs[i]) return false;
    }
    for(; rhs[i] != '\0'; i++) {
      if (rhs[i] != blank) return false;
    }
    return true;
  }

  inline
  size_t_2
  find_leading_and_trailing_blank_padding(
    char const* str,
    size_t stop)
  {
    size_t i = 0;
    while (i != stop) {
      if (str[i] != ' ') break;
      i++;
    }
    size_t j = stop;
    while (j != 0) {
      j--;
      if (str[j] != ' ') {
        j++;
        break;
      }
    }
    return size_t_2(i, j);
  }

  inline
  std::string
  strip_leading_and_trailing_blank_padding(
    std::string const& str)
  {
    size_t_2 indices = find_leading_and_trailing_blank_padding(
      str.data(), str.size());
    if (indices.elems[0] == 0 && indices.elems[1] == str.size()) {
      return str;
    }
    return std::string(
      str.data() + indices.elems[0],
      indices.elems[1] - indices.elems[0]);
  }

  inline
  std::string
  to_lower(
    std::string const& str)
  {
    std::string result = str;
    size_t n = str.size();
    for(size_t i=0;i<n;i++) {
      result[i] = to_lower(result[i]);
    }
    return result;
  }

  inline
  int
  keyword_index(
    char const* valid_vals[],
    std::string const& val,
    char const* throw_info=0)
  {
    std::string
      val_norm = to_lower(strip_leading_and_trailing_blank_padding(val));
    for (int i=0; valid_vals[i] != 0; i++) {
      if (std::strcmp(valid_vals[i], val_norm.c_str()) == 0) {
        return i;
      }
    }
    if (throw_info != 0) {
      std::ostringstream o;
      o << throw_info << ": invalid keyword: \"" << val << "\"";
      throw std::runtime_error(o.str());
    }
    return -1;
  }

  //! Assumes ASCII or similar.
  inline
  std::string
  format_char_for_display(
    int c)
  {
    std::ostringstream o;
    bool printable = (c >= ' ' && c <= '~');
    if (printable) {
      if (c == '"') {
        o << "'\"' (double quote, ";
      }
      else if (c == '\'') {
        o << "\"'\" (single quote, ";
      }
      else {
        o << "\"" << static_cast<char>(c) << "\" (";
      }
    }
    o << "ordinal=" << (c < 0 ? c + 256 : c);
    if (printable) o << ")";
    return o.str();
  }

}} // namespace fem::utils

#endif // GUARD
