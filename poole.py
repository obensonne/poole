#!/usr/bin/python

# =============================================================================
#
#    Poole - A damn simple static website generator.
#    Copyright (C) 2009 Oben Sonne <obensonne@googlemail.com>
#
#    This file is part of Poole.
#
#    Poole is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    Poole is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with Poole.  If not, see <http://www.gnu.org/licenses/>.
#
# =============================================================================

from __future__ import with_statement

import codecs
from ConfigParser import SafeConfigParser
import glob
import inspect
import optparse
import os
import os.path
from os.path import join as opj
import re
import shutil
import sys
import urlparse

from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer

import markdown

#------------------------------------------------------------------------------
# constants
#------------------------------------------------------------------------------

MACRO_TITLE = "title"
MACRO_MENU = "menu-position"
MACRO_CONTENT = "__content__"
MACRO_ENCODING = "__encoding__"

#------------------------------------------------------------------------------
# example content for a new project
#------------------------------------------------------------------------------

PAGE_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset={{ %s }}" />
    <title>Poole - %s</title>
    <style type="text/css" id="internalStyle">
      body {
          font-family: sans;
          width: 800px;
          margin: 1em auto;
          color: #2e3436;
      }
      div#box {
          border: solid #2e3436 1px;
      }
      div#header, div#menu, div#content, div#footer {
          padding: 1em;
      }
      div#menu {
          background-color: #2e3436;
          padding: 0.6em 0 0.6em 0;
      }
      #menu span {
          background-color: #2e3436;
          font-weight: bold;
          padding: 0.6em;
      }
      #menu span.current {
          background-color: #555753;
      }
      #menu a {
          color: #fefefc;
          text-decoration: none;
      }
      div#footer {
          color: gray;
          text-align: center;
          font-size: small;
      }
      div#footer a {
          color: gray;
          text-decoration: none;
      }
      pre {
          border: dotted black 1px;
          background: #eeeeec;
          font-size: small;
          padding: 1em;
      }
    </style>
</head>
<body>
    <div id="box">
    <div id="header">
         <h1>a poole site</h1>
         <h2>{{ %s }}</h2>
    </div>
    <div id="menu">
        {{ menu }}
    </div>
    <div id="content">{{ %s }}</div>
    </div>
    <div id="footer">
        Built with <a href="http://bitbucket.org/obensonne/poole">Poole</a> &middot;
        Licensed as <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-by-SA</a> &middot;
        <a href="http://validator.w3.org/check?uri=referer">Validate me.</a>
    </div>
</body>
</html>
""" % (MACRO_ENCODING, MACRO_TITLE, MACRO_TITLE, MACRO_CONTENT)

EXAMPLE_PAGES =  {
"index.md" : """
%s: home
%s: 0
---

## Welcome to Poole

In Poole you write your pages in [markdown][md]. It's easier to write
markdown than HTML.

Poole sites by default have a navigation menu, like the one above. It contains
all pages having the *menu-position* macro defined, for instance like this:

    menu-position: 1
    ---
    Here starts the normal content of the page, everything above `---` are
    macro definitions.

This page's file name is `index` but the name shown above is **home**.
That's because this page has the *title* macro defined to `home`.

[md]: http://daringfireball.net/projects/markdown/
""" % (MACRO_TITLE, MACRO_MENU),

"layout.md": """
%s: 5
---

Every page of a poole site is based on *one global template file*, `page.html`.
All you need to adjust the site layout is to edit the `page.html` file.

The blog post *[Pimp your Poole site with a free CSS template][bp]* is a good
starting point if you'd like to adjust the site layout. 

### Did you ..
.. read the [foobar](barfoo.html)?

[bp]: http://obensonne.bitbucket.org/blog/20091122-using-a-free-css-templates-in-poole.html

""" % (MACRO_MENU),
                  
"barfoo.md" : """
foobaz: boo
---
This page's soure file is *barfoo.md*. It does not show up in the menu, because
it has not defined the *menu-position* macro. But it has defined a *foobaz*
macro and it says {{ foobaz }}. Yes, it really says {{ foobaz }}.

"""
}

#--------------------------------------------------------------------------
# built-in macros
#--------------------------------------------------------------------------

def bim_menu(pages, page, tag="span", current="current"):
    """Expands to HTML code for a navigation menu.
    
    The name of any page which has a macro `menu-posistion` defined is
    included in the menu. Menu positions are sorted by the integer values
    of `menu-position` (smallest first).
    
    Each menu entry is surrounded by the HTML tag given by the keyword
    `tag`. The current page's tag element is assigned the CSS class
    given by keyword `current`.
    
    """
    mpages = [p for p in pages if MACRO_MENU in p.macros]
    mpages.sort(key=lambda p: int(p.macros[MACRO_MENU]))
    
    html = ''
    for p in mpages:
        style = p.title == page.title and (' class="%s"' % current) or ''
        html += '<%s%s><a href="%s">%s</a></%s>' % (tag, style, p.url,
                                                    p.title, tag)
    return html

BIMS = {
    "menu": bim_menu,
}

#------------------------------------------------------------------------------
# macro dictionary
#------------------------------------------------------------------------------

class MacroDict(dict):
    """Dictionary merging site and page specific macros.
    
    Value lookup order:
      * plain dictionary entry (in-page macro)
      * function or variable in macro module (site-global macro)
      * function macro in BIMS (built-in macro)

    If all fail, an empty string is returned and a warning is printed.
    
    """
    pages = None
    module = None
    
    def __init__(self, page):
        """New macro dictionary."""
        
        super(MacroDict, self).__init__()
        self.page = page
        
    def __getitem__(self, key):
        
        # in-page macro definition
        if key in self:
            return super(MacroDict, self).__getitem__(key)
        
        key = key.replace("-", "_")
        
        # split macro into name and arguments
        name = key.split(None, 1)[0]
        kwargs = {}
        for key, value in [kv.split("=", 1) for kv in key.split()[1:]]:
            if "," in value:
                value = [v.strip() for v in value.split(",")]
            kwargs[str(key)] = value
        
        macro = getattr(self.module, name, None)

        # function macro in macro module
        if inspect.isfunction(macro):
            return macro(self.pages, self.page, **kwargs)
        
        # string macro in macro module
        if not macro is None:
            return str(macro)
        
        # built-in macro
        if name in BIMS:
            return BIMS[name](self.pages, self.page, **kwargs)
        
        # macro not defined -> warning
        print("warning: page %s uses undefined macro '%s'" %
              (self.page.path, name))
        return ""
        
#------------------------------------------------------------------------------
# page class
#------------------------------------------------------------------------------

class Page(object):
    """Abstraction of a source page."""
    
    _re_eom = r'^---+ *\n?$'
    _sec_macros = "macros"
    
    def __init__(self, path, strip, opts):
        """Create a new page.
        
        @param path: full path to page input file
        @param strip: portion of path to strip from `path` for deployment
        @param opts: command line options
        
        """
        base = os.path.splitext(path)[0]
        base = base[len(strip):].lstrip(os.path.sep)
        self.url = "%s.html" % base.replace(os.path.sep, "/")
        self.path = "%s.html" % base
        
        self.macros = MacroDict(self)
        self.opts = opts
        
        with codecs.open(path, 'r', opts.input_enc) as fp:
            self.raw = fp.readlines()
        
        # split raw content into macro definitions and real content
        macro_defs = ""
        self.source = ""
        for line in self.raw:
            if not macro_defs and re.match(self._re_eom, line):
                macro_defs = self.source
                self.source = "" # only macro defs until here, reset source
            else:
                self.source += line

        # evaluate macro definitions
        tfname = ".page-macros.tmp"
        with codecs.open(tfname, "w", opts.input_enc) as tf:
            tf.write("[%s]\n" % self._sec_macros)
            tf.write(macro_defs)
        with codecs.open(tfname, "r", opts.input_enc) as tf:
            cp = SafeConfigParser()
            cp.readfp(tf)
        os.remove(tfname)
        for key in cp.options(self._sec_macros):
            self.macros[key] = cp.get(self._sec_macros, key)
        
        # page title (fall back to file name if macro 'title' is not set)
        if not MACRO_TITLE in self.macros:
            self.macros[MACRO_TITLE] = os.path.basename(base)
        self.title = self.macros[MACRO_TITLE]
        
#------------------------------------------------------------------------------
# build site
#------------------------------------------------------------------------------

def build(project, opts):
    """Build a site project."""
    
    RE_MACRO_FIND = r'(?:^|[^\\]){{ *([^}]+) *}}' # any macro
    RE_MACRO_SUB_PATT = r'(^|[^\\]){{ *%s *}}' # specific macro
    RE_MACRO_SUB_REPL = r'\g<1>%s'
    RE_MACRO_X_PATT = r'\\({{ *[^}]+ *}})' # any escaped macro
    RE_MACRO_X_REPL = r'\g<1>'
    RE_FILES_IGNORE = r'(^\.)|(~$)' # files to not copy to output
    
    def expand_macro(macro, value, source):
        """Expand macro in source to value."""
        patt = RE_MACRO_SUB_PATT % macro
        repl = RE_MACRO_SUB_REPL % value
        return re.sub(patt, repl, source)
    
    def expand_all_macros(source, md):
        """Expand all macros in source using given macro dictionary."""
        
        macros = re.findall(RE_MACRO_FIND, source)
        expanded = source
        for macro in macros:
            macro = macro.strip()
            expanded = expand_macro(macro, md[macro], expanded)
        return expanded

    dir_in = opj(project, "input")
    dir_out = opj(project, "output")
    page_html = opj(project, "page.html")

    # check required files and folders
    for pelem in (page_html, dir_in, dir_out):
        if not os.path.exists(pelem):
            print("error: %s does not exist, looks like project has not been "
                  "initialized, abort" % pelem)
            sys.exit(1)

    # prepare output dir
    for fod in glob.glob(opj(dir_out, "*")):
        if os.path.isdir(fod):
            shutil.rmtree(fod)
        else:
            os.remove(fod)
    if not os.path.exists(dir_out):
        os.mkdir(dir_out)
    
    # import site macros module
    sys.path.insert(0, project)
    try:
        import macros as site_macros_module
    except ImportError:
        site_macros_module = None
    del(sys.path[0])
    MacroDict.module = site_macros_module
        
    # read and render pages
    pages = []
    for cwd, dirs, files in os.walk(dir_in):
        cwd_site = cwd[len(dir_in):].lstrip(os.path.sep)
        for sdir in dirs:
            if re.search(RE_FILES_IGNORE, sdir): continue
            os.mkdir(opj(dir_out, cwd_site, sdir))
        for f in files:
            if re.search(RE_FILES_IGNORE, f): continue
            if os.path.splitext(f)[1] in (".md", ".markdown", ".mdown", ".mkd"):
                page = Page(opj(cwd, f), dir_in, opts)
                pages.append(page)
            else:
                shutil.copy(opj(cwd, f), opj(dir_out, cwd_site))

    # make list of pages available in macro dictionaries
    MacroDict.pages = pages
   
    # read page skeleton
    with codecs.open(opj(project, "page.html"), 'r', opts.input_enc) as fp:
        skeleton = fp.read()
    
    for page in pages:
        
        print("info: processing page %s" % page.path)
        
        # expand macros, phase 1 (macros used in page source)
        out = expand_all_macros(page.source, page.macros)
        
        # convert to HTML
        out = markdown.Markdown().convert(out)
        
        # expand reserved macros
        out = expand_macro(MACRO_CONTENT, out, skeleton)
        out = expand_macro(MACRO_ENCODING, opts.output_enc, out)
        
        # expand macros, phase 2 (macros used in page.html)
        out = expand_all_macros(out, page.macros)
        
        # un-escape escaped macros
        out = re.sub(RE_MACRO_X_PATT, RE_MACRO_X_REPL, out)

        # make relative links absolute
        links = re.findall(r'(?:src|href)="([^#/][^"]*)"', out)
        for link in links:
            based = urlparse.urljoin(opts.base_url, link)
            out = out.replace('href="%s"' % link, 'href="%s"' % based)
            out = out.replace('src="%s"' % link, 'src="%s"' % based)
        
        # write HTML page
        with codecs.open(opj(dir_out, page.path), 'w', opts.output_enc) as fp:
            fp.write(out)

    print("success: built project")

#------------------------------------------------------------------------------
# init site
#------------------------------------------------------------------------------

def init(project):
    """Initialize a site project."""
    
    if not os.path.exists(project):
        os.makedirs(project)
        
    if os.listdir(project):
        print("error: project dir %s is not empty, abort" % project)
        sys.exit(1)
    
    os.mkdir(opj(project, "input"))
    os.mkdir(opj(project, "output"))
    
    for page_file, page_content in EXAMPLE_PAGES.items():
        with open(opj(project, "input", page_file), 'w') as fp:
            fp.write(page_content)

    with open(opj(project, "page.html"), 'w') as fp:
        fp.write(PAGE_HTML)
    
    print("success: initialized project")

#------------------------------------------------------------------------------
# serve site
#------------------------------------------------------------------------------

def serve(project, port):
    """Temporary serve a site project."""
    
    root = opj(project, "output")
    if not os.listdir(project):
        print("error: output dir is empty (build project first!), abort")
        sys.exit(1)
    
    os.chdir(root)
    server = HTTPServer(('', port), SimpleHTTPRequestHandler)
    server.serve_forever()

#------------------------------------------------------------------------------
# options
#------------------------------------------------------------------------------

def options():
    """Parse and validate command line arguments."""
    
    usage = ("Usage: %prog --init [path/to/project]\n"
             "       %prog --build [OPTIONS] [path/to/project]\n"
             "       %prog --serve [OPTIONS] [path/to/project]\n"
             "\n"
             "       Project path is optional, '.' is used as default.")
           
    op = optparse.OptionParser(usage=usage)
    
    op.add_option("-i" , "--init", action="store_true", default=False,
                  help="init project")
    op.add_option("-b" , "--build", action="store_true", default=False,
                  help="build project")
    op.add_option("-s" , "--serve", action="store_true", default=False,
                  help="serve project")
    
    og = optparse.OptionGroup(op, "Build options")
    og.add_option("", "--base-url", default="/", metavar="URL",
                  help="base url for relative links (default: /)")
    og.add_option("", "--input-enc", default="utf-8", metavar="ENC",
                  help="encoding of input pages (default: utf-8)")
    og.add_option("", "--output-enc", default="utf-8", metavar="ENC",
                  help="encoding of output pages (default: utf-8)")
    op.add_option_group(og)
    
    og = optparse.OptionGroup(op, "Serve options")
    og.add_option("" , "--port", default=8080,
                  metavar="PORT", type="int",
                  help="port for serving (default: 8080)")
    op.add_option_group(og)
    
    opts, args = op.parse_args()
    
    if opts.init + opts.build + opts.serve < 1:
        op.print_help()
        op.exit()
    
    opts.project = args and args[0] or "."
    
    return opts
    
#------------------------------------------------------------------------------
# main
#------------------------------------------------------------------------------

def main():
    
    opts = options()
    
    if opts.init:
        init(opts.project)
    if opts.build:
        build(opts.project, opts)
    if opts.serve:
        serve(opts.project, opts.port)

if __name__ == '__main__':
    
    main()
