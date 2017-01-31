#!/usr/bin/env python
# -*- coding: utf-8 -*-

from glob import glob
from os import path
import sys, os, json
from re import match
import utils
from landing_page import print_landingPage, print_disambiguationPage, encode_package_name
from render import printout, render_module, render_external, missing_description, jquery_url, jquery_function

#=============================================================================
def main():
    if(len(sys.argv) != 4):
        print("Usage: ast2doc.py <src-dir> <ASTs-dir> <HTML-output-dir>")
        sys.exit(1)

    src_dir = sys.argv[1]
    ast_dir = sys.argv[2]
    out_dir = sys.argv[3]

    # pre compute the lookup table of imported symbols
    sym_lookup_table = lookup_imported_symbols(ast_dir)

    # dump modules and own publics lists in JSON
    symbols_db = dump_modules_publics(sym_lookup_table, out_dir)

    # build a packages tree
    packages = scan_packages(src_dir)
    src_tree = build_tree(packages)

    # dump packages in JSON
    dump_packages_json(packages, out_dir)

    # module/symbol usage statistics
    statistics = usage_statistics(sym_lookup_table, packages)

    # document all modules public symbols
    modules_lists, modules_description, privates_referenced = document_all_modules(
                                        packages=packages,
                                        ast_dir=ast_dir,
                                        output_dir=out_dir,
                                        sym_lookup_table=sym_lookup_table)

    # dump private referenced symbols in JSON
    dump_privates_referenced(privates_referenced, out_dir)

    # mention external/intrinsic modules
    render_external(out_dir)

    # Landing page
    print_landingPage(prefix=out_dir,
                      src_tree=src_tree,
                      packages=packages,
                      modules_lists=modules_lists,
                      modules_description=modules_description,
                      statistics=statistics,
                      sym_lookup_table=sym_lookup_table)

    # Disambiguation page
    print_disambiguationPage(symbols_db, modules_description, out_dir)

#=============================================================================
def usage_statistics(sym_lookup_table, packages):

    counter = {'__SYMBOLS__':{}, '__MODULES__':{}}
    for module in sym_lookup_table:
        symmap = sym_lookup_table[module]['symbols_map']
        my_used_modules = set()
        for sym, smap in symmap.iteritems():
            ext_mod, ext_sym = smap.split(':',1)
            if(ext_mod in ('__PRIV__', '__HERE__', '__EXTERNAL__')):
                pass
            elif(ext_mod=="__MULTI__"):
                for item in eval(ext_sym):
                    m = item.split(':')[0]
                    my_used_modules.add(m)
                    counter['__SYMBOLS__'].setdefault(item, 0)
                    counter['__SYMBOLS__'][item] += 1
            else:
                if(match('__\w+__', ext_mod)): raise Exception('Unexpected EXT_MOD: "%s"' % ext_mod)
                my_used_modules.add(ext_mod)
                counter['__SYMBOLS__'].setdefault(smap, 0)
                counter['__SYMBOLS__'][smap] += 1
        for ext_mod in my_used_modules:
            counter['__MODULES__'].setdefault(ext_mod, 0)
            counter['__MODULES__'][ext_mod] += 1

    statistics = {}
    for key in ('__MODULES__', '__SYMBOLS__'):
        statistics[key] = sorted([(k,v) for k,v in counter[key].iteritems() if v>1], key=lambda item: item[1])
        statistics[key].reverse()

    # statistics per package
    pkgfiles = dict( (k, packages[k]['files']) for k in packages.keys() )
    filepkg = {}
    for k, flist in pkgfiles.iteritems():
        filepkg.update( dict( (f[:-2].upper(), k) for f in flist ) )
        statistics[k] = {'__MODULES__':[], '__SYMBOLS__':[]}
    for k in ('__MODULES__', '__SYMBOLS__'):
        for item in statistics[k]:
            mod = item[0].split(':',1)[0] # this works in both k cases!
            if not mod in utils.external_modules:
                pkg = filepkg[mod]
                statistics[pkg][k].append(item)

    return statistics

#=============================================================================
def lookup_imported_symbols(ast_dir):

    sym_lookup_table = {}

    for f in glob(path.join(ast_dir, "*.ast")):
        print("Reading for cache: " + f)
        ast = utils.read_ast(f, do_doxycheck=False)
        utils.cache_symbol_lookup(ast, ast_dir, sym_lookup_table)

    return(sym_lookup_table)

#=============================================================================
def document_all_modules(packages, ast_dir, output_dir, sym_lookup_table):

    # init
    modules_lists = {'__ALL__':[]}
    modules_description = {}
    privates_referenced = {}

    # scan packages
    src_root = path.normpath(path.commonprefix(packages.keys()))
    for d, p in packages.iteritems():
        # d: dir hosting a PACKAGE file, p: basically the eval()uation of that PACKAGE file
        rel_path = path.relpath(d, src_root)
        modules_lists[rel_path] = []

        # scan PACKAGE-owned module files (the 'files' key is contributed by the scan_packages() function)
        for f in p['files']:
            mod_name = f.rsplit(".", 1)[0]
            ast_file = path.join(ast_dir, mod_name + ".ast")
            if(path.isfile(ast_file)):
                print("Reading ast: "+ast_file)
                ast = utils.read_ast(ast_file)
                if(ast['tag'] == 'module'):
                    if(utils.verbose()): print '>>>> Module: %s [%s]' % (mod_name, rel_path)

                    # lists of modules per PACKAGE, needed by the landing page
                    modules_lists[rel_path].append(mod_name)
                    modules_lists['__ALL__'].append(mod_name)
                    modules_description[mod_name] = ast['descr'][0] if ast['descr'] else missing_description # Only 1st \brief is retained here

                    # dump the current module HTML documentation
                    body, my_privates_referenced = render_module(ast, rel_path, ast_dir, output_dir, sym_lookup_table)
                    printout(body, output_dir, mod_name=mod_name,
                        jscript=['packages_modules.json', 'js/common.js', 'js/updateURL.js', 'js/highlightArgument.js', jquery_url],
                        custom_script=jquery_function%mod_name)
                    if my_privates_referenced:
                        privates_referenced[mod_name.upper()] = my_privates_referenced

    return modules_lists, modules_description, privates_referenced

#=============================================================================
def dump_modules_publics(sym_lookup_table, out_dir):

    # modules DB
    mdump = json.dumps(sym_lookup_table.keys(), sort_keys=True).lower()

    # symbols DB
    syms = {}
    dummy = [syms.setdefault(s, []).append(m) for m in sym_lookup_table for s in sym_lookup_table[m]['my_symbols']]
    sdump = json.dumps(syms).lower()

    f = open(path.join(out_dir, 'modules_publics.json'), 'w')
    f.write("modules = '" + mdump + "'\n")
    f.write("symbols = '" + sdump + "'\n")
    f.close()

    return syms

#=============================================================================
def dump_privates_referenced(privates_referenced, out_dir):
    syms = {}
    dummy = [syms.setdefault(s, []).append(m) for m in privates_referenced for s in privates_referenced[m]]
    sdump = json.dumps(privates_referenced).lower()
    f = open(path.join(out_dir, 'privates_referenced.json'), 'w')
    f.write("modules_priv_symbols = '" + sdump + "'\n")
    f.write("priv_symbols = '" + json.dumps(syms).lower() + "'\n")
    f.close()

#=============================================================================
def scan_packages(src_dir):
    packages = {}
    for root, dirs, files in os.walk(src_dir):
        if("PACKAGE" in files):
            content = open(path.join(root,"PACKAGE")).read()
            package = eval(content)
            package['files'] = [f for f in files if f.endswith(".F")]
            rel_path = path.relpath(root, src_dir)
            packages[rel_path] = package
    return(packages)

#=============================================================================
def dump_packages_json(packages, out_dir):

    # packages DB
    pdump = json.dumps([encode_package_name(p) for p in packages], sort_keys=True)

    # modules DB
    mdump = json.dumps(dict( (f[:-2], encode_package_name(p)) for p in packages for f in packages[p]['files'] ))

    f = open(path.join(out_dir, 'packages_modules.json'), 'w')
    f.write("packages = '" + pdump + "'\n")
    f.write("modules = '" + mdump + "'\n")
    f.close()

#=============================================================================
def build_tree(packages):

    src_root = path.normpath(path.commonprefix(packages.keys()))
    tree = Tree(src_root)

    for folder in packages.iterkeys():

        # only include the forlders that have some .F files within
        if(packages[folder]['files']):
            rel_path = path.relpath(folder, src_root)
            tree.NewPath(rel_path)

    return(tree)

#=============================================================================
class Tree():

    def __init__(self, root_dir):
        self.tree = {root_dir:{'parent':None, 'children':[]}}
        self.root = root_dir

    def NewPath(self, rel_path):
        parent = self.root
        for me in rel_path.split("/"):
            self.NewNode(me, parent)
            parent = path.normpath(path.join(parent, me))

    def NewNode(self, me, parent):
        my_id = path.normpath(path.join(parent, me))
        if(not my_id in self.tree):
            self.tree[my_id] = {'parent':parent, 'children':[]}
            assert(not my_id in self.tree[parent]['children'])
            self.tree[parent]['children'].append(my_id)

    def GetChildren(self, rootnode=None):
        if(not rootnode):
            rootnode = self.root
        return self.tree[rootnode]['children']

    def Print(self, rootnode=None, indent=''):
        if(not rootnode):
            rootnode = self.root
        for d in self.tree[rootnode]['children']:
            me = path.split(d)[1]
            print indent + me
            my_indent = indent + " "*len(me)
            self.Print(d,my_indent)

#=============================================================================
if __name__ == '__main__':
    main()

#EOF
