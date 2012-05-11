from five import grok
from Acquisition import aq_inner, aq_parent
from zope import schema
from zope.publisher.interfaces import NotFound
from zope.traversing.interfaces import TraversalError

from plone.directives import form, dexterity
from plone.dexterity.content import Item
from plone.formwidget.contenttree import UUIDSourceBinder
from plone.app.uuid.utils import uuidToObject
from plone.app.content.interfaces import INameFromTitle

from plone.app.textfield import RichText
from plone.app.textfield.interfaces import ITransformer
from plone.namedfile.field import NamedImage
from plone.namedfile.scaling import ImageScaling
from plone.memoize import view
from plone.indexer import indexer
from Products.CMFCore.utils import getToolByName, _checkPermission

from collective.exhibit import exhibitMessageFactory as _


class IExhibitItem(form.Schema):
    """An Exhibit Item.  Often a reference to another object in
    the site/collection."""

    collection_item = schema.Choice(title=_(u'Referenced Item'),
                                    description = _(u'Chose an item from the '
                                                    'collection'),
                                    source=UUIDSourceBinder(),
                                    required=False,
                                    )
    form.widget(collection_item='plone.formwidget.autocomplete.AutocompleteFieldWidget')

    title = schema.TextLine(
        title = _(u'Title'),
        description = _(u'Leave this blank to use the title '
                        'from the referenced item'),
        required = False
        )

    description = schema.Text(
        title=_(u'Summary'),
        description = _(u'Leave this blank to use the summary '
                        'from the referenced item.  This text appears '
                        'in listings and searches.'),
        required = False,
        missing_value = u'',
        )

    image = NamedImage(title=_(u'Image'),
                       description = _(u'Leave this blank to use the '
                                       'primary image from the '
                                       'referenced item'),
                       required=False,
                       )

    text = RichText(title=_(u'Description'),
                    description=_(u'Describe the collection item.  Leave '
                                  'this blank to use the description '
                                  'from the referenced item.'),
                    required=False,
                    allowed_mime_types=('text/html',),
                    default_mime_type='text/html',
                    output_mime_type='text/x-html-safe',
                    default=u'',
                    )

    show_more_link = schema.Bool(title=_(u'Show more info link'),
                                 default=True)


class ExhibitItemScaling(ImageScaling):
    """ view used for generating (and storing) image scales """

    @view.memoize
    def _get_referenced(self):
        """Do an unrestricted lookup to ensure that we don't fail
        during traversal"""
        uid = getattr(self.context, 'collection_item')
        if not uid:
            return
        catalog = getToolByName(self.context, 'portal_catalog', None)
        if catalog is not None:
            brains = catalog.unrestrictedSearchResults(UID=uid)
            if brains:
                return brains[0]._unrestrictedGetObject()

    @view.memoize
    def _get_referenced_image_name(self, obj, name):
        # Choose the first image field from the referenced object schema
        if hasattr(obj, 'Schema'):
            schema = obj.Schema()
            if name in schema.keys():
                return name
            for field in schema.fields():
                if field.type == 'image':
                    name = field.__name__
                    break
            else:
                name = None
        return name

    def publishTraverse(self, request, name):
        """used for traversal via publisher, i.e. when using as a url"""
        scale = None
        stack = request.get('TraversalRequestNameStack')
        if stack:
            scale = stack[-1]
        try:
            return super(ExhibitItemScaling, self).publishTraverse(request,
                                                                   name)
        except (NotFound, AttributeError):
            obj = self._get_referenced()
            if obj is not None:
                # XXX: We assume the referenced object is either
                # Archetypes content or has an image field named
                # 'image'
                name = self._get_referenced_image_name(obj, name)
                if name:
                    if scale:
                        self._new_url = '%s/@@images/%s/%s'%(obj.absolute_url(),
                                                             name, scale)
                    else:
                        self._new_url = obj.absolute_url() + '/' + name
                    return self.redirector
            raise

    def traverse(self, name, furtherPath):
        """ used for path traversal, i.e. in zope page templates """
        morePath = furtherPath[:]
        try:
            image = super(ExhibitItemScaling, self).traverse(name, furtherPath)
        except (TraversalError, AttributeError):
            image = None

        if image is None:
            obj = self._get_referenced()
            if obj is not None:
                name = self._get_referenced_image_name(obj, name)
                image = obj.restrictedTraverse('@@images').traverse(name,
                                                                    morePath)
        return image

    def redirector(self, REQUEST=None):
        """Redirect to image url"""
        if getattr(self, '_new_url'):
            request = REQUEST or self.context.REQUEST
            request.response.redirect(self._new_url)
            return ''


class ExhibitItemContent(Item):
    """View providing default values for fields in view and for indexes"""

    def _get_referenced(self):
        uid = getattr(self, 'collection_item')
        if not uid:
            return
        obj = uuidToObject(uid)
        if not _checkPermission('View', obj):
            # Raise AttributeError if the current user cannot access
            # the referenced object.
            raise AttributeError, 'Referenced Object: %s not accessible'%uid
        return obj

    def _text_output(self, text_value, mimetype, raw=False):
        transformer = ITransformer(self)
        if mimetype is None and not raw:
            return text_value.output.encode(text_value.encoding)
        elif raw:
            return text_value.raw_encoded
        else:
            return transformer(text_value, mimetype).encode(text_value.encoding)

    @property
    def collection_item_url(self):
        """Returns the url of the referenced object"""
        ref = self._get_referenced()
        return ref and ref.absolute_url()

    def Title(self):
        """Returns the title of the object or referenced object"""
        title = self.title
        if not title:
            referenced = self._get_referenced()
            if referenced is not None:
                title = referenced.Title()
        else:
            title = title.encode('utf-8')
        return title

    def Description(self):
        """Returns the description of the object or referenced object"""
        desc = self.description
        if not desc:
            referenced = self._get_referenced()
            if referenced is not None:
                desc = referenced.Description()
        else:
            desc = desc.encode('utf-8')
        return desc

    def Subject(self):
        """Returns the description of the object or referenced object"""
        subject = self.subject
        if not subject:
            referenced = self._get_referenced()
            if referenced is not None:
                subject = referenced.Subject()
        else:
            subject = [s.encode('utf-8') for s in subject]
        return subject

    def getText(self, mimetype=None, raw=False, **kwargs):
        """Returns the transformed and encoded full text of the object
        or referenced object"""
        text = None
        transformed = None
        text_value = self.text
        if text_value:
            transformed = self._text_output(text_value, 'text/plain').strip()
            text = self._text_output(text_value, mimetype)
        if not text_value or not transformed:
            referenced = self._get_referenced()
            if referenced is not None and hasattr(referenced, 'getRawText'):
                text = referenced.getText(mimetype=mimetype, raw=raw, **kwargs)
            elif referenced is not None and hasattr(referenced, 'text'):
                text_value = referenced.text
                text = self._text_output(text_value, mimetype, raw)
        return text


class ExhibitItemNamer(grok.Adapter):
    grok.context(IExhibitItem)
    grok.provides(INameFromTitle)

    @property
    def title(self):
        """Use the DC title not the one stored on the instance which
        may be blank"""
        return self.context.Title()


@indexer(IExhibitItem)
def textIndexer(obj):
    return '%s\n%s\n%s'%(obj.getText(mimetype='text/plain'),
                         obj.Title(), obj.Description())
grok.global_adapter(textIndexer, name="SearchableText")

@indexer(IExhibitItem)
def sectionIndexer(obj):
    return aq_parent(aq_inner(obj)).Title()
grok.global_adapter(sectionIndexer, name="ExhibitSection")
