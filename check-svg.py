# 1305,  9 Jan 2018 (NZDT)
#
# Nevil Brownlee, U Auckland
#   From a simple original version by Joe Hildebrand

# ElementTree doesn't have nsmap
try:
    import xml.etree.cElementTree as ET
except ImportError:
    import xml.etree.ElementTree as ET
#from lxml import etree as ET

import getopt, sys, re

import word_properties as wp

indent = 4
warn_nbr = 0
current_file = None

verbose = False   # set by -v
warn_limit = 40   # set by -w nnn
new_file = False  # set by -n
trace = False     # set by -t

bad_namespaces = []

def help_msg(msg):
    suffix = ''
    if msg:
        suffix = ": %s" % msg
    print("Nevil's SVG checker%s" % suffix)
    print("\n  ./check.py [options] input-svg-file(s)\n")
    print("options:")
    print("  -n     write .new.svg file, stripping out anything\n           not allowed in SVG 1.2 RFC")
    print("  -w nn  stop after nn warning messages\n")
    exit()

try:
    options, rem_args = getopt.getopt(sys.argv[1:], "hntvw:")
except getopt.GetoptError:
    help_msg("Unknown option")
    
filter = None
for o,v in options:
    if o == "-w":
        warn_limit = int(v)
    elif o == "-v":
        verbose = True
    elif o == "-h":
        help_msg(None)
    elif o == "-n":
        new_file = True
    elif o == "-t":
        trace = True

if len(rem_args) == 0:
    help_msg("No input file(s) specified!")

def warn(msg, depth):
    global indent, warn_nbr, warn_limit, current_file
    warn_nbr += 1
    print("%5d %s%s" % (warn_nbr, ' '*(depth*indent), msg))
    if warn_nbr == warn_limit:
        print("warning limit (%d) reached for %s <<" % (
            warn_nbr, current_file))
        exit()

#def check_some_props(attr, val, depth):  # For [style] properties
# Not needed Jan 2018 versionq
#    props_to_check = wp.property_lists[attr]
#    new_val = '';  ok = True
#    style_props = val.rstrip(';').split(';')
#    print("style_props = %s" % style_props)
#    for prop in style_props:
#        print("prop = %s" %  prop)
#        p, v = prop.split(':')
#        v = v.strip()  # May have leading blank
#        if p in props_to_check:
#            #allowed_vals = wp.properties[p]
#            #print("$csp p=%s, allowed_vals=%s." % (p, allowed_vals))
#            allowed = value_ok(v, p, depth)
#            if not allowed:
#                warn("['%s' attribute: value %s not valid for '%s']" % (
#                    attr,v, p), depth)
#                ok = False
#        else:
#            new_val += ';' + prop
#    return (ok, new_val)

def value_ok(v, obj, depth):  # Is value v OK for attrib/property obj?
    # Returns  (T/F/int, val that matched)
    #print("V++ value_ok(%s, %s, %s) type(v) = %s, type(obj)=%s" % (
    #    v, obj, depth, type(v), type(obj)))
    if obj in wp.properties:
        values = wp.properties[obj]
    elif obj in wp.basic_types:
        values = wp.basic_types[obj]
    elif isinstance(obj, str):
        return (v == obj, v)
    else:  # Unknown attribute
        return (False, None)

    #print("2++ values = %s <%s>" % ((values,), type(values)))
    if len(values) == 0:  # Empty values tuple, can't check
        return (True, None)
    elif isinstance(values, str):  # values is a string
        if values[0] == '<':
            #print("4++ values=%s, v=%s" % (values, v))
            ok_v, matched_v = value_ok(v, values, depth)
            #print("5++ ok_v = %s, matched_v = %s" % (ok_v, matched_v))
            return (ok_v, matched_v)
        if  values[0] == '+g':  # Any integer or real
            n = re.match(r'\d+\.\d+$', v)
            rv = None
            if n:
                rv = n.group()
            return (True, rv)
        if  values[0] == '+h':  # [100,900] in hundreds
            n = re.match(r'\d00$', v)
            rv = None
            if n:
                rv = n.group()
            return (True, rv)
        if values == v:
            print("4++ values=%s, v=%s." % (values, v))
            return (True, values)
        if values[0] == "[":
            some_ok, matched_val = check_some_props(values, v, depth)
            return (some_ok, matched_val)
        #if values == '#':  # RGB value
        #    lv = v.lower()
        #    if lv[0] == '#':  #rrggbb  hex
        #        if len(lv) == 7:
        #            return (lv[3:5] == lv[1:3] and lv[5:7] == lv[1:3], None)
        #        if len(lv) == 4:
        #            return (lv[2] == lv[1] and lv[3] == lv[1], None)
        #        return (False, None)
        #    elif lv.find('rgb') == 0:  # integers
        #        rgb = re.search(r'\((\d+),(\d+),(\d+)\)', lv)
        #        if rgb:
        #            return ((rgb.group(2) == rgb.group(1) and
        #                rgb.group(3) == rgb.group(1)), None)
        #        return (False, None)

    #print("6++ values tuple = %s" % (values,))
    for val in values:  # values is a tuple
        ok_v, matched_v = value_ok(v, val, depth)
        #print("7++ ok_v = %s, matched_v = %s" % (ok_v, matched_v))
        if ok_v:
            return (True, matched_v)

    #print("8++ values=%s, (%s) <<<" % ((values,), type(values)))
    return (True, None)  # Can't check it, so it's OK
        
def strip_prefix(element):  # Remove {namespace} prefix
    global bad_namespaces
    ns_ok = True
    if element[0] == '{':
        rbp = element.rfind('}')  # Index of rightmost }
        if rbp >= 0:
            ns = element[1:rbp]
            if not ns in wp.xmlns_urls:
                if not ns in bad_namespaces:
                    bad_namespaces.append(ns)
                ns_ok = False
            #print("@@ element=%s" % element[rbp+1:])
            element = element[rbp+1:]
    return element, ns_ok  # return False if not in a known namespace

def check(el, depth):
    global new_file, trace
    if trace:
        print("T1: %s tag = %s  (depth=%d <%s>)" % (
            ' '*(depth*indent), el.tag, depth, type(depth)))
    if warn_nbr >= warn_limit:
        return False
    element, ns_ok = strip_prefix(el.tag)  # name of element
    # ElementTree prefixes elements with default namespace in braces
    #print("element=%s, ns_ok=%s" % (element, ns_ok))
    if not ns_ok:
        return False  # Remove this el
    if verbose:
        print("%selement % s: %s" % (' '*(depth*indent), element, el.attrib))

    attrs_to_remove = []  # Can't remove them inside the iteration!
    attrs_to_set = []
    for attrib, val in el.attrib.items():
        # (attrib,val) tuples for each attribute
        attr, ns_ok = strip_prefix(attrib)
        if trace:
            print("%s attrib %s = %s (ns_ok = %s), val = %s" % (
                ' ' * (depth*(indent+1)), attr, val, ns_ok, val))
        if attrib in wp.elements:  # Is it an element?
            warn("element '%s' not allowed as attribute" % element, depth )
            attrs_to_remove.append(attrib)
        else:
            atr_ok, matched_val = value_ok(val, attr, depth)
            #print("$1-- val=%s, attr=%s -> atr_ok=%s, matched_val=%s" % (
            #    val, attr, atr_ok, matched_val))
            if not atr_ok:
                warn("value '%s' not allowed for attribute %s" % (val, attrib),
                     depth)
                attrs_to_remove.append(attrib)
            if matched_val != val and attrib == 'font-family':
                # Special case!
                if val.find('sans') >= 0:
                    attrs_to_set.append( (attrib, 'sans-serif') )
                if val.find('serif') >= 0:
                    attrs_to_set.append( (attrib, 'serif') )
        #print("%s is %s, matched_val %s" % (attr, atr_ok, matched_val))
    for atr in attrs_to_remove:
        el.attrib.pop(atr)
    for ats in attrs_to_set:
        el.set(ats[0], ats[1])

    children_to_remove = []
    for child in el:  # Children of this svg element
        ch_el, el_ok = strip_prefix(child.tag)  # name of element
        #print("$$ el=%s, child=%s, el_ok=%s, child.tag=%s, %s" % (
        #    el, ch_el, el_ok, child.tag, type(child)))
        # Check for not-allowed elements
        if ch_el in wp.element_children:
            allowed_children = wp.element_children[element]
        else:  # not in wp.element_children
            allowed_children = []
        if not ch_el in allowed_children:
            msg = "'%s' may not appear in a '%s'" % (ch_el, element)
            warn(msg, depth)
            children_to_remove.append(child)
        else:
            ch_ok = check(child, depth+1)  # OK, check this child
            #print("@2@ check(depth %d) returned %s" % (depth, ch_ok))

    #print("@3@ children_to_remove = %s" % children_to_remove)
    for child in children_to_remove:
        el.remove(child)
    return True  # OK

def remove_namespace(doc, namespace):
    return True  # OKace):
    # From  http://stackoverflow.com/questions/18159221/
    #   remove-namespace-and-prefix-from-xml-in-python-using-lxml
    ns = u'{%s}' % namespace
    nsl = len(ns)
    for elem in doc.getiterator():
        if elem.tag.startswith(ns):
            print("elem.tag before= %s," % elem.tag)
            elem.tag = elem.tag[nsl:]
            print("after=%s." % elem.tag)

def checkFile(fn, options):
    global current_file, warn_nbr, root
    current_file = fn
    print("Starting %s%s" % (fn, options))
    tree = ET.parse(fn)
    root = tree.getroot()
    #print("root.attrib=%s, test -> %d" % (root.attrib, "xmlns" in root.attrib))
    #    # attrib list doesn't have includes "xmlns", even though it's there
    #print("root.tag=%s" % root.tag)
    no_ns = root.tag.find("{") < 0
    #print("no_ns = %s" % no_ns)

    ET.register_namespace("", "http://www.w3.org/2000/svg")
        # Stops tree.write() from prefixing above with "ns0"
    check(root, 0)
    if trace and len(bad_namespaces) != 0:
        print("bad_namespaces = %s" % bad_namespaces)
    if new_file:
        sp = fn.rfind('.svg')
        if sp+3 != len(fn)-1:  # Indeces of last chars
            print("filename doesn't end in '.svg' (%d, %d)" % (sp, len(fn)))
        else:
            if no_ns:
                root.attrib["xmlns"] = "http://www.w3.org/2000/svg"
            for ns in bad_namespaces:
                remove_namespace(root, ns)
            new_fn = fn.replace(".svg", ".new.svg")
            print("writing to %s" % (new_fn))
            tree.write(new_fn)

    return warn_nbr

if __name__ == "__main__":
    options = ''
    if len(sys.argv) > 2:
        options = "  %s" % ' '.join(sys.argv[1:-1])
    for arg in rem_args:
        warn_nbr = 0
        n_warnings = checkFile(arg, options)
        print("%d warnings for %s" % (n_warnings, arg))
        if len(rem_args) == 1:
            exit(n_warnings)
