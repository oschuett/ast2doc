#!/usr/bin/env python
# -*- coding: utf-8 -*-

from os import path
from makeHTML import newTag
from render import filename, printout, separator, back_to_top_char

slash_replacement = '__'

#=============================================================================
def encode_package_name(pkgname):
    pkg = "ROOT" if pkgname=='.' else pkgname.replace('/',slash_replacement).upper()
    return "pkg__" + pkg

#=============================================================================
def print_allModules(prefix, modules_list, modules_description, pkgdir=None, packages=None):

    if pkgdir:
        pkgname = 'ROOT' if pkgdir=='.' else pkgdir
        title = " ".join([pkgname, "package"])
        pre = ""
        pkg = newTag('span', content=pkgname, attributes={"class":'pkgname'})
        post = " modules:"
        heading_content = [pre, pkg, post]
        encoded_pkgname = encode_package_name(pkgdir)
        assert(packages)
        print_packageOverview(prefix, pkgname, encoded_pkgname, packages[pkgdir]['description'], modules_list, modules_description)
    else:
        title = "All Modules:"
        heading_content = title
        encoded_pkgname = "pkg__allmodules"

    heading = newTag('h2', content=heading_content, newlines=False)

    mod_items = []
    for module in sorted(modules_list):
        link = newTag('a', content=module, id=module+"__inPackageFrame__"+encoded_pkgname, attributes={"href":module+".html", "target":'moduleFrame', "title":modules_description[module]})
        mod_items.append(newTag('li', content=link))
    mod_list = newTag('ul', content=mod_items, attributes={"class":'modules_in_package'})
    body = newTag('body', content=[heading, mod_list])

    fileBaseName = encoded_pkgname+"-frame"
    printout(body, prefix, title=title, output_file=fileBaseName)
    return fileBaseName+'.html'

#=============================================================================
def print_packageOverview(prefix, pkgname, encoded_pkgname, descr, modules_list, modules_description):

    pkgspan = newTag('span', content=pkgname, attributes={"class":"pkgname"})
    heading = newTag('h3', content=["Overview of package ", pkgspan], newlines=False)
    description = newTag('p', content=descr)
    items = []
    for module in sorted(modules_list):
        link = newTag('a', content=module, attributes={"href":module+".html", "target":'moduleFrame'})
        mod_dt = newTag('dt', content=link, attributes={"style":"padding-top:0.5em;"}, newlines=False)
        mod_descr = newTag('dd', content=modules_description[module])
        items.extend([mod_dt, mod_descr])
    modules_dl = newTag('dl', content=items)
    body = newTag('body', content=[heading, description, modules_dl])

    fileBaseName = encoded_pkgname+"-overview"
    printout(body, prefix, title="Overview of package "+pkgname, output_file=fileBaseName)

#=============================================================================
def print_packageFrame(prefix, modules_lists, modules_description, packages):
    my_packages = [item for item in modules_lists.keys() if not item in ('__ALL__')]

    files = []
    for pkg in sorted(my_packages):
        title = "Modules for package " + 'ROOT' if pkg=='.' else pkg
        heading = newTag('h2', content=title)
        my_modules = modules_lists[pkg]
        my_file = print_allModules(prefix, my_modules, modules_description, pkg, packages)
        files.append(my_file)
    return files

#=============================================================================
def print_packageListFrame(prefix, allModulesFile, src_tree, packages):
    title = "Overview of CP2K API"
    heading = newTag('h2', content=title)

    link = newTag('a', content="All Modules", attributes={"href":allModulesFile, "target":"packageFrame", "style":'font-style:oblique;'})
    allModLink_div = newTag('div', content=link)

    pkglist = getTree(src_tree, packages)
    pkgdir = "."
    pkgname = encode_package_name(pkgdir)
    pkgdescr = packages[pkgdir]['description']
    rootnode = newTag('a', content="[root]", attributes={
        "href":pkgname + "-frame.html",
        "target":"packageFrame",
        "title":pkgdescr,
        "style":'font-style:oblique;',
        "onclick":"resetModuleFrameWithPkgDescr('root', '"+pkgname+"')"
    })
    fakelist = newTag('ul', content=newTag('li', content=[rootnode, pkglist]), attributes={"class":"nobullet"})
    list_heading = newTag('h4', content="Packages:", attributes={"title":"Packages"})
    listContainer_div = newTag('div', content=[list_heading, fakelist])

    body = newTag('body', content=[heading, allModLink_div, listContainer_div])

    fileBaseName = "packages-frame"
    printout(body, prefix, title=title, output_file=fileBaseName, jscript=["js/common.js", "js/resetModuleFrame.js"])
    return fileBaseName+'.html'

#=============================================================================
def getTree(tree, packages, rootnode=None):
    branches = []
    for child in sorted(tree.GetChildren(rootnode)):
        pkgname = encode_package_name(child)
        pkgdescr = packages[child]['description']
        link = newTag('a', content=child, attributes={
            "href":pkgname+"-frame.html",
            "target":"packageFrame",
            "title":pkgdescr,
            "onclick":"resetModuleFrameWithPkgDescr('"+child+"', '"+pkgname+"')"
        })
        list_item = newTag('li', content=link)
        childpkglist = getTree(tree, packages, rootnode=child)
        if childpkglist:
            list_item.addPiece(childpkglist)
        branches.append(list_item)

    if branches:
        pkglist = newTag('ul', content=branches, attributes={"class":"nobullet_noindent"})
        return pkglist

#=============================================================================
def get_banner(indices, prefix):

    buttons = []
    for i, basename in enumerate(indices.l2sort):
        my_title = getattr(indices, basename)
        button_name = indices.brief[i]
        button_id = 'button_' + basename
        target_href = basename + ".html"
        link = newTag('a', content=button_name, id=button_id, attributes={"href":target_href, "target":"moduleFrame", "title":my_title})
        buttons.append( newTag('li', content=link) )

    #  .. quick search (last button handled here since is not actually a html document)
    link = newTag('a', content="Quick search", attributes={"href":"javascript:showhide('qsearch_dropdown')", "class":"dropbtn"})
    form_items = [
        newTag('input', attributes={"type":"text", "name":"whois", "placeholder":"e.g.: dbcsr_filter", "class":"qsearch_text"}), newTag('br'),
        newTag('input', attributes={"type":"radio", "name":"whatis", "value":"symbol", "checked":None}), "symbol", newTag('br'),
        newTag('input', attributes={"type":"radio", "name":"whatis", "value":"module"}), "module", #newTag('br'),
        newTag('input', attributes={"type":"submit", "value":"GO!", "style":"float: right;"})
    ]
    form = newTag('form', content=form_items, attributes={"action":"index.html", "method":'get', "target":"_top"}, newlines=False)
    dropdown_content = newTag('div', content=form, id="qsearch_dropdown", attributes={"class":"dropdown-content"}, newlines=False)
    buttons.append( newTag('li', content=[link, dropdown_content], attributes={"class":'dropdown'}) )

    buttons_list = newTag('ul', content=buttons, attributes={"class":'navlist'})

    CP2kAPIlogo = newTag('img', attributes={"src":'cp2k_apidoc_logo.svg', "alt":'Logo', "class":'logo'})
    header = newTag('h1', content=["CP2K API-Documentation", CP2kAPIlogo], newlines=False)
    banner = newTag('div', content=[header, buttons_list], attributes={"class":'wideautoheightbanner'})
    return banner

#=============================================================================
def activate_item_inplace(active_item_index, banner):

    # banner ___ header (h1)
    #       \
    #        \__ buttons_list (ul) ___ button (li) ___ link (a)

    buttons_list = banner.pieces[1]
    for i, button in enumerate(buttons_list.pieces):
        link = button.pieces[0]
        if i == active_item_index:
            link.attributes["class"] = "active"
        else:
            dummy = link.attributes.pop("class", None)

#=============================================================================
def commit_banner_dump_indices(banner, indices, prefix):

    # loop over buttons (indices)
    for i, index_id in enumerate(indices.l2sort):
        activate_item_inplace(i, banner)
        my_body = indices.bodies[i]
        my_body.addAttribute("class", "landing_page_content")
        title = getattr(indices, index_id)
        body = newTag('body', content=[banner, my_body], attributes={
            "class":"landing_page",
            "onload":"javascript:setContentSize()",
            "onresize":"javascript:setContentSize()"
        })
        printout(body, prefix, title=title, output_file=index_id, jscript=["js/showhide.js", "js/setContentSize.js"], html_class="landing_page")

#=============================================================================
def print_overview(prefix, src_tree, packages, modules_lists, modules_description, sym_lookup_table):

    my_indices = IofIndices()
    # left flushed items
    my_indices.Append( 'Tree',          *print_logical_tree_index(src_tree, modules_lists, modules_description, prefix, packages, sym_lookup_table) )
    my_indices.Append( 'Index',         *print_alphabetic(modules_lists['__ALL__'],           modules_description, prefix, 'all') )
    # right flushed items (last few buttons are swapped since they're right-flushed! if new items here: update accordingly styles.css [ul.navlist li:nth-last-child(XX)]!
    my_indices.Append( 'About',         *print_about_page(prefix) )
    my_indices.Append( 'Custom search', *print_gcse_page(prefix) )

    # prepare the header & navigation bar
    banner = get_banner(my_indices, prefix)

    # insert the banner into all the landing page tabs and dump them
    commit_banner_dump_indices(banner, my_indices, prefix)

    initial_index = 0
    return my_indices.l2sort[initial_index]+".html"

#=============================================================================
def print_landingPage(prefix, src_tree, packages, modules_lists, modules_description, sym_lookup_table):

    allModulesFile  = print_allModules(prefix, modules_lists['__ALL__'], modules_description)
    pkgModulesFiles = print_packageFrame(prefix, modules_lists, modules_description, packages)
    packageListFile = print_packageListFrame(prefix, allModulesFile, src_tree, packages)
    overviewFile    = print_overview(prefix, src_tree, packages, modules_lists, modules_description, sym_lookup_table)

    title = 'CP2K API Documentation'

    packageListFrame = newTag('frame', id="packageListFrame", attributes={"src":packageListFile, "name":"packageListFrame", "title":"All Packages"})
    packageFrame     = newTag('frame', id="packageFrame",     attributes={"src":allModulesFile,  "name":"packageFrame",     "title":"All Modules"})
    moduleFrame      = newTag('frame', id="moduleFrame",      attributes={"src":overviewFile,    "name":"moduleFrame",      "title":"Module descriptions"})

    noscript = newTag('noscript', content=newTag('div', content="JavaScript is disabled on your browser."))
    heading  = newTag('h2', content="Frame Alert")
    paragrph = newTag('p',  content="This document is designed to be viewed using the frames feature. If you see this message, you are using a non-frame-capable web client.")
    noframes = newTag('noframes', content=[noscript, heading, paragrph])

    inner_frameset = newTag('frameset', content=[packageListFrame, packageFrame], attributes={
        "rows":"50%,50%", "title":"Left frames", "onload":"top.loadFrames()"})
    outer_frameset = newTag('frameset', content=[inner_frameset, moduleFrame, noframes], attributes={
        "cols":"20%,80%", "title":"Documentation frame", "onload":"top.loadFrames()"})

    printout(outer_frameset, prefix, title=title, output_file="index", jscript=["modules_publics.json", "privates_referenced.json", "js/searchURL.js"])

#=============================================================================
def print_gcse_page(prefix):

    title = 'Custom search'
    body_parts = [newTag('h3', content=title, attributes={"class":'index_title'})]

    # search box
    inner_div = newTag('gcse:searchbox', content="")
    outer_div = newTag('div', content=inner_div, id="searchbox-container", attributes={"style":"width:600px;"})
    body_parts.append(outer_div)

    # search results
    inner_div = newTag('gcse:searchresults', content="", attributes={"linkTarget":"moduleFrame"})
    outer_div = newTag('div', content=inner_div, id="searchresults-container", attributes={"style":"min-height:100px;"})
    body_parts.append(outer_div)

    fileBaseName = 'custom_search'
    gcse_code = "000324016156316545387:r519rvudrhy"
    gcse_link = "https://cse.google.com/cse.js?cx=" + gcse_code
    body_parts.append( newTag('script', content="", attributes={"src":gcse_link, "type":"text/javascript"}) )
    body = newTag('div', content=body_parts)
    return fileBaseName+'.html', title, body

#=============================================================================
import time
def print_about_page(prefix):

    title = 'About CP2K API documentation'
    body_parts = [newTag('h3', content=title, attributes={"class":'index_title'})]

    p = newTag('p', content="Documentation automatically generated via:")
    # fparse
    href = "https://github.com/oschuett/fparse"
    link = newTag('a', content="", attributes={"class":"external_href my_tools", "href":href, "target":'_blank', "rel":'nofollow'})
    fparse = newTag('li', content=["fparse", link])
    # ast2doc
    href = "https://github.com/oschuett/ast2doc"
    link = newTag('a', content="", attributes={"class":"external_href my_tools", "href":href, "target":'_blank', "rel":'nofollow'})
    ast2doc = newTag('li', content=["ast2doc", link])
    l = newTag('ul', content=[fparse, ast2doc])
    body_parts.extend([p, l])

    time_now  = time.strftime("%c")
    time_zone = time.tzname[time.daylight]
    time_info = " ".join(["Last update:", time_now, time_zone]) #Last modified: 2016/04/08 12:11
    body_parts.append(time_info)

    fileBaseName = 'about'
    body = newTag('div', content=body_parts)
    return fileBaseName+'.html', title, body

#=============================================================================
def get_package_stuff(modules_lists, modules_description, packages, pkg_path='__ROOT__'):
    root = path.normpath(path.commonprefix(packages.keys())) 
    be_root = pkg_path=='__ROOT__'
    node = root if be_root else pkg_path
    rel_path = path.relpath(node, root)
    pkg_name = '[root]' if be_root else pkg_path
    pkg_id = node + '__mlist'
    pkg_files = [f.rsplit(".", 1)[0] for f in packages[node]['files']]
    pkg_modules = [f for f in pkg_files if f in modules_lists[rel_path]]
    mlinks = [newTag('a', content=m, attributes={"href":m+".html", "target":'moduleFrame', "title":modules_description[m]}) for m in sorted(pkg_modules)]
    mitems = [newTag('li', content=l) for l in mlinks]
    mlist = newTag('ul', content=mitems, attributes={"class":'horizontal', "style":'padding:5px;'})
    modules_container = newTag('div', content=mlist, attributes={"id":pkg_id, "class":'togglevis'})
    node_button = newTag('a', content=pkg_name, attributes={"href":"javascript:showhide('"+pkg_id+"')", "title":'[show/hide package modules]'})
    if be_root:
        node_button.addAttribute("style", 'font-style:oblique;')
    description = packages[node]['description']
    return [node_button, ' &#8212; ', description, modules_container]

#=============================================================================
def print_logical_tree_index(src_tree, modules_lists, modules_description, prefix, packages, sym_lookup_table=None):

    title = 'Logical tree of ALL packages'

    heading = newTag('h2', content=title, attributes={"class":'index_title'})

    root_item = newTag('li', content=get_package_stuff(modules_lists, modules_description, packages))

    branches = get_tree(src_tree, modules_lists, modules_description, packages, sym_lookup_table)
    assert(branches)
    root_item.addPiece(branches)

    fileBaseName = "tree_index"
    outer_list = newTag('ul', content=root_item, attributes={"class":'nobullet'})
    body = newTag('div', content=[heading, outer_list])

    return fileBaseName+".html", title, body

#=============================================================================
def get_tree(tree, modules_lists, modules_description, packages, sym_lookup_table, rootnode=None):

    children = sorted(tree.GetChildren(rootnode))

    # no need to open a new ordered list if there are no children!
    if(not children):
        return

    children_list = newTag('ul', attributes={"class":'nobullet'})
    for child in children:
        relative_path = child.replace(tree.root,'',1)[1:]
        files = packages[child]['files']

        my_modules_map = {}
        for f in files:
            mod_name = f.rsplit(".", 1)[0].upper()
            if mod_name in sym_lookup_table:
                my_mmap = {}
                for k, v in sym_lookup_table[mod_name]['symbols_map'].iteritems():
                    ext_module, external_sym_name = v.split(':',1)
                    if(ext_module == '__HERE__'): # no forwarded symbols here...
                        assert(k == external_sym_name)
                        my_mmap[k] = k
                if(my_mmap):
                    my_modules_map[mod_name.lower()] = my_mmap

        if(my_modules_map):
            children_item = newTag('li', content=get_package_stuff(modules_lists, modules_description, packages, child))

            # recurse ...
            branches = get_tree(tree, modules_lists, modules_description, packages, sym_lookup_table, rootnode=child)
            if branches:
                children_item.addPiece(branches)

            children_list.addPiece(children_item)

    return children_list

#=============================================================================
def print_alphabetic(mod_list, modules_description, prefix, descr, fmt='html'):
    items_list = sorted(mod_list)
    initials = sorted(set(item[0] for item in items_list))
    items_dict = dict((ini, [item for item in items_list if item.startswith(ini)]) for ini in initials)

    title = 'Alphabetic index of '+descr+' modules'

    if(fmt=='html'):

        heading = newTag('h2', content=title, attributes={"class":'index_title'})

        # initials
        items = []
        for ini in initials:
            link = newTag('a', content=ini.upper(), attributes={"href":'#'+ini.upper()})
            item = newTag('li', content=link)
            items.append(item)
        ini_list = newTag('ul', content=items, id="initials", attributes={"class":'menu'})

        items = []
        for ini in initials:
            inner_items = []
            for mod in items_dict[ini]:
                link = newTag('a', content=mod, attributes={"href":filename(mod), "target":'moduleFrame', "title":modules_description[mod]})
                inner_item = newTag('li', content=link)
                inner_items.append(inner_item)

            inner_list = newTag('ul', content=inner_items)
            columns = newTag('div', content=inner_list, attributes={"class":'columns'})
            back_link = newTag('a', content=back_to_top_char, attributes={"href":'#initials', "title":'[back to top]'})
            head = newTag('h4', content=[back_link, ini.upper()], id=ini.upper(), newlines=False)
            item = newTag('li', content=[head, columns])
            items.append(item)
        outer_list = newTag('ul', content=items, attributes={"class":'nobullet'})

        fileBaseName = "alphabetic_index_"+'_'.join(descr.split())
        body = newTag('div', content=[heading, ini_list, outer_list])

    else:
        assert(False) # Unknown format

    return fileBaseName+".html", title, body

#=============================================================================
def print_disambiguationPage(symbols_db, modules_description, prefix):

    title = "Disambiguation Page"
    heading = newTag('h2', content=title)
    subhead = newTag('h4', content="This disambiguation page lists modules that share the same name for a public symbol")
    body_parts = [heading, subhead]

    todo_list = sorted(s for s in symbols_db if len(symbols_db[s])>1)
    for s in todo_list:
        symbol = s.lower()
        owner_modules = symbols_db[s]
        items = []
        for m in owner_modules:
            module = m.lower()
            link = newTag('a', content=module, attributes={"href":filename(module, hashtag=symbol), "title":modules_description[module]})
            items.append(newTag('li', content=link))
        sname = newTag('span', content=symbol, id=symbol, attributes={"class":"symname"})
        p = newTag('p', content=[sname, " symbol found in "+str(len(owner_modules))+" modules:"])
        l = newTag('ul', content=items, attributes={"class":"horizontal", "style":'padding-top: 0;'})
        body_parts.extend([p, l])

    body = newTag('body', content=body_parts)
    fileBaseName = "disambiguation"
    printout(body, prefix, title=title, output_file=fileBaseName)

#=============================================================================
class IofIndices():

    def __init__(self, fmt='html'):
        self.l2sort = []
        self.brief  = []
        self.bodies = []
        self.fmt = fmt
        self.dname = None

    def Append(self, brief, fn, t, body):
        assert(fn.endswith('.' + self.fmt))
        dname = path.dirname(fn)
        if(self.dname):
            assert(dname == self.dname)
        else:
            self.dname = dname
        fname = path.basename(fn)
        k = fname.rsplit('.',1)[0]
        setattr(self, k, t)
        self.l2sort.append(k)
        self.brief.append(brief)
        self.bodies.append(body)

#EOF
