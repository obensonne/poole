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
from xml.sax.saxutils import escape as xcape
import shutil
import sys
import urlparse

from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer

#------------------------------------------------------------------------------
# constants
#------------------------------------------------------------------------------

RE_MACRO = r'{{ *%s *}}'

MACRO_NAME = "name"
MACRO_SOURCE = "source"
MACRO_CONTENT = "__content__"
MACRO_ENCODING = "__encoding__"

#------------------------------------------------------------------------------
# example content for a new project
#------------------------------------------------------------------------------

SOURCE = """
<!-- source of the original page file -->
<hr style="margin-top: 1em;" />
<span style="font-size: small;">Source of this page:</span>
<pre>%s</pre>
<!-- end: source of the original page file -->
"""

PAGE_HTML = """<html>
<head>
    <meta http-equiv="Content-Type" content="text/html; charset={{ __encoding__ }}" />
    <title>a poole site</title>
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
          color: fefefc;
          text-decoration: none;
      }
      div#footer {
          color: gray;
          text-align: center;
          font-size: small;
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
         <h2>{{ name }}</h2>
    </div>
    <div id="menu">
        {{ menu }}
    </div>
    <div id="content">{{ __content__ }}</div>
    </div>
    <div id="footer">
        Content licensed under <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-by-SA</a>.
        <br />
        Powered by <a href="http://bitbucket.org/obensonne/poole">Poole</a>
    </div>
</body>
</html>
"""

EXAMPLE_PAGES =  {
"index.markdown" : """
name: Home
menu-pos: 0
--- EOM ---

This page's source file is `index.markdown`, written in
[markdown](http://daringfireball.net/projects/markdown/).

The navigation menu above links to all pages having the *menu-pos* macro defined. 

This page's file name is `index` but the name shown above is **Home**.
That's because this page has the *name* macro defined to `Home`.

{{ %s }}
""" % MACRO_SOURCE,

"about.html": """
name: About
menu-pos: 5
--- EOM ---
<p>
This page's source file is <tt>about.html</tt>, written in <b>HTML</b>.
</p>
<p>
Did you read the <a href="barfoo.html">foobar</a>?
</p>
{{ %s }}
""" % MACRO_SOURCE,
                  
"barfoo.textile" : """
name: Foobar
foobaz: boo
--- EOM ---
This page's soure file is @barfoo.textile@, written in "textile":http://textile.thresholdstate.com/.

It does not show up in the menu, because it has no *menu-pos* macro defined.

But it has defined a *foobaz* macro and it says {{ foobaz }}. Yes, it really says {{ foobaz }}.

You can adjust the site layout in the file @page.html@.

{{ %s }}
""" % MACRO_SOURCE
}

#------------------------------------------------------------------------------
# content conversion
#------------------------------------------------------------------------------

MISSING_MODULE = """
<p style="color: red; text-align: center">
Missing Python module <strong>%s</strong>.
<br/>
Either install this module or use another markup language for your pages.
</p>
{{ source }}
"""

try:
    import markdown
except ImportError:
    markdown = None
try:
    import textile
except ImportError:
    textile = None

PAGE_FILE_EXTS = (".md", ".markdown", ".textile", ".html")

def convert(content, markup):
    """Convert content of given type into HTML."""
    
    markup = markup.strip(".")
    
    if markup in ("md", "markdown"):
        if markdown:
            return markdown.Markdown().convert(content)
        else:
            return MISSING_MODULE % ("markdown")
    if markup in ("textile",):
        if textile:
            return unicode(textile.textile(content.encode("utf8")))
        else:
            return MISSING_MODULE % ("textile")

    return content

#------------------------------------------------------------------------------
# macro dictionary
#------------------------------------------------------------------------------

class MacroDict(dict):
    """Dictionary merging site and page specific macros.
    
    Value lookup order:
      * plain dictionary entry (in-page macro)
      * function or variable in macro module (site-global macro)
      * function in MacroDict (built-in macro)

    If all of these fail, a warning string is returned.
    
    """
    pages = None
    
    def __init__(self, macros, page):
        """Create new macro dictionary.
        
        Page macros have higher priority than site macros set in `macros`.
        
        """
        super(MacroDict, self).__init__()
        self.__macros = macros
        self.__page = page
        
    def __getitem__(self, key):
        
        # in-page macro definition
        if key in self:
            return super(MacroDict, self).__getitem__(key)
        
        # split macro into name and arguments
        name = key.split(None, 1)[0]
        kwargs = {}
        for key, value in [kv.split("=", 1) for kv in key.split()[1:]]:
            if "," in value:
                value = [v.strip() for v in value.split(",")]
            kwargs[str(key)] = value
        
        macro = getattr(self.__macros, name, None)

        # function macro in macro module
        if inspect.isfunction(macro):
            return macro(self.pages, self.__page, **kwargs)
        
        # string macro in macro module
        if not macro is None:
            return str(macro)
        
        # built-in macro
        macro = getattr(self, "_builtin_%s" % name, None)
        if macro:
            return macro(**kwargs)
        
        # macro not defined -> warning
        print("warning: page %s uses undefined macro '%s'" %
              (self.__page.path, name))
        return ""
        
    #--------------------------------------------------------------------------
    # built-in macros
    #--------------------------------------------------------------------------

    def _builtin_menu(self, tag="span", current="current"):
        """Compile an HTML list of pages to appear as a navigation menu.
        
        Any page which has a macro `menu-pos` defined is included. Menu
        positions are sorted by the integer values of `menu-pos` (smallest
        first).
        
        The current page's tag element is assigned the CSS class `active`.
        
        """
        menu_pages = [p for p in self.pages if "menu-pos" in p.macros]
        menu_pages.sort(key=lambda p: int(p.macros["menu-pos"]))
        
        html = ''
        for p in menu_pages:
            style = p.name == self.__page.name and (' class="%s"' % current) or ''
            html += '<%s%s><a href="%s">%s</a></%s>' % (tag, style, p.url,
                                                        p.name, tag)
        return html

#------------------------------------------------------------------------------
# page class
#------------------------------------------------------------------------------

class Page(object):
    """Abstraction of a page."""
    
    _re_eom = r'^-+ *EOM *-+ *\n?$'
    _sec_macros = "macros"
    
    def __init__(self, path, strip, site_macros, enc_in):
        """Create a new page.
        
        @param path: full path to page input file
        @param strip: portion of path to strip from `path` for deployment
        @param site_macros: site macros
        @param enc_in: encoding of page input file
        
        """
        base, ext = os.path.splitext(path)
        base = base[len(strip):].lstrip(os.path.sep)
        self.url = "%s.html" % base.replace(os.path.sep, "/")
        self.path = "%s.html" % base
        
        self.macros = MacroDict(site_macros, self)
        
        with codecs.open(path, 'r', enc_in) as fp:
            self.raw = fp.readlines()
        
        # split raw content into macro definitions and real content
        macro_defs = ""
        content = ""
        for line in self.raw:
            if not macro_defs and re.match(self._re_eom, line):
                macro_defs = content
                content = ""
            else:
                content += line

        # evaluate macro definitions
        with os.tmpfile() as tf:
            tf.write("[%s]\n" % self._sec_macros)
            tf.write(macro_defs)
            tf.flush()
            tf.seek(0)
            cp = SafeConfigParser()
            cp.readfp(tf)
        for key in cp.options(self._sec_macros):
            self.macros[key] = cp.get(self._sec_macros, key)
        
        # page name (fall back to file name if macro 'name' is not set)
        if not MACRO_NAME in self.macros:
            self.macros[MACRO_NAME] = os.path.basename(base)
            print("warning: no 'name' macro for %s, using filename" % self.path)
        self.name = self.macros[MACRO_NAME]
        
        # convert to HTML
        self.content = convert(content, ext)
        
#------------------------------------------------------------------------------
# helper
#------------------------------------------------------------------------------

def site_macros(project):
    """Get site macros module or a dummy if undefined."""
    
    sys.path.insert(0, project)
    try:
        import macros
    except ImportError:
        class macros: pass
    finally:
        del(sys.path[0])
    return macros    

#------------------------------------------------------------------------------
# commands
#------------------------------------------------------------------------------

def build(project, base_url, enc_in, enc_out):
    """Build a site project."""
    
    dir_in = opj(project, "input")
    dir_out = opj(project, "output")
    page_html = opj(project, "page.html")

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
    
    # site macros
    macros = site_macros(project)
        
    # read and render pages
    pages = []
    for cwd, dirs, files in os.walk(dir_in):
        cwd_site = cwd[len(dir_in):].lstrip(os.path.sep)
        for sdir in dirs:
            os.mkdir(opj(dir_out, cwd_site, sdir))
        for f in files:
            if os.path.splitext(f)[1] in PAGE_FILE_EXTS:
                page = Page(opj(cwd, f), dir_in, macros, enc_in)
                page.macros["base_url"] = base_url
                pages.append(page)
            else:
                shutil.copy(opj(cwd, f), opj(dir_out, cwd_site))

    # make list of pages available in macro dictionaries
    MacroDict.pages = pages
   
    # read page skeleton
    with codecs.open(opj(project, "page.html"), 'r', enc_in) as fp:
        skeleton = fp.read()
    
    for page in pages:
        
        # expand reserved macros
        html = re.sub(RE_MACRO % MACRO_CONTENT, page.content, skeleton)
        html = re.sub(RE_MACRO % MACRO_ENCODING, enc_out, html)
        
        # expand other macros
        macros_used = re.findall(RE_MACRO % "([^}]+)", html)
        for macro in macros_used:
            macro = macro.strip()
            if macro in (MACRO_SOURCE,): continue
            html = re.sub(RE_MACRO % macro, page.macros[macro], html)
        
        # make relative links absolute
        links = re.findall(r'(?:src|href)="([^#/][^"]*)"', html)
        for link in links:
            based = urlparse.urljoin(base_url, link)
            html = html.replace('href="%s"' % link, 'href="%s"' % based)
            html = html.replace('src="%s"' % link, 'src="%s"' % based)
        
        raw = SOURCE % xcape(''.join(page.raw).strip('\n'))
        html = re.sub(RE_MACRO % MACRO_SOURCE, raw, html)
        
        # write HTML page
        with codecs.open(opj(dir_out, page.path), 'w', enc_out) as fp:
            fp.write(html)

    print("success: built project")

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

def get_options():
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
                  metavar="PORT",
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
    
    opts = get_options()
    
    if opts.init:
        init(opts.project)
    if opts.build:
        build(opts.project, opts.base_url, opts.input_enc, opts.output_enc)
    if opts.serve:
        serve(opts.project, opts.port)

if __name__ == '__main__':
    
    main()
