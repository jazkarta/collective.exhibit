from zope import schema
from zope.interface import alsoProvides
from z3c.form.interfaces import IEditForm, IAddForm
from plone.directives import form
from plone.supermodel.model import Schema
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.field import NamedBlobImage
from plone.app.textfield import RichText
from plone.formwidget.contenttree import UUIDSourceBinder
from collective.exhibit import exhibitMessageFactory as _


class IExhibitSection(Schema):
    """An Exhibit Section"""

    text = RichText(title=_(u'Text'),
                    required=False,
                    allowed_mime_types=('text/html',),
                    default_mime_type='text/html',
                    output_mime_type='text/x-html-safe',
                    default=u'',
                    )

    image = NamedBlobImage(title=_(u'Image'),
                           required=False)

    show_image = schema.Bool(title=_(u'Show image in default view'))

    section_display = schema.Choice(title=_(u'Section Display'),
                                    values=(u'Slider', u'Grid', u'List'),
                                    default=u'Slider')


class IBulkItemAdd(Schema):
    """Allow bulk addition of exhibit items when creating sections"""

    exhibit_items = schema.List(title=_(u'Item References'),
                                description=_(u'Choose content to be used as '
                                              'a basis for your exhibit '
                                              'items.'),
                                value_type=schema.Choice(
                                                   source=UUIDSourceBinder()),
                                required=False,
                                )
    form.widget(
     exhibit_items='plone.formwidget.contenttree.MultiContentTreeFieldWidget')
    form.fieldset('bulk_add', label=_(u'Bulk Add Exhibit Items'),
                  fields=['exhibit_items'])
    form.omitted('exhibit_items')
    form.no_omit(IEditForm, 'exhibit_items')
    form.no_omit(IAddForm, 'exhibit_items')

alsoProvides(IBulkItemAdd, form.IFormFieldProvider)


class BulkItemAdd(object):
    """Adapter implementing bulk item add"""

    def __init__(self, context):
        self.context = context

    def _get_items(self):
        return []

    def _set_items(self, values):
        context = self.context
        for uid in values:
            createContentInContainer(context,
                                     'collective.exhibit.exhibititem',
                                     referenced_item=uid)
    exhibit_items = property(_get_items, _set_items)
