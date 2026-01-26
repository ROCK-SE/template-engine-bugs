# Detailed information for built-in filters (including description and caveat)

JINJA2_BUILTIN_FILTERS_INFO = {
    "abs": {
        "signature": "abs(x)",
        "description": "Return the absolute value of a number.",
        "caveat": "Only works with numeric types."
    },
    "first": {
        "signature": "first(seq)",
        "description": "Return the first item of a sequence.",
        "caveat": "Returns undefined for empty sequences."
    },
    "last": {
        "signature": "last(seq)",
        "description": "Return the last item of a sequence.",
        "caveat": "May be inefficient for large iterators."
    },
    "min": {
        "signature": "min(value, case_sensitive=False, attribute=None)",
        "description": "Return the smallest item from a sequence.",
        "caveat": "All elements must be comparable; mixed types may raise errors."
    },
    "max": {
        "signature": "max(value, case_sensitive=False, attribute=None)",
        "description": "Return the largest item from a sequence.",
        "caveat": "All elements must be comparable; mixed types may raise errors."
    },
    "length": {
        "signature": "length(obj)",
        "description": "Return the number of items in an object.",
        "caveat": "Returns 0 for objects without a defined length."
    },
    "default": {
        "signature": "default(value, default_value='', boolean=False)",
        "description": "Return a default value if the original value is undefined.",
        "caveat": "If boolean=True, only False triggers the default (not 0 or empty strings)."
    },
    "lower": {
        "signature": "lower(s)",
        "description": "Convert a string to lowercase.",
        "caveat": "Only applicable to strings."
    },
    "upper": {
        "signature": "upper(s)",
        "description": "Convert a string to uppercase.",
        "caveat": "Only applicable to strings."
    },
    "sort": {
        "signature": "sort(value, reverse=False, case_sensitive=False, attribute=None)",
        "description": "Sort a sequence.",
        "caveat": "Elements must be comparable; attribute must exist on objects."
    },
    "reverse": {
        "signature": "reverse(value)",
        "description": "Reverse the order of a sequence.",
        "caveat": "Iterators are consumed and converted to lists."
    },
    "join": {
        "signature": "join(value, d='', attribute=None)",
        "description": "Join items into a string using a delimiter.",
        "caveat": "All items must be string-convertible."
    },
    "sum": {
        "signature": "sum(iterable, attribute=None, start=0)",
        "description": "Sum numeric values in an iterable.",
        "caveat": "All values must be numeric; floating-point precision applies."
    },
    "list": {
        "signature": "list(value)",
        "description": "Convert a value into a list.",
        "caveat": "Strings are split into individual characters."
    },
    "string": {
        "signature": "string(value)",
        "description": "Convert a value to a string.",
        "caveat": "None is converted to an empty string."
    },
    "int": {
        "signature": "int(value, default=0, base=10)",
        "description": "Convert a value to an integer.",
        "caveat": "Floats are truncated, not rounded."
    },
    "float": {
        "signature": "float(value, default=0.0)",
        "description": "Convert a value to a floating-point number.",
        "caveat": "Invalid values return the default."
    },
    "escape": {
        "signature": "escape(s)",
        "description": "Escape HTML special characters.",
        "caveat": "Input is first converted to a string."
    },
    "safe": {
        "signature": "safe(value)",
        "description": "Mark a string as safe HTML, disabling auto-escaping.",
        "caveat": "Use only with trusted content; improper use can cause XSS vulnerabilities."
    },
    "replace": {
        "signature": "replace(s, old, new, count=None)",
        "description": "Replace occurrences of a substring.",
        "caveat": "Case-sensitive; regex is not supported."
    },
    "tojson": {
        "signature": "tojson(value, indent=None)",
        "description": "Serialize an object to a JSON-formatted string.",
        "caveat": "Not all Python objects are JSON-serializable."
    },
    "wordcount": {
        "signature": "wordcount(s)",
        "description": "Count the number of words in a string.",
        "caveat": "Uses simple whitespace splitting."
    },
    "capitalize": {
        "signature": "capitalize(s)",
        "description": "Capitalize the first character of a string.",
        "caveat": "Primarily ASCII-oriented."
    },
    "title": {
        "signature": "title(s)",
        "description": "Convert a string to title case.",
        "caveat": "May mishandle acronyms or special cases."
    },
    "truncate": {
        "signature": "truncate(s, length=255, killwords=False, end='...')",
        "description": "Truncate a string to a given length.",
        "caveat": "HTML tags are not taken into account."
    },
    "attr": {
        "signature": "attr(obj, name)",
        "description": "Access an attribute of an object.",
        "caveat": "Missing attributes return undefined."
    },
    "items": {
        "signature": "items(value)",
        "description": "Return key-value pairs of a dictionary.",
        "caveat": "Only works with dictionaries."
    },
    "unique": {
        "signature": "unique(value, case_sensitive=False, attribute=None)",
        "description": "Return unique items from a sequence while preserving order.",
        "caveat": "Returns an iterator; convert to list if reuse is needed."
    },
    "batch": {
        "signature": "batch(value, linecount, fill_with=None)",
        "description": "Group items into batches of a fixed size.",
        "caveat": "The final batch may be padded with fill_with."
    },
    "slice": {
        "signature": "slice(value, slices, fill_with=None)",
        "description": "Split a sequence into a fixed number of slices.",
        "caveat": "Slices may be uneven and padded."
    },
    "map": {
        "signature": "map(value, attribute)",
        "description": "Apply a filter or extract an attribute from each item.",
        "caveat": "Missing attributes yield undefined."
    },
    "select": {
        "signature": "select(value, test)",
        "description": "Filter items that pass a test.",
        "caveat": "Items failing the test are silently skipped."
    },
    "reject": {
        "signature": "reject(value, test)",
        "description": "Filter items that fail a test.",
        "caveat": "Opposite behavior of select."
    },
    "selectattr": {
        "signature": "selectattr(value, attr, test)",
        "description": "Filter objects by attribute value.",
        "caveat": "Objects without the attribute are skipped."
    },
    "rejectattr": {
        "signature": "rejectattr(value, attr, test)",
        "description": "Exclude objects based on attribute value.",
        "caveat": "Objects without the attribute are kept."
    },
    "groupby": {
        "signature": "groupby(value, attribute, default=None, case_sensitive=False)",
        "description": "Group items by a common attribute.",
        "caveat": "Returns a group iterator, not a list."
    },
    "dictsort": {
        "signature": "dictsort(value, case_sensitive=False, by='key', reverse=False)",
        "description": "Sort a dictionary by key or value.",
        "caveat": "Returns a list of (key, value) tuples."
    },
    "indent": {
        "signature": "indent(s, width=4, first=False, blank=False)",
        "description": "Indent each line in a multi-line string.",
        "caveat": "Width may be an integer or a string."
    },
    "striptags": {
        "signature": "striptags(value)",
        "description": "Remove HTML/XML tags from a string.",
        "caveat": "Does not decode HTML entities."
    },
    "center": {
        "signature": "center(value, width=80)",
        "description": "Center a string within a given width.",
        "caveat": "No effect if width is smaller than the string."
    },
    "format": {
        "signature": "format(value, *args, **kwargs)",
        "description": "Apply Python string formatting.",
        "caveat": "Complex formats may reduce readability."
    },
    "trim": {
        "signature": "trim(value, chars=None)",
        "description": "Strip characters from both ends of a string.",
        "caveat": "Equivalent to Python's strip()."
    },
    "filesizeformat": {
        "signature": "filesizeformat(value, binary=False)",
        "description": "Format bytes as a human-readable file size.",
        "caveat": "Binary units differ from decimal units."
    },
    "wordwrap": {
        "signature": "wordwrap(s, width=79, break_long_words=True, wrapstring=None)",
        "description": "Wrap long text lines to a given width.",
        "caveat": "Long words may be forcibly split."
    },
    "xmlattr": {
        "signature": "xmlattr(d, autospace=True)",
        "description": "Convert a dictionary to XML attributes.",
        "caveat": "Values are always escaped."
    },
    "pprint": {
        "signature": "pprint(value)",
        "description": "Pretty-print a data structure.",
        "caveat": "Not suitable for large data structures."
    },
    "random": {
        "signature": "random(seq)",
        "description": "Return a random item from a sequence.",
        "caveat": "Undefined behavior for empty sequences."
    },
    "urlize": {
        "signature": "urlize(value, trim_url_limit=None, nofollow=False, target=None, rel=None, extra_schemes=None)",
        "description": "Convert URLs in text into clickable links.",
        "caveat": "Simple URL detection; output is marked safe."
    },
    "urlencode": {
        "signature": "urlencode(value)",
        "description": "URL-encode a string or dictionary.",
        "caveat": "Dictionaries are converted into query strings."
    }
}

FILTER_ALIASES = {
    "d": "default",
    "e": "escape",
    "count": "length",
}

BUILTIN_FILTER_NAMES = (
    set(JINJA2_BUILTIN_FILTERS_INFO.keys()) |
    set(FILTER_ALIASES.keys())
)
