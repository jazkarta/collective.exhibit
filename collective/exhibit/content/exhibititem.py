import itertools
from five import grok
from Acquisition import aq_inner, aq_parent
from zope import schema
from zope.interface import invariant, Invalid, alsoProvides
from zope.component import queryUtility
from zope.component import getUtility
from zope.publisher.interfaces import NotFound
from zope.traversing.interfaces import TraversalError

from plone.directives import form
from plone.supermodel.model import Schema
from plone.dexterity.interfaces import IDexterityFTI
from plone.dexterity.content import Item
from plone.dexterity.utils import getAdditionalSchemata
from plone.formwidget.contenttree import (UUIDSourceBinder,
                                          ContentTreeFieldWidget)
from plone.app.uuid.utils import uuidToObject
from plone.app.content.interfaces import INameFromTitle

from plone.app.textfield import RichText
from plone.app.textfield.interfaces import ITransformer
from plone.namedfile.interfaces import INamedImageField
from plone.namedfile.field import NamedImage
from plone.namedfile.scaling import ImageScaling
from plone.memoize import view
from plone.indexer import indexer
from Products.CMFCore.utils import getToolByName, _checkPermission

from plone.registry.interfaces import IRegistry
from collective.exhibit.interfaces import IExhibitSettings

from collective.exhibit import exhibitMessageFactory as _
from collective.z3cform.keywordwidget.field import Keywords
from plone.app.dexterity.behaviors.metadata import ICategorization
from plone.autoform.interfaces import IFormFieldProvider


class ExhibitUUIDSourceBinder(UUIDSourceBinder):

    def __call__(self, context):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IExhibitSettings)
        self.selectable_filter.criteria['portal_type'] = list(settings.exhibit_item_types)
        return super(ExhibitUUIDSourceBinder, self).__call__(context)

class MustHaveTitle(Invalid):
    __doc__ = _(u'If there is no referenced item, you must set the title.')

class MustHaveImage(Invalid):
    __doc__ = _(u'If the referenced item does not have an image field, '
                'you must upload an image.')


class IExhibitItem(Schema):
    """An Exhibit Item.  Often a reference to another object in
    the site."""

    referenced_item = schema.Choice(title=_(u'Referenced Item'),
                                    description = _(u'Chose an existing '
                                                    'content item from the '
                                                    'site'),
                                    source=ExhibitUUIDSourceBinder(),
                                    required=False,
                                    )
    form.widget(referenced_item=ContentTreeFieldWidget)
    form.primary('referenced_item')

    title = schema.TextLine(
        title = _(u'Title'),
        description = _(u'Leave this blank to use the title '
                        'from the referenced item.  You must set the '
                        'title if you do not choose a referenced item.'),
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
                                       'primary image from the referenced '
                                       'item.  You must upload an image if '
                                       'the referenced item has no image '
                                       'field.'),
                       required=False,
                       )

    show_image = schema.Bool(title=_(u'Show image in default view'),
                             default=True)

    text = RichText(title=_(u'Description'),
                    description=_(u'Describe the exhibit item.  Leave '
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

    @invariant
    def validateHasTitle(data):
        """Verifies that there is a title, either from the referenced
        item or explicitly set"""
        if not data.referenced_item:
            if not data.title:
                raise MustHaveTitle(_(u'You must either choose a Referenced '
                                      'Item or set a Title.'))

    @invariant
    def validateHasImage(data):
        """Verifies that either the referenced object has an image or
        an image has been explicitly set"""
        if data.image is None:
            if data.referenced_item:
                obj = uuidToObject(data.referenced_item)
                image_name = _get_image_field_name(obj)
                if image_name is None:
                    raise MustHaveImage(_(u'The Referenced Item does not have '
                                          'an image.  Either upload an '
                                          'Image, or choose a referenced item '
                                          'with an image field.'))
            else:
                raise MustHaveImage(_(u"You must either choose a Referenced "
                                      "Item or upload an Image."))

class IKeywordCategorization(ICategorization):
    # Override Subjects
    subjects = Keywords(title = _(u'label_categories',
                                      default=u'Categories'),
                    description = _(u'help_categories',
                                    default=u'Also known as keywords, '
                                    'tags or labels, these help you '
                                    'categorize your content.'),
                    required = False,
                    index_name='Subject',
        )
    form.widget(subjects='collective.z3cform.keywordwidget.widget.KeywordFieldWidget')

alsoProvides(IKeywordCategorization, IFormFieldProvider)

def _get_image_field_name(obj, default_name='image'):
    """Try to find an image field on an object, if there's a field
    with the requested default name, use it."""
    if hasattr(obj, 'Schema'):
        schema = obj.Schema()
        if default_name in schema.keys():
            return default_name
        for field in schema.fields():
            if field.type == 'image':
                return field.__name__
    else:
        fti = queryUtility(IDexterityFTI, name=obj.portal_type)
        if fti:
            schema = fti.lookupSchema()
            additional = getAdditionalSchemata(context=obj,
                                               portal_type=obj.portal_type)
            for schemata in itertools.chain([schema], additional):
                names = schemata.names()
                if default_name in names:
                    return default_name
                for fname in schemata.names():
                    if INamedImageField.providedBy(schemata.get(fname)):
                        return fname
    return None

class ExhibitItemScaling(ImageScaling):
    """ view used for generating (and storing) image scales """

    @view.memoize
    def _get_referenced(self):
        """Do an unrestricted lookup to ensure that we don't fail
        during traversal"""
        uid = getattr(self.context, 'referenced_item')
        if not uid:
            return
        catalog = getToolByName(self.context, 'portal_catalog', None)
        if catalog is not None:
            brains = catalog.unrestrictedSearchResults(UID=uid)
            if brains:
                return brains[0]._unrestrictedGetObject()

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
                name = _get_image_field_name(obj, name)
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
                name = _get_image_field_name(obj, name)
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
        uid = getattr(self, 'referenced_item')
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
    def referenced_item_url(self):
        """Returns the url of the referenced object"""
        ref = self._get_referenced()
        return ref and ref.absolute_url()

    def Title(self):
        """Returns the title of the object or referenced object"""
        title = self.title
        if not title:
            try:
                referenced = self._get_referenced()
            except AttributeError:
                return None
            if referenced is not None:
                title = referenced.Title()
            else:
                title = ''
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
                desc = ''
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
                subject = []
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
