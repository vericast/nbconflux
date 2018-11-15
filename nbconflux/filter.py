import re

from bleach import Cleaner
from html5lib.filters.base import Filter

# Tags, attributes, and styles allowed in Confluence storage format according to
# https://confluence.atlassian.com/doc/confluence-storage-format-790796544.html
ALLOWED_TAGS = ['a', 'ac:image', 'ac:layout', 'ac:layout-cell', 'ac:layout-section', 'ac:link',
                'ac:plain-text-link-body', 'ac:task-list', 'big', 'blockquote', 'br', 'code', 'div',
                'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'li', 'ol', 'p', 'pre',
                'ri:attachment', 'ri:page', 'ri:url', 'small', 'span', 'strong', 'sub', 'sup',
                'table', 'tbody', 'td', 'tfoot', 'th', 'thead', 'tr', 'tt', 'u', 'ul',
                'ac:structured-macro', 'ac:parameter',
                # Allow for full removal with RemovalFilter
                'style']

ALLOWED_ATTRS = {'*': ['class'], 'a': ['href', 'title'], 'span': ['style'],
                 'ri:page': ['ri:content-title'], 'ri:attachment': ['ri:filename'],
                 'ac:image': ['ac:title', 'ac:alt'], 'ac:link': ['ac:anchor'],
                 'ri:url': ['ri:value'], 'ac:layout-section': ['ac:type'],
                 'ac:parameter': ['ac:name'],
                 'ac:structured-macro': ['ac:name', 'ac:schema-version'],
                 'td': ['rowspan', 'colspan'], 'th': ['rowspan', 'colspan']}

ALLOWED_STYLES = ['color', 'text-align', 'text-decoration']

# Tags that will be removed along with all of their descendants
REMOVED_TAGS = ['style']

EMPTY_TAG_REGEX = re.compile('<(hr|br)>')

class RemovalFilter(Filter):
    """Removes tags and all of their descendants."""
    def __iter__(self):
        stack = []
        for token in Filter.__iter__(self):
            if 'name' in token and token['name'] in REMOVED_TAGS:
                if token['type'] == 'StartTag':
                    stack.append(token['name'])
                elif token['type'] == 'EndTag':
                    stack.pop(-1)
            elif not stack:
                yield token


def sanitize_html(source):
    """Uses bleach to sanitize HTML of any tags and attributes that are
    invalid in Confluence storage format.

    Uses a regex to workaround https://github.com/mozilla/bleach/issues/28 in
    common cases.
    """
    html = Cleaner(
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRS,
        styles=ALLOWED_STYLES,
        filters=[RemovalFilter],
        strip=True,
        strip_comments=True
    ).clean(source)
    return EMPTY_TAG_REGEX.sub(r'<\1/>', html)
