# Poole

**Create simple websites fast, now.**

Poole is an easy to use [Markdown][] driven static website generator. You write
the content of your pages in Markdown and Poole creates a nice and simple site
with a navigation menu. You don't need to learn a template or preprocessing
engine.

Though Poole is made for simple sites, it has basic support for content
generation by embedding Python code in page source files. This is a dirty merge
of content and logic but for simple sites it's a pragmatic way to get things
done fast and easy -- if you know Python you're ready to start.

Check the list of [sites built with Poole][examples] (and feel free to add
yours).

[examples]: https://bitbucket.org/obensonne/poole/wiki/Home

[![Flattr this][flattr-img]][flattr-url]

[![Build status][travis-img]][travis-url]

[flattr-url]: http://flattr.com/thing/142425/Poole
[flattr-img]: http://api.flattr.com/button/flattr-badge-large.png "Flattr this"

[travis-url]: https://travis-ci.org/obensonne/poole
[travis-img]: https://travis-ci.org/obensonne/poole.png?branch=master "Build status"

## Requirements

**You** should know Markdown and optionally Python if you want to use Poole's
dirty content generation capability.

**Your system** should have installed Python ≥ 2.5 and [python-markdown][pymd].
Poole has been tested on Linux but should also work on other Unix systems and
Windows (in theory, [report an issue][issues] if it fails).

[markdown]: http://daringfireball.net/projects/markdown/
[pymd]: https://pypi.python.org/pypi/Markdown

## Getting Started

Clone or download ([zip][zip], [tgz][tgz]) the repository and then put
*poole.py* to your *PATH*:

    $ hg clone http://bitbucket.org/obensonne/poole/ /some/where/poole
    $ export PATH=$PATH:/some/where/poole

**TIP**: You might want to add the last command to your `~/.bashrc`.

**Python3**: Download the packages from the *py3* branch ([zip][zip3],
[tgz][tgz3]) or check out the *py3* branch when cloned.

Create and build a site project:

    $ mkdir /path/to/site/project
    $ cd /path/to/site/project
    $ poole.py --init --theme minimal
    $ poole.py --build
    $ poole.py --serve

Done. You've just created a website! Browse <http://localhost:8080/> and watch
the example pages which have been created during initialization. To write your
own pages, use the example pages in the *input* folder as a starting point.

Next to the *miniaml* theme, there are some other [choices available][themes].

Run `poole.py --build` whenever you've made some changes in the *input* folder.

[zip]: http://bitbucket.org/obensonne/poole/get/default.zip
[tgz]: http://bitbucket.org/obensonne/poole/get/default.tar.gz
[zip3]: https://bitbucket.org/obensonne/poole/get/py3.zip
[tgz3]: http://bitbucket.org/obensonne/poole/get/py3.tar.gz
[themes]: https://bitbucket.org/obensonne/poole/wiki/Themes

## How It Works

Poole takes files from a project's `input` directory and copies them to the
`output` directory. In this process files ending with *md*, *mkd*, *mdown* or
*markdown* get converted to HTML using the project's `page.html` as a skeleton.

Additionally Poole expands any macros used in a page. Don't care about that for
now ..

When running `poole.py --build` in a Poole project, an input directory like
this:

    |- input
        |- index.md
        |- news.mkd
        |- foo.mdown
        |- images
            |- bar.png

will result in an output folder like that:

    |- output
        |- index.html
        |- news.html
        |- foo.html
        |- images
            |- bar.png

## Page Layout

Every Poole page is based on the skeleton file `page.html`. Hence adjusting the
site layout means adjusting `page.html` and extending or replacing its CSS file
`input/poole.css`.

The only thing you should keep in `page.html` are the embedded
{{\_\_content\_\_}} and {{\_\_encoding\_\_}} expressions.  Below is an almost
minimal `page.html` file. It does not look nice but it's a clean starting point
to build your own layout from scratch.

Minimal `page.html`:

    <html>
      <head>
        <meta http-equiv="Content-Type" content="text/html; charset={{ __encoding__ }}" />
      </head>
      <body>
        {{ __content__ }}
      </body>
    </html>

It's easy to apply one of the numerous free CSS templates out there to a Poole
site. For more information read [this blog post with step-by-step
instructions][pimp].

[pimp]: http://obensonne.bitbucket.org/blog/20091122-using-a-free-css-templates-in-poole.html

## Content Generation

Poole allows you to embed Python code in your pages to *generate* content:

`input/some-page.md`:

    Here is normal text in *markdown* flavor.
    {%
    print "hello poole"
    %}
    Did you know? The sum of 2 and 2 is {{ 2 + 2 }}.

This example demonstrates two ways to embed Python code, either as statements or
as expressions:

  1. Everything between `{%` and `%}` are *statements* and whatever is printed
     to *stdout* during their execution is going to be part of the final HTML
     page.
  2. Everything between `{{` and `}}` are *expressions* and their evaluation is
     going to be part of the final page.

**TIP**: Instead of the outer curly brackets `{` and `}` you can also use
`<!--` and `-->` to prevent syntax highlighting markdown editors from getting
confused by the Python code.

**TIP:** To print the code surrounding tags literally, simply escape the
opening tag with a backslash.

[hyde]: http://ringce.com/hyde

### Outsource complex or frequently used code

To keep embedded code short and compact or to reuse it in several pages, it can
be outsourced into a file called `macros.py` in a project's root folder (where
the `page.html` file is located). Every public attribute in `macros.py` is
available within embedded Python code blocks:

`macros.py`:

    from datetime import date
    def today():
        return date.today().strftime("%B %d, %Y")

    author = "Popeye"

`input/some-page.md`:

    This site has been updated on {{ today() }} by {{ author }}.

#### Builtin macros

Builtin macros can be used from the macros module as well as from python
code in your pages and templates (just as if they are defined within
your macros.py).

Currently, there is only one builtin macro available.

`hx(s)`

> Replace the characters that are special within HTML (`&`, `<`, `>` and `"`)
> with their equivalent character entity (e.g., `&amp;`). This should be
> called whenever an arbitrary string is inserted into HTML (i.e. use
> `{{ hx(variable) }}` instead of `{{ variable }}`). You do not need this
> within a markdown context.
>
> Note that `"` is not special in most HTML, only within attributes.
> However, since escaping it does not hurt within normal HTML, it is
> just escaped unconditionally.

### Working with pages

Next to stuff defined in `macros.py` the objects `page` and `pages` are
available in embedded Python code. The first one is a dictionary describing the
page in which the code is embedded. The second one is a list of *all* pages in
the project.

The following attributes are always set in a page dictionary:

  * **title:** The page's title, by default its filename without extension
    (setting alternatives is described in the next section).
  * **fname:** Path to the page's source file, e.g.
    `/path/to/project/input/stuff/news.md`.
  * **url:** The page's relative URL, e.g. for a source page
    `input/stuff/news.md` this is `stuff/news.html`.

The example `page.html` file in a freshly initialized site project uses a
page's *title* attribute:

    ...
    <div id="header">
         <h1>a poole site</h1>
         <h2>{{ page["title"] }}</h2>
    </div>
    ...

**TIP:** All items in a page dictionary are exposed as attributes, i.e.
`page["foobar"]` is identical to `page.foobar`. Dictionary access is useful if
an item may not be set, e.g.: `page.get("foobar", "...")`.

#### Setting page attributes

Page attributes can be set at the top of a page's source file, in [Python's
configuration file style][pyconf]. They are delimited from the page's content
by a line with 3 or more dashes.

`input/stuff/news.md`:

    title: Hot News
    foobar: King Kong
    ---
    Here are some news about {{ page.foobar }}.
    Did I say {% print(page.foobar) %}?

That way you can also set a page's title explicitly, instead of using the file
name. Other useful attributes to set are *description* and *keywords*, which
get used by the default `page.html` file to set HTML meta tags. Here it comes
in handy to set *default* page attributes in the `macros.py` file:

`macros.py`:

    page = { "description": "some stuff", "keywords": "stuff" }

That way you can safely use the *description* and *keywords* attributes without
bothering if they are really defined in every page.

[pyconf]: http://docs.python.org/library/configparser.html

#### Accessing page objects in the macros module

The objects `pages` and `page` are also available within `macros.py`. That
means you can define them as dummys and reference them in `macros.py`. Poole
updates them when loading the `macros` module.

`macros.py`:

    page = {} # you can also set defaults here, see previous section
    pages = []

    def something():
        # when executing this, the page and pages objects above are up-to-date
        print page["title"]

### Options and paths

Similarly to `page` and `pages` the following objects are available within
embedded Python code and within the *macros* module:

  * **options:** The command line arguments given to Poole as parsed by
    [Python's optparse module][pyopts]. For instance the base URL can be
    retrieved by `options.base_url`.
  * **project:** Path to the project's root directory.
  * **input:** Path to the project's input directory.
  * **output:** Path to the project's output directory.

[pyopts]: http://docs.python.org/library/optparse.html

### Character encodings

In case you use non-ASCII characters, check the *encoding* options of Poole. In
most cases working with non-ASCII strings should work straight forward if the
options are set properly (default is *UTF-8*).

However, be aware that page variables defined within page source files and
derived from a page's file name internally are handled as Python *unicode*
objects. That means if you want to refer to non-ASCII page variable names and
values form within embedded Python code or from `macros.py`, make sure to use
*unicode* strings to reference them.

### Custom file converters

If you use [LESS][] or [CleverCSS][] you'll be happy about the possibility to
define custom converters Poole applies to selected files in its building
process. Custom converters may be defined in `macros.py` using a dictionary
named 'converter' with file name patterns as keys and a converter function as
well as a target file name extension as values:

    converter = {
        r'\.ccss': (ccss_to_css, 'css'),
        ...
    }

The converter function `ccss_to_css` must accept the source file name and the
destination file name as arguments. The destination file name is a suggestion
(the source filename mapped to the project's output directory with the
extension given in the converter dictionary) - you are free to choose another
one:

    import clevercss

    def ccss_to_css(src, dst):
        # when `src` is '/path/to/project/input/foo.ccss'
        # then `dst` is '/path/to/project/output/foo.css'
        ccss = open(src).read()
        css = clevercss.convert(ccss)
        open(dst, 'w').write(css)

[clevercss]: http://sandbox.pocoo.org/clevercss/
[less]: http://lesscss.org/

### Pre- and post-convert hooks

All pages converted by Poole may be processed by custom code in `macros.py`
using *hook* functions. In particular, any function whose name starts with
`hook_preconvert_` is run after source markdown files have been parsed but
not yet converted. Similarly, any function whose name starts with
`hook_postconvert_` is run after the content of pages has been converted to
HTML (but still without the skeleton HTML given in the project's `page.html`
file).

Pre-convert hooks are useful to preprocess the markdown source and/or to
generate new virtual pages based on existing real pages:

    def hook_preconvert_foo():
        # important: replace all foos by bars in every page
        for p in pages:
            p.source = p.source.replace("foo", "bar")
        # create a new virtual page which still has a foo
        p = Page("foo.md", virtual="The only page with a *foo*.", title="Foony")
        pages.append(p)

Virtual pages can be created by providing a virtual source filename relative
to the project's input folder and corresponding markdown content. Page
attributes (e.g. `title`) may be given as additional keyword arguments but
may also be encoded in the markdown source as in real markdown input files.

A common use case for post-convert hooks is to generate full content RSS feeds:

    def hook_postconvert_rss():
        # this is kind of pseudo code
        rss = ...
        for p in pages:
            rss.add_item(..., r.html)
        rss.save(".../rss.xml")

More practical and detailed usage examples of hooks and virtual pages can be
found in the recipes.

### Recipes

You can do some pretty fancy and useful things with inlined Python code and
the macros module, for instance generate a list of blog posts or create an RSS
file. Check out the [example recipes][recipes].

[recipes]: https://bitbucket.org/obensonne/poole/wiki/Recipes

## Feedback

Please use the [issue tracker][issues].

[issues]: http://bitbucket.org/obensonne/poole/issues/
