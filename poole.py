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
import imp
import inspect
import optparse
import os
import os.path
from os.path import join as opj
from os.path import exists as opx
import re
import shutil
import StringIO
import sys
import traceback
import urlparse

from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer

import markdown

# =============================================================================
# constants
# =============================================================================

MKD_PATT = r'\.(?:md|mkd|mdown|markdown)$'

# =============================================================================
# example content for a new project
# =============================================================================

PAGE_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset={{ __encoding__ }}" />
    <title>poole - {{ page.title }}</title>
    <meta name="description" content="{{ page.description or 'a poole site' }}" />
    <meta name="keywords" content="{{ page.keywords or 'poole'  }}" />
    <link rel="stylesheet" type="text/css" href="poole.css" />
</head>
<body>
    <div id="box">
    <div id="header">
         <h1>a poole site</h1>
         <h2>{{ page.title }}</h2>
    </div>
    <div id="menu">
<!--%
mpages = [p for p in pages if "menu-position" in p]
mpages.sort(key=lambda p: int(p["menu-position"]))

for p in mpages:
    style = p["title"] == page["title"] and ' class="current"' or ''
    link = '<a href="%s">%s</a>' % (p["url"], p["title"])
    print '<span%s>%s</span>' % (style, link)
%-->
    </div>
    <div id="content">{{ __content__ }}</div>
    </div>
    <div id="footer">
        Built with <a href="http://bitbucket.org/obensonne/poole">Poole</a>
        &middot;
        Licensed as <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-SA</a>
        &middot;
        <a href="http://validator.w3.org/check?uri=referer">Validate me</a>
    </div>
</body>
</html>
"""

EXAMPLE_FILES =  {

"index.md" : """
title: home
menu-position: 0
---

## Welcome to Poole

In Poole you write your pages in [markdown][md]. It's easier to write
markdown than HTML.

Poole sites by default have a navigation menu, like the one above. It contains
all pages having the *menu-position* variable defined, for instance like this:

    menu-position: 1
    ---
    Here starts the normal content of the page, everything above `---` are
    variable definitions.

This page's file name is `index` but the name shown above is **home**.
That's because this page has the *title* variable defined to `home`.

[md]: http://daringfireball.net/projects/markdown/
""",

"layout.md": """
menu-position: 3
---

Every page of a poole site is based on *one global template file*, `page.html`.
All you need to adjust the site layout is to
 
 * edit the page template `page.html` and
 * extend or edit the style file `input/poole.css`.
""",
                  
"blog.md" : """
menu-position: 5
---

Poole has basic support for blog posts. If a file name has a
structure like `page-title.YYYY-MM-DD.post-title`, e.g.
`blog.201010-02-27.read_this.md`, it recognizes the date and post title.
OTOH you don't have to put the date and post-title into the file name, you can
also set them via variables in the page:

    post: Read this, my friend
    date: 2010-02-27
    summary: A very interesting post.
    ----
    ... blog post text ...

Do whatever fit's best in your case. These variables can then be used to
generate a list of blog posts:

{%
from datetime import datetime
pp = [p for p in pages if p["post"]]
pp.sort(key=lambda p: datetime.strptime(p["date"], "%Y-%m-%d"))
for p in pp[:5]:
    title = p["post"]
    date = datetime.strptime(p["date"], "%Y-%m-%d").strftime("%B %d, %Y")
    md = '  * [**%s**](%s) - %s' % (p["post"], p["url"], date)
    md += p["summary"] and '<br/>\\n    *%s*' % p["summary"] or ''
    print(md)
%}

This list has been generated by inline Python code in `input/blog.md`.

*Yes, this is dirty and everything but MVC. Keep in mind that Poole focuses
on small sites where we want to get things done fast and pragmatically.*
""",

"blog.2010-02-01.Doctors_in_my_penguin.md" : """
summary: There is a bank in my eel, your argument is invalid.
---
## {{ page.post }}

Posted at
<!--%
from datetime import datetime
print datetime.strptime(page["date"], "%Y-%m-%d").strftime("%B %d, %Y")
%-->

*{{ page.summary }}*

THE MOVIE INDUSTRY? IN *MY* MACBOOK?
JESUS CHRIST IT'S A BABBY GET IN THE HERO!
BLESS YOU, KEYBOARD CAT. BLEYBOARD CAT.
DISREGARD THAT, I TROLL MONGS.
WHAT *ARE* EMOS? WE JUST DON'T KNOW.

More nonsense at <http://meme.boxofjunk.ws>.

{{ 4 + 4 }}

<!--{ 2 }-->
""",

"poole.css": """
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

"""
}

# =============================================================================
# page class
# =============================================================================

class Page(dict):
    """Abstraction of a source page."""
    
    all_pages = None
    
    _re_eom = r'^---+ *\n?$'
    _sec_macros = "macros"
    _modmacs = None
    
    def __init__(self, fname, strip, opts):
        """Create a new page.
        
        @param fname: full path to page input file
        @param strip: portion of path to strip from `fname` for deployment
        @param opts: command line options
        
        """
        super(Page, self).__init__()
        
        self.update(opts.macros.get("page", {}))
        
        self["url"] = re.sub(MKD_PATT, ".html", fname)
        self["url"] = self["url"][len(strip):].lstrip(os.path.sep)
        self["url"] = self["url"].replace(os.path.sep, "/")
        
        self.fname = fname
        
        with codecs.open(fname, 'r', opts.input_enc) as fp:
            self.raw = fp.readlines()
        
        # split raw content into macro definitions and real content
        vardefs = ""
        self.source = ""
        for line in self.raw:
            if not vardefs and re.match(self._re_eom, line):
                vardefs = self.source
                self.source = "" # only macro defs until here, reset source
            else:
                self.source += line

        # evaluate macro definitions
        tfname = ".page-macros.tmp"
        with codecs.open(tfname, "w", opts.input_enc) as tf:
            tf.write("[%s]\n" % self._sec_macros)
            tf.write(vardefs)
        with codecs.open(tfname, "r", opts.input_enc) as tf:
            cp = SafeConfigParser()
            cp.readfp(tf)
        os.remove(tfname)
        for key in cp.options(self._sec_macros):
            self[key] = cp.get(self._sec_macros, key)
        
        basename = os.path.basename(fname)
        
        fpatt = r'(.+?)(?:\.([0-9]+-[0-9]+-[0-9]+)(?:\.(.*))?)?%s' % MKD_PATT
        title, date, post = re.match(fpatt, basename).groups()
        title = title.replace("_", " ")
        post = post and post.replace("_", " ") or None
        self["title"] = self.get("title", title)
        self["date"] = self.get("date", date)
        self["post"] = self.get("post", post)
        
    def __getitem__(self, key):

        if key in self:
            return super(Page, self).__getitem__(key)
        
        print("warning: variable '%s' is undefined in %s -> "
              "fall back to empty string" % (key, self.fname))
        return ""
    
    def __getattribute__(self, name):
        
        try:
            return super(Page, self).__getattribute__(name)
        except AttributeError:
            return self[name]
        
# =============================================================================
# build site
# =============================================================================

def build(project, opts):
    """Build a site project."""
    
    # -------------------------------------------------------------------------
    # utilities
    # -------------------------------------------------------------------------

    def abort_iex(page, itype, inline, exc):
        """Abort because of an exception in inlined Python code."""
        print("error  : Python %s in %s failed" % (itype, page.fname))
        print((" %s raising the exception " % itype).center(79, "-"))
        print(inline)
        print(" exception ".center(79, "-"))
        print(exc)
        sys.exit(1)
        
    # -------------------------------------------------------------------------
    # regex patterns and replacements
    # -------------------------------------------------------------------------
    
    regx_escp = re.compile(r'\\((?:<!--|{)(?:{|%))') # escaped PI section
    repl_escp = r'\1'
    regx_rurl = re.compile(r'(?<=(?:(?:\n| )src|href)=")([^#/].*?)(?=")')
    repl_rurl = lambda m: urlparse.urljoin(opts.base_url, m.group(1))
    
    regx_eval = re.compile(r'(?<!\\)(?:(?:<!--|{){)((?:.*?\n?)*)(?:}(?:-->|}))')

    def repl_eval(m):
        """Replacement callback for re.sub()."""
        expr = m.group(1)
        env = opts.macros.copy()
        env.update({"pages": pages, "page": page})
        try:
            return str(eval(expr, env))
        except:
            abort_iex(page, "expression", expr, traceback.format_exc())

    regx_exec = re.compile(r'(?<!\\)(?:(?:<!--|{)%)((?:.*?\n?)*)(?:%(?:-->|}))')
    
    def repl_exec(m):
        """Replacement callback for re.sub()."""
        stmt = m.group(1)
        
        # base indentation
        ind_lvl = len(re.findall(r'^(?: *\n)*( *)', stmt, re.MULTILINE)[0])
        ind_rex = re.compile(r'^ {0,%d}' % ind_lvl, re.MULTILINE)
        stmt = ind_rex.sub('', stmt)
        
        # set execution environment
        env = opts.macros.copy()
        env.update({"pages": pages, "page": page})
        
        # execute
        sys.stdout = StringIO.StringIO()
        try:
            exec stmt in env
        except:
            sys.stdout = sys.__stdout__ 
            abort_iex(page, "statements", stmt, traceback.format_exc())
        else:
            repl = sys.stdout.getvalue()[:-1] # remove last line break
            sys.stdout = sys.__stdout__ 
            return repl
    
    def repl_link(m):
        return urlparse.urljoin(opts.base_url, m.group(1))
    
    # -------------------------------------------------------------------------
    # preparations
    # -------------------------------------------------------------------------
    
    dir_in = opj(project, "input")
    dir_out = opj(project, "output")
    page_html = opj(project, "page.html")

    # check required files and folders
    for pelem in (page_html, dir_in, dir_out):
        if not opx(pelem):
            print("error  : %s does not exist, looks like project has not been "
                  "initialized, abort" % pelem)
            sys.exit(1)

    # prepare output directory
    for fod in glob.glob(opj(dir_out, "*")):
        if os.path.isdir(fod):
            shutil.rmtree(fod)
        else:
            os.remove(fod)
    if not opx(dir_out):
        os.mkdir(dir_out)
    
    # -------------------------------------------------------------------------
    # collect input date
    # -------------------------------------------------------------------------
    
    pages = []
    for cwd, dirs, files in os.walk(dir_in):
        cwd_site = cwd[len(dir_in):].lstrip(os.path.sep)
        for sdir in dirs:
            if re.search(opts.ignore, sdir): continue
            os.mkdir(opj(dir_out, cwd_site, sdir))
        for f in files:
            if re.search(opts.ignore, f):
                pass
            elif re.search(MKD_PATT, f):
                page = Page(opj(cwd, f), dir_in, opts)
                pages.append(page)
            else:
                shutil.copy(opj(cwd, f), opj(dir_out, cwd_site))

    # -------------------------------------------------------------------------
    # convert pages
    # -------------------------------------------------------------------------
    
    with codecs.open(opj(project, "page.html"), 'r', opts.input_enc) as fp:
        skeleton = fp.read()
    
    for page in pages:
        
        print("info   : processing %s" % page.fname)
        
        # replacements, phase 1 (expressions and statements in page source)
        out = regx_eval.sub(repl_eval, page.source)
        out = regx_exec.sub(repl_exec, out)
        
        # convert to HTML
        out = markdown.Markdown().convert(out)
        
        # replacements, phase 2 (variables and code blocks used in page.html)
        opts.macros["__content__"] = out
        out = regx_eval.sub(repl_eval, skeleton)
        out = regx_exec.sub(repl_exec, out)
        
        # un-escape escaped stuff
        out = regx_escp.sub(repl_escp, out)
        
        # make relative links absolute
        out = regx_rurl.sub(repl_rurl, out)
        
        # write HTML page
        fname = page.fname.replace(dir_in, dir_out)
        fname = re.sub(MKD_PATT, ".html", fname) 
        with codecs.open(fname, 'w', opts.output_enc) as fp:
            fp.write(out)

    print("success: built project")

# =============================================================================
# init site
# =============================================================================

def init(project):
    """Initialize a site project."""
    
    if not opx(project):
        os.makedirs(project)
        
    if os.listdir(project):
        print("error  : project dir %s is not empty, abort" % project)
        sys.exit(1)
    
    os.mkdir(opj(project, "input"))
    os.mkdir(opj(project, "output"))
    
    for fname, content in EXAMPLE_FILES.items():
        with open(opj(project, "input", fname), 'w') as fp:
            fp.write(content)

    with open(opj(project, "page.html"), 'w') as fp:
        fp.write(PAGE_HTML)
    
    print("success: initialized project")

# =============================================================================
# serve site
# =============================================================================

def serve(project, port):
    """Temporary serve a site project."""
    
    root = opj(project, "output")
    if not os.listdir(project):
        print("error  : output dir is empty (build project first!), abort")
        sys.exit(1)
    
    os.chdir(root)
    server = HTTPServer(('', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# =============================================================================
# options
# =============================================================================

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
    og.add_option("" , "--ignore", default=r"(^\.)|(~$)", metavar="REGEX",
                  help="input files to ignore (default: '(^\.)|(~$)')")
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
    
    # macro module (not an option, but here it is available globally)
    fname = opj(opts.project, "macros.py")
    macmod = opx(fname) and imp.load_source("macros", fname) or None
    opts.macros = {"__encoding__": opts.output_enc}
    for attr in dir(macmod):
        if not attr.startswith("_"):
            opts.macros[attr] = getattr(macmod, attr)
    
    return opts
    
# =============================================================================
# main
# =============================================================================

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
