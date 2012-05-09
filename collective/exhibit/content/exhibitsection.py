from five import grok
from zope import schema

from plone.directives import form, dexterity
from plone.app.textfield import RichText
from collective.exhibit import exhibitMessageFactory as _


class IExhibitSection(form.Schema):
    """An Exhibit Section"""

    text = RichText(title=_(u'Text'),
                    required=False,
                    allowed_mime_types=('text/html',),
                    default_mime_type='text/html',
                    output_mime_type='text/x-html-safe',
                    default=u'',
                    )
