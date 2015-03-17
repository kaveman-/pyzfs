CDEF = """
	typedef ... nvlist_t;
	typedef ... nvpair_t;
	enum data_type_t { ... };
	typedef bool boolean_t;

	int nvlist_alloc(nvlist_t **, uint_t, int);
	void nvlist_free(nvlist_t *);

	int nvlist_add_nvpair(nvlist_t *, nvpair_t *);
	int nvlist_add_boolean(nvlist_t *, const char *);
	int nvlist_add_boolean_value(nvlist_t *, const char *, boolean_t);
	int nvlist_add_byte(nvlist_t *, const char *, uchar_t);
	int nvlist_add_int8(nvlist_t *, const char *, int8_t);
	int nvlist_add_uint8(nvlist_t *, const char *, uint8_t);
	int nvlist_add_int16(nvlist_t *, const char *, int16_t);
	int nvlist_add_uint16(nvlist_t *, const char *, uint16_t);
	int nvlist_add_int32(nvlist_t *, const char *, int32_t);
	int nvlist_add_uint32(nvlist_t *, const char *, uint32_t);
	int nvlist_add_int64(nvlist_t *, const char *, int64_t);
	int nvlist_add_uint64(nvlist_t *, const char *, uint64_t);
	int nvlist_add_string(nvlist_t *, const char *, const char *);
	int nvlist_add_nvlist(nvlist_t *, const char *, nvlist_t *);
	int nvlist_add_boolean_array(nvlist_t *, const char *, boolean_t *, uint_t);
	int nvlist_add_byte_array(nvlist_t *, const char *, uchar_t *, uint_t);
	int nvlist_add_int8_array(nvlist_t *, const char *, int8_t *, uint_t);
	int nvlist_add_uint8_array(nvlist_t *, const char *, uint8_t *, uint_t);
	int nvlist_add_int16_array(nvlist_t *, const char *, int16_t *, uint_t);
	int nvlist_add_uint16_array(nvlist_t *, const char *, uint16_t *, uint_t);
	int nvlist_add_int32_array(nvlist_t *, const char *, int32_t *, uint_t);
	int nvlist_add_uint32_array(nvlist_t *, const char *, uint32_t *, uint_t);
	int nvlist_add_int64_array(nvlist_t *, const char *, int64_t *, uint_t);
	int nvlist_add_uint64_array(nvlist_t *, const char *, uint64_t *, uint_t);
	int nvlist_add_string_array(nvlist_t *, const char *, char *const *, uint_t);
	int nvlist_add_nvlist_array(nvlist_t *, const char *, nvlist_t **, uint_t);

	int nvlist_lookup_boolean(nvlist_t *, const char *);
	int nvlist_lookup_boolean_value(nvlist_t *, const char *, boolean_t *);
	int nvlist_lookup_byte(nvlist_t *, const char *, uchar_t *);
	int nvlist_lookup_int8(nvlist_t *, const char *, int8_t *);
	int nvlist_lookup_uint8(nvlist_t *, const char *, uint8_t *);
	int nvlist_lookup_int16(nvlist_t *, const char *, int16_t *);
	int nvlist_lookup_uint16(nvlist_t *, const char *, uint16_t *);
	int nvlist_lookup_int32(nvlist_t *, const char *, int32_t *);
	int nvlist_lookup_uint32(nvlist_t *, const char *, uint32_t *);
	int nvlist_lookup_int64(nvlist_t *, const char *, int64_t *);
	int nvlist_lookup_uint64(nvlist_t *, const char *, uint64_t *);
	int nvlist_lookup_string(nvlist_t *, const char *, char **);
	int nvlist_lookup_nvlist(nvlist_t *, const char *, nvlist_t **);
	int nvlist_lookup_boolean_array(nvlist_t *, const char *,
	    boolean_t **, uint_t *);
	int nvlist_lookup_byte_array(nvlist_t *, const char *, uchar_t **, uint_t *);
	int nvlist_lookup_int8_array(nvlist_t *, const char *, int8_t **, uint_t *);
	int nvlist_lookup_uint8_array(nvlist_t *, const char *, uint8_t **, uint_t *);
	int nvlist_lookup_int16_array(nvlist_t *, const char *, int16_t **, uint_t *);
	int nvlist_lookup_uint16_array(nvlist_t *, const char *, uint16_t **, uint_t *);
	int nvlist_lookup_int32_array(nvlist_t *, const char *, int32_t **, uint_t *);
	int nvlist_lookup_uint32_array(nvlist_t *, const char *, uint32_t **, uint_t *);
	int nvlist_lookup_int64_array(nvlist_t *, const char *, int64_t **, uint_t *);
	int nvlist_lookup_uint64_array(nvlist_t *, const char *, uint64_t **, uint_t *);
	int nvlist_lookup_string_array(nvlist_t *, const char *, char ***, uint_t *);
	int nvlist_lookup_nvlist_array(nvlist_t *, const char *,
	    nvlist_t ***, uint_t *);

	int nvlist_lookup_nvpair(nvlist_t *, const char *, nvpair_t **);
	int nvlist_lookup_nvpair_embedded_index(nvlist_t *, const char *, nvpair_t **,
	    int *, char **);
	boolean_t nvlist_exists(nvlist_t *, const char *);
	boolean_t nvlist_empty(nvlist_t *);

	/* processing nvpair */
	nvpair_t *nvlist_next_nvpair(nvlist_t *, nvpair_t *);
	nvpair_t *nvlist_prev_nvpair(nvlist_t *, nvpair_t *);
	char *nvpair_name(nvpair_t *);
	data_type_t nvpair_type(nvpair_t *);
	int nvpair_type_is_array(nvpair_t *);
	int nvpair_value_boolean_value(nvpair_t *, boolean_t *);
	int nvpair_value_byte(nvpair_t *, uchar_t *);
	int nvpair_value_int8(nvpair_t *, int8_t *);
	int nvpair_value_uint8(nvpair_t *, uint8_t *);
	int nvpair_value_int16(nvpair_t *, int16_t *);
	int nvpair_value_uint16(nvpair_t *, uint16_t *);
	int nvpair_value_int32(nvpair_t *, int32_t *);
	int nvpair_value_uint32(nvpair_t *, uint32_t *);
	int nvpair_value_int64(nvpair_t *, int64_t *);
	int nvpair_value_uint64(nvpair_t *, uint64_t *);
	int nvpair_value_string(nvpair_t *, char **);
	int nvpair_value_nvlist(nvpair_t *, nvlist_t **);
	int nvpair_value_boolean_array(nvpair_t *, boolean_t **, uint_t *);
	int nvpair_value_byte_array(nvpair_t *, uchar_t **, uint_t *);
	int nvpair_value_int8_array(nvpair_t *, int8_t **, uint_t *);
	int nvpair_value_uint8_array(nvpair_t *, uint8_t **, uint_t *);
	int nvpair_value_int16_array(nvpair_t *, int16_t **, uint_t *);
	int nvpair_value_uint16_array(nvpair_t *, uint16_t **, uint_t *);
	int nvpair_value_int32_array(nvpair_t *, int32_t **, uint_t *);
	int nvpair_value_uint32_array(nvpair_t *, uint32_t **, uint_t *);
	int nvpair_value_int64_array(nvpair_t *, int64_t **, uint_t *);
	int nvpair_value_uint64_array(nvpair_t *, uint64_t **, uint_t *);
	int nvpair_value_string_array(nvpair_t *, char ***, uint_t *);
	int nvpair_value_nvlist_array(nvpair_t *, nvlist_t ***, uint_t *);
"""

SOURCE = """
#include <libzfs/sys/nvpair.h>
"""

LIBRARIES = [ "nvpair", ]

