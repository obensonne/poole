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

See what you get: [example site](http://obensonne.bitbucket.org/).

[![Flattr this][flattr-img]][flattr-url]

[flattr-url]: http://flattr.com/thing/142425/Poole
[flattr-img]: http://api.flattr.com/button/flattr-badge-large.png "Flattr this"

## Requirements

**You** should know Markdown and optionally Python if you want to use Poole's
dirty content generation capability.

**Your system** should have installed Python ≥ 2.5 and python-markdown. Poole
has been tested on Linux but should also work on other Unix systems and Windows
(in theory, [report an issue][issues] if it fails).

[markdown]: http://daringfireball.net/projects/markdown/

## Getting Started

Clone oder download ([zip][zip], [tgz][tgz]) the repository and then put
*poole.py* to your *PATH*:

    $ hg clone http://bitbucket.org/obensonne/poole/ /some/where/poole
    $ export PATH=$PATH:/some/where/poole

**TIP**: You might want to add the last command to your `~/.bashrc`.

Create and build a site project:

    $ mkdir /path/to/site/project
    $ cd /path/to/site/project
    $ poole.py --init
    $ poole.py --build
    $ poole.py --serve

Done. You've just created a website! Browse <http://localhost:8080/> and watch
the example pages which have been created during initialization.

To write your own pages, use the example pages in the *input* folder as a
starting point.

Run `poole.py --build` whenever you've made some changes in the *input* folder.

[zip]: http://bitbucket.org/obensonne/poole/get/tip.zip
[tgz]: http://bitbucket.org/obensonne/poole/get/tip.tar.gz

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
site layout means adjusting `page.html` and extending or replacing its CCS file
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

This example demonstrates 2 ways to embed Python code, either as statements or
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

### Howtos

#### Navigation menu

Have a look into the `page.html` file in a freshly initialized Poole project.

#### List of blog posts

If you want to write some blog posts, you probably would like to have a page
listing all or the latest blog posts. This is easy if you set certain page
attributes in every blog post page:

`input/brain-on-mongs.md`:

    title: blog
    post: This is your brain on mongs
    date: 2010-03-01
    ---

    # {{ page.post }}

    Posted on {{ page.date }}

    My hero is full of keyboards. Get nonsense at <http://automeme.net/>

`input/blog.md`:

    This is my blog.

    # My posts

    {%
    from datetime import datetime
    posts = [p for p in pages if "post" in p] # get all blog post pages
    posts.sort(key=lambda p: p.get("date"), reverse=True) # sort post pages by date
    for p in posts:
        date = datetime.strptime(p["date"], "%Y-%m-%d").strftime("%B %d, %Y")
        print "  * **[%s](%s)** - %s" % (p.post, p.url, date) # markdown list item
    %}

Feel free to adjust this to your needs.

**TIP:** Instead of setting the post title and date as page attributes, you can
encode them in the page's file name using a structure like
`page-title.YYYY-MM-DD.post-title.md`. For instance for the file name
`blog.2010-03-01.This_is_your_brain_on_mongs.md` Poole would automatically set
the page attributes which has been set manually in the example above.

To see this example in action, have a look into the example pages in a freshly
initialized Poole project.

#### Google sitemap file

To generate a Google sitemap.xml file, put this into the project's `macros.py`
file:

    # -----------------------------------------------------------------------------
    # generate sitemap.xml
    # -----------------------------------------------------------------------------

    from datetime import datetime
    import os.path

    _SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
    <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    %s
    </urlset>
    """

    _SITEMAP_URL = """
    <url>
        <loc>%s/%s</loc>
        <lastmod>%s</lastmod>
        <changefreq>%s</changefreq>
        <priority>%s</priority>
    </url>
    """

    def hook_preconvert_sitemap():
        """Generate Google sitemap.xml file."""
        date = datetime.strftime(datetime.now(), "%Y-%m-%d")
        urls = []
        for p in pages:
            urls.append(_SITEMAP_URL % (options.base_url.rstrip('/'), p.url, date,
                        p.get("changefreq", "monthly"), p.get("priority", "0.8")))
        fname = os.path.join(options.project, "output", "sitemap.xml")
        fp = open(fname, 'w')
        fp.write(_SITEMAP % "".join(urls))
        fp.close()

You probably want to adjust the default values for *changefreq* and *priority*.

**Info:** Every function in `macros.py` whose name starts with
`hook_preconvert_` or `hook_postconvert_` is executed exactly once per project
build -- either before or after converting pages from markdown to HTML. In
post-convert hooks the HTML content of a page (yet without header and footer)
can be accessed with `page.html`. This is useful to generate full-content RSS
feeds.

#### RSS feed for blog posts

To generate an RSS feed for blog posts put this into the project's `macros.py`
file and adjust for your site:

    # -----------------------------------------------------------------------------
    # generate rss feed
    # -----------------------------------------------------------------------------

    import email.utils
    import os.path
    import time

    _RSS = """<?xml version="1.0"?>
    <rss version="2.0">
    <channel>
    <title>%s</title>
    <link>%s</link>
    <description>%s</description>
    <language>en-us</language>
    <pubDate>%s</pubDate>
    <lastBuildDate>%s</lastBuildDate>
    <docs>http://blogs.law.harvard.edu/tech/rss</docs>
    <generator>Poole</generator>
    %s
    </channel>
    </rss>
    """

    _RSS_ITEM = """
    <item>
        <title>%s</title>
        <link>%s</link>
        <description>%s</description>
        <pubDate>%s</pubDate>
        <guid>%s</guid>
    </item>
    """

    def hook_postconvert_rss():
        items = []
        posts = [p for p in pages if "post" in p] # get all blog post pages
        posts.sort(key=lambda p: p.date, reverse=True)
        for p in posts:
            title = p.post
            link = "%s/%s" % (options.base_url.rstrip("/"), p.url)
            desc = p.get("description", "")
            date = time.mktime(time.strptime("%s 12" % p.date, "%Y-%m-%d %H"))
            date = email.utils.formatdate(date)
            items.append(_RSS_ITEM % (title, link, desc, date, link))

        items = "".join(items)

        # --- CHANGE THIS --- #
        title = "Maximum volume yields maximum moustaches"
        link = "%s/blog.html" % options.base_url.rstrip("/")
        desc = "My name is dragonforce. You killed my dragons. Prepare to scream."
        date = email.utils.formatdate()

        rss = _RSS % (title, link, desc, date, date, items)

        fp = open(os.path.join(output, "rss.xml"), 'w')
        fp.write(rss)
        fp.close()

#### Convert CleverCSS to CSS

To convert all [CleverCSS][] files in the `input` directory to regular CSS
files in the `output` directory, put this into the project's `macros.py`
(assuming you use `.ccss` as file name extension):

    # -----------------------------------------------------------------------------
    # convert clevercss files to css
    # -----------------------------------------------------------------------------

    import clevercss
    import glob
    import os.path
    
    def hook_preconvert_ccss(): # pre- or post-convert hook, doesn't matter
        for ccss in glob.glob(os.path.join(input, "**.ccss")):
            css = ccss[len(input):].lstrip("/")
            css = "%s.css" % os.path.splitext(css)[0]
            css = os.path.join(output, css)
            fpi = open(ccss)
            fpo = open(css, 'w')
            fpo.write(clevercss.convert(fpi.read()))
            fpi.close()
            fpo.close()

To prevent the original *CCSS* files from getting copied to the output
directory, use Poole's *--ignore* option:
`poole.py --build --ignore '^\.|~$|\.ccss$'`.

[clevercss]: http://sandbox.pocoo.org/clevercss/

## Feedback

Please use the [issue tracker][issues].

[issues]: http://bitbucket.org/obensonne/poole/issues/
