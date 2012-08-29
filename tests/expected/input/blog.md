
menu-position: 10
---
Poole has basic blog support. If an input page's file name has a structure like
`page-title.YYYY-MM-DD.post-title.md`, e.g. `blog.2010-02-27.read_this.md`,
Poole recognizes the date and post title and sets them as attributes of the
page. These attributes can then be used to generate a list of blog posts:

<!--%
from datetime import datetime
posts = [p for p in pages if "post" in p] # get all blog post pages
posts.sort(key=lambda p: p.get("date"), reverse=True) # sort post pages by date
for p in posts:
    date = datetime.strptime(p.date, "%Y-%m-%d").strftime("%B %d, %Y")
    print "  * **[%s](%s)** - %s" % (p.post, p.url, date) # markdown list item
%-->

Have a look into `input/blog.md` to see how it works. Feel free to adjust it
to your needs.
