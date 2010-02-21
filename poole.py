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
from datetime import datetime
import glob
import inspect
import imp
import optparse
import os
import os.path
from os.path import join as opj
import re
import shutil
import StringIO
import sys
import urlparse

from SimpleHTTPServer import SimpleHTTPRequestHandler
from BaseHTTPServer import HTTPServer

import markdown


#_POST_HEADER_TMPL = """<div class="post-header">
#<h2 class="post-header-title">%s</h2>
#<p class="post-header-date">%s</p>
#<p class="post-header-summary">%s</p>
#</div>
#"""
#
#def bim_post_header(pages, page):
#
#    if not page["post"]:
#        print("error: page %s uses macro `post-header` but it's filename "
#              "does not match a post filename")
#        sys.exit(1)
#    
#    title = page["post"]
#    date = _post_date(page)
#    summary = page["summary"]
#    
#    return _POST_HEADER_TMPL % (title, date, summary)

# -----------------------------------------------------------------------------
# constants
# -----------------------------------------------------------------------------

MKD_PATT = r'\.(?:md|mkd|mdown|markdown)$'

# -----------------------------------------------------------------------------
# example content for a new project
# -----------------------------------------------------------------------------

PAGE_HTML = """<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" lang="en" xml:lang="en">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset={{ __encoding__ }}" />
    <title>poole - {{ title }}</title>
    <meta name="description" content="{{ description }}" />
    <meta name="keywords" content="{{ keywords }}" />
    <link rel="stylesheet" type="text/css" href="poole.css" />
</head>
<body>
    <div id="box">
    <div id="header">
         <h1>a poole site</h1>
         <h2>{{ title }}</h2>
    </div>
    <div id="menu">
{%
mpages = [p for p in pages if "menu-position" in p]
mpages.sort(key=lambda p: int(p["menu-position"]))

for p in mpages:
    style = p["title"] == page["title"] and ' class="current"' or ''
    link = '<a href="%s">%s</a>' % (p["url"], p["title"])
    print '<span%s>%s</span>' % (style, link)
%}
    </div>
    <div id="content">{{ __content__ }}</div>
    </div>
    <div id="footer">
        Built with <a href="http://bitbucket.org/obensonne/poole">Poole</a> &middot;
        Licensed as <a href="http://creativecommons.org/licenses/by-sa/3.0">CC-by-SA</a> &middot;
        <a href="http://validator.w3.org/check?uri=referer">Validate me.</a>
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
## {{ post }}

Posted at
{%
from datetime import datetime
return datetime.strptime(page["date"], "%Y-%m-%d").strftime("%B %d, %Y")
%}

*{{ summary }}*

THE MOVIE INDUSTRY? IN *MY* MACBOOK?
JESUS CHRIST IT'S A BABBY GET IN THE HERO!
BLESS YOU, KEYBOARD CAT. BLEYBOARD CAT.
DISREGARD THAT, I TROLL MONGS.
WHAT *ARE* EMOS? WE JUST DON'T KNOW.

More nonsense at <http://meme.boxofjunk.ws>.
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

# -----------------------------------------------------------------------------
# page class
# -----------------------------------------------------------------------------

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
        
        self["url"] = re.sub(MKD_PATT, ".html", fname)
        self["url"] = self["url"][len(strip):].lstrip(os.path.sep)
        self["url"] = self["url"].replace(os.path.sep, "/")
        
        self.fname = fname
        
        self.opts = opts
        
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
        # if page is a blog post, set post to it's date
        
    def __getitem__(self, key):
        
        if key in self:
            return super(Page, self).__getitem__(key)
        
        if self._modmacs is None:
            self._load_modmacs()
        if hasattr(self._modmacs, key):
            return getattr(self._modmacs, key)
        
        print("warning: page %s uses undefined macro '%s'" % (self.fname, key))
        return ""
    
    def _load_modmacs(self):
        fname = opj(self.opts.project, "macros.py")
        if os.path.exists(fname):
            Page._modmacs = imp.load_source("macros", fname)
            print "loaded"
        else:
            Page._modmacs = object()
            
# -----------------------------------------------------------------------------
# build site
# -----------------------------------------------------------------------------

PYCODE_HEADER="""
import sys
sys.path.insert(0, "%s")
try:
    from macros import *
except ImportError:
    pass
"""

def build(project, opts):
    """Build a site project."""
    
    RE_VAR_ANY = r'(^|[^\\])({{.+?}})' # any variable reference
    RE_VAR_ONE = r'(^|[^\\]){{ *%s *}}' # specific variable reference
    RE_VAR_ONE_REPL = r'\g<1>%s'# replacement for a specific variable reference
    
    RE_PYCODE = r'([^\\]|^)({%(?:.*?\n?)*%})' # any code block
    
    RE_ESCAPED = r'\\({{|{%)' # escaped code block or variable reference
    RE_ESCAPED_REPL = r'\1' # unescaped
    
    def repl_code(m):
        """Replacement callback for re.sub()."""
        code = m.group(2).strip("\n{%}")
        dname = opj(opts.project, ".build")
        shutil.rmtree(dname, ignore_errors=True)
        os.mkdir(dname)
        fname = opj(dname, "pycode.py")
        with open(fname, "w") as fp:
            fp.write(PYCODE_HEADER % opts.project)
            fp.write("def execute(pages, page):\n")
            lines = ["    %s" % l for l in code.split("\n")] # indent lines
            fp.write("\n".join(lines))
        pycode = imp.load_source("pycode", fname)
        stdout = sys.stdout
        sys.stdout = StringIO.StringIO()
        pycode.execute(page.all_pages, page)
        repl = sys.stdout.getvalue()
        sys.stdout = stdout
        shutil.rmtree(dname)
        return "%s%s" % (m.group(1), repl)
    
    def repl_var(m):
        """Replacement callback for re.sub()."""
        if m.group(1) == "\\":
            return m.group(2)
        name = m.group(2).strip(" {}")
        return "%s%s" % (m.group(1), page[name])
        
    def repl_specific_variable(name, value, source):
        """Expand one specific variable in source to value."""
        patt = RE_VAR_ONE % name
        repl = RE_VAR_ONE_REPL % value
        return re.sub(patt, repl, source)
    
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
    
    # read and render pages
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

    # make list of all pages available in page objects
    Page.all_pages = pages
   
    # read page skeleton
    with codecs.open(opj(project, "page.html"), 'r', opts.input_enc) as fp:
        skeleton = fp.read()
    
    for page in pages:
        
        print("info: processing %s" % page.fname)
        
        # replacements, phase 1 (variables and code blocks used in page source)
        out = re.sub(RE_VAR_ANY, repl_var, page.source)
        out = re.sub(RE_PYCODE, repl_code, out, re.MULTILINE)
        
        # convert to HTML
        out = markdown.Markdown().convert(out)
        
        # expand reserved variables
        out = repl_specific_variable("__content__", out, skeleton)
        out = repl_specific_variable("__encoding__", opts.output_enc, out)
        
        # replacements, phase 2 (variables and code blocks used in page.html)
        out = re.sub(RE_VAR_ANY, repl_var, out)
        out = re.sub(RE_PYCODE, repl_code, out, re.MULTILINE)
        
        # un-escape escaped stuff
        out = re.sub(RE_ESCAPED, RE_ESCAPED_REPL, out)
        
        # make relative links absolute
        links = re.findall(r'(?:src|href)="([^#/].*?)"', out)
        for link in links:
            based = urlparse.urljoin(opts.base_url, link)
            out = out.replace('href="%s"' % link, 'href="%s"' % based)
            out = out.replace('src="%s"' % link, 'src="%s"' % based)
        
        # write HTML page
        fname = page.fname.replace(dir_in, dir_out)
        fname = re.sub(MKD_PATT, ".html", fname) 
        with codecs.open(fname, 'w', opts.output_enc) as fp:
            fp.write(out)

    print("success: built project")

# -----------------------------------------------------------------------------
# init site
# -----------------------------------------------------------------------------

def init(project):
    """Initialize a site project."""
    
    if not os.path.exists(project):
        os.makedirs(project)
        
    if os.listdir(project):
        print("error: project dir %s is not empty, abort" % project)
        sys.exit(1)
    
    os.mkdir(opj(project, "input"))
    os.mkdir(opj(project, "output"))
    
    for fname, content in EXAMPLE_FILES.items():
        with open(opj(project, "input", fname), 'w') as fp:
            fp.write(content)

    with open(opj(project, "page.html"), 'w') as fp:
        fp.write(PAGE_HTML)
    
    print("success: initialized project")

# -----------------------------------------------------------------------------
# serve site
# -----------------------------------------------------------------------------

def serve(project, port):
    """Temporary serve a site project."""
    
    root = opj(project, "output")
    if not os.listdir(project):
        print("error: output dir is empty (build project first!), abort")
        sys.exit(1)
    
    os.chdir(root)
    server = HTTPServer(('', port), SimpleHTTPRequestHandler)
    server.serve_forever()

# -----------------------------------------------------------------------------
# options
# -----------------------------------------------------------------------------

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
    
    return opts
    
# -----------------------------------------------------------------------------
# main
# -----------------------------------------------------------------------------

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
