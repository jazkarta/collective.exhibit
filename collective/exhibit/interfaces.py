from zope.interface import Interface
from zope import schema
from collective.exhibit import exhibitMessageFactory as _

class IExhibitSettings(Interface):
    """Describes registry records"""

    exhibit_item_types = schema.Tuple(
        title=_(u"Exhibit Item Content Types"),
        description=_(u"A List of portal types that can be used as items"),
        value_type=schema.TextLine(),
        default=(u'Document',
        )
    )
