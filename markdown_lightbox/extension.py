from markdown.blockprocessors import BlockProcessor
from markdown.extensions import Extension
from markdown.util import etree
import re

class LightBoxBlockProcessor(BlockProcessor):
    ''' 
        Given markdown block like:
            image[P1000061, mygroup, My clever caption text]

        The following html will be produced:

        <div class="single">
            <a href="img/P1000061.small.jpg" rel="lightbox[mygroup]" title="My clever caption text">
                <img src="img/P1000061.thumb.jpg" alt="My clever caption text" />
            </a>
        </div>
    '''

    def test(self, parent, block):
        return block.startswith('image[')

    def run(self, parent, blocks):
        block = blocks.pop(0)
        txt = re.search('image\[(.*?)\]', block).group(1)
        fn, group, caption = txt.split(',')
        group = group.lstrip()
        caption = caption.lstrip()
        photo_div = etree.SubElement(parent, 'div')
        photo_div.set('class', 'single')
        a_href = etree.SubElement(photo_div, 'a')
        a_href.set('href', 'img/%s.small.jpg' % fn)
        a_href.set('rel', 'lightbox[%s]' % group)
        a_href.set('title', caption)
        img = etree.SubElement(a_href, 'img')
        img.set('src', 'img/%s.thumb.jpg' % fn)
        img.set('alt', caption)


class LightBoxExtension(Extension):
    def extendMarkdown(self, md, md_globals):
        md.parser.blockprocessors.add('LightBox', LightBoxBlockProcessor(md.parser), '_begin')

if __name__ == '__main__':
    import markdown
    html = markdown.markdown('image[image_name_without_extension, my_group_name, Caption text]', extensions=[LightBoxExtension()])
    print html
