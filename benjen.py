#!/usr/bin/env python

from glob import glob
import codecs, datetime, re, shutil, sys, yaml, os.path
from markdown_lightbox.extension import LightBoxExtension 
from markdown import Markdown
from functools import partial
from mako.lookup import TemplateLookup
from PyRSS2Gen import RSS2, RSSItem, Guid

class Benjen(object):
    def __init__(self):
        self.lookup = TemplateLookup(directories=['templates'])

        self.config = yaml.load(file('config.yaml'))
        trailing_slash = lambda x: x if x.endswith('/') else x+'/'
        self.root_url = trailing_slash(self.config['root_url'])
        self.out = trailing_slash(self.config['path'])
        shutil.rmtree(self.out, ignore_errors=True)
        shutil.copytree('static', self.out)

        self.load_entries()
        self.generate_indexes()
        self.generate_galley()
        map(self.generate_post, self.entries)
        self.generate_statics()
        self.generate_rss()
    
    def render(self, name, **kwargs):
        return self.lookup.get_template('/' + name + '.html').render(**kwargs)

    title_sub = partial(re.compile(r'[^a-zA-Z0-9_\-]').sub, '_')
    def load_entries(self):
        md = Markdown(extensions=['codehilite(guess_lang=False)', 'meta', LightBoxExtension()])
        raw = (file(fn, 'r').read().decode('utf-8') for fn in glob('entries/*'))

        self.entries = []
        self.galley_entries = []

        for entry in raw:
            html, meta = md.convert(entry), md.Meta
            if 'title' not in meta or 'date' not in meta:
                continue
            title, date = meta['title'][0], meta['date'][0]
            tags = meta.get('tags', [])
            print 'Processed', title

            this_entry = dict(
                title=title,
                date=date,
                tags=tags,
                raw=entry,
                html=html,
                link=date + '_' + self.title_sub(title) + '.html'
            )

            if 'galley' in tags:
                self.galley_entries.append(this_entry)
            else:
                self.entries.append(this_entry)

        self.entries.sort(lambda a, b: cmp(b['date'], a['date']))
        self.galley_entries.sort(lambda a, b: cmp(b['date'], a['date']))

    def generate_indexes(self):
        per = self.config['per_page']
        recent = self.entries[:self.config['recent_posts']]
        genFn = lambda i: 'index.html' if i == 0 else 'index_%i.html' % (i / per)
        for i in xrange(0, len(self.entries), per):
            with codecs.open(self.out + genFn(i), 'w', 'utf-8') as fp:
                fp.write(self.render('index',
                    page=(i / per) + 1,
                    pages=(len(self.entries) + per - 1) / per,
                    prev=None if i == 0 else genFn(i - per),
                    next=None if i + per >= len(self.entries) else genFn(i + per),
                    posts=self.entries[i:i+per],
                    recent_posts=recent
                ))

        with codecs.open(self.out + 'archive.html', 'w', 'utf-8') as fp:
            fp.write(self.render('archive', posts=self.entries))

    def generate_galley(self):
        # TODO Remove code duplication
        per = self.config['per_page']
        recent = self.galley_entries[:self.config['recent_posts']]
        genFn = lambda i: 'galley.html' if i == 0 else 'galley_%i.html' % (i / per)
        for i in xrange(0, len(self.galley_entries), per):
            with codecs.open(self.out + genFn(i), 'w', 'utf-8') as fp:
                fp.write(self.render('index',
                    page=(i / per) + 1,
                    pages=(len(self.galley_entries) + per - 1) / per,
                    prev=None if i == 0 else genFn(i - per),
                    next=None if i + per >= len(self.galley_entries) else genFn(i + per),
                    posts=self.galley_entries[i:i+per],
                    recent_posts=recent
                ))

    def generate_post(self, post):
        with codecs.open(self.out + post['link'], 'w', 'utf-8') as fp:
            fp.write(self.render('post', post=post))

    def generate_statics(self):
        gen_pages = ('templates/top.html', 'templates/index.html', 'templates/archive.html', 'templates/post.html')
        static_pages = (os.path.basename(fn) for fn in glob('templates/*') if fn not in gen_pages)

        for static in static_pages:
            print 'Processing', static
            with codecs.open(self.out + static, 'w', 'utf-8') as fp:
                fp.write(self.render(os.path.splitext(static)[0]))

    def generate_rss(self):
        if 'rss_title' not in self.config or 'rss_description' not in self.config:
            return

        all_entries = []
        all_entries.extend(self.entries)
        all_entries.extend(self.galley_entries)

        RSS2(
            title=self.config['rss_title'], 
            link=self.root_url, 
            description=self.config['rss_description'], 
            lastBuildDate=datetime.datetime.now(), 
            items=[
                RSSItem(
                    title=entry['title'], 
                    link=self.root_url + entry['link'], 
                    description=entry['html'], 
                    guid=Guid(self.root_url + entry['link']), 
                    pubDate=datetime.datetime.strptime(entry['date'][:10], '%Y-%m-%d')
                ) for entry in all_entries 
            ]
        ).write_xml(file(self.out + 'feed.xml', 'wb'), encoding='utf-8')

def main():
    Benjen()

if __name__=='__main__':
    Benjen()
