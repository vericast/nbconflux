from nbconvert.filters.markdown_mistune import IPythonRenderer


class ConfluenceMarkdownRenderer(IPythonRenderer):
    def image(self, src, title, alt_text):
        """Renders a Markdown image as a Confluence image tag.

        Parameters
        ----------
        src: str
            Image source URL
        title: str
            Image title attribute
        alt_text: str
            Alternative text description of the image

        Returns
        -------
        str
            Confluence storage format image tag
        """
        title = 'ac:title="{title}"'.format(title=title) if title else ''
        alt_text = 'ac:alt="{alt_text}"'.format(alt_text=alt_text) if alt_text else ''
        html = '<ac:image {title} {alt_text}><ri:url ri:value="{src}" /></ac:image>'.format(title=title, alt_text=alt_text, src=src)
        return html
