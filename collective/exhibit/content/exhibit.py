from five import grok
from zope import schema
from zope.interface import implements, alsoProvides
from zope.component import getUtility, getMultiAdapter, adapts
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IContextSourceBinder
from z3c.form import interfaces
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope.app.container.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent
from zope.container.interfaces import IContainerModifiedEvent

from Products.CMFCore.utils import getToolByName
from plone.directives import form
from plone.supermodel.model import Schema
from plone.app.textfield import RichText
from plone.app.textfield.value import RichTextValue
from plone.dexterity.utils import createContentInContainer
from plone.behavior.interfaces import IBehaviorAssignable
from plone.dexterity.interfaces import IDexterityContent
from plone.namedfile.field import NamedBlobImage
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.constants import GROUP_CATEGORY
from plone.portlets.constants import CONTENT_TYPE_CATEGORY
from plone.portlets.constants import CONTEXT_CATEGORY

from collective.exhibit.config import EXHIBIT_TEMPLATES
from collective.exhibit.config import EXHIBIT_STYLESHEETS
from collective.exhibit.config import EXHIBIT_HOMEPAGES
from collective.exhibit import exhibitMessageFactory as _


@grok.provider(IContextSourceBinder)
def exhibit_pages(context):
    pages = []
    portal_url = getToolByName(context, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.unrestrictedTraverse(EXHIBIT_TEMPLATES)
    for page in exhibit_templates.listFolderContents():
        if page.getId() not in context.objectIds():
            term = SimpleVocabulary.createTerm(page.getId(),
                                               str(page.getId()),
                                               page.Title())
            pages.append(term)
    return SimpleVocabulary(pages)


@grok.provider(IContextSourceBinder)
def exhibit_homepages(context):
    pages = []
    portal_url = getToolByName(context, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.unrestrictedTraverse(EXHIBIT_HOMEPAGES)
    for page in exhibit_templates.listFolderContents():
        if page.getId() not in context.objectIds():
            term = SimpleVocabulary.createTerm(page.getId(),
                                               str(page.getId()),
                                               page.Title())
            pages.append(term)
    return SimpleVocabulary(pages)


@grok.provider(IContextSourceBinder)
def exhibit_stylesheets(context):
    pages = []
    portal_url = getToolByName(context, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_stylesheets = site.unrestrictedTraverse(EXHIBIT_STYLESHEETS)
    for page in exhibit_stylesheets.listFolderContents():
        if page.getId() not in context.objectIds():
            term = SimpleVocabulary.createTerm(page.getId(),
                                               str(page.getId()),
                                               page.Title())
            pages.append(term)
    return SimpleVocabulary(pages)


@grok.provider(IContextSourceBinder)
def bibliography_types(context):
    types = []
    portal_bibliography = getToolByName(context, 'portal_bibliography')
    bib_types = portal_bibliography.getReferenceTypes()
    for rtype in bib_types:
        term = SimpleVocabulary.createTerm(rtype, rtype, rtype)
        types.append(term)
    return SimpleVocabulary(types)


class IExhibit(Schema):
    """An Exhibit"""

    homepage = schema.Choice(title=_(u'Template Text'),
                       required=False,
                       description=u'Select a template to use for the default text or leave blank to enter custom text below',
                       source=exhibit_homepages)
    form.omitted('homepage')
    form.no_omit(interfaces.IAddForm, 'homepage')

    text = RichText(title=_(u'Text'),
                    required=False,
                    allowed_mime_types=('text/html',),
                    default_mime_type='text/html',
                    output_mime_type='text/x-html-safe',
                    default=u'',
                    )
    form.primary('text')

    image = NamedBlobImage(title=_(u'Image'),
                           required=False)

    stylesheet = schema.Choice(title=_(u'Exhibit Stylesheet'),
                       required=False,
                       description=u'Select an stylesheet from the global site stylesheets.)',
                       source=exhibit_stylesheets)

    pages = schema.List(title=_(u'Exhibit Pages'),
                       required=False,
                       description=u'Select any pages from the global site templates that you want to be included on the exhibit. (If this list is blank, it means that you have already added all of the global site templates.)',
                       value_type=schema.Choice(source=exhibit_pages))
    form.widget(pages=CheckBoxFieldWidget)


class IInitialSections(Schema):
    sections = schema.List(title=_(u'Exhibit Sections'),
                          required=True,
                          description=u'Add the titles of any sections that you wish to add to the exhibit, one per line. You must add at least one section.',
                          value_type=schema.TextLine())

    form.omitted('sections')
    form.no_omit(interfaces.IAddForm, 'sections')

alsoProvides(IInitialSections, form.IFormFieldProvider)


class InitialSections(object):
    implements(IInitialSections)
    adapts(IExhibit)

    def __init__(self, context):
        self.context = context
        self.context._v_sections = []

    def _get_items(self):
        return self.context._v_sections

    def _set_items(self, values):
        self.context._v_sections = values or []

    sections = property(_get_items, _set_items)


@grok.subscribe(IExhibit, IObjectAddedEvent)
def createExhibitContent(exhibit, event):
    from collective.exhibit.portlets.navigation import Assignment
    portal_url = getToolByName(exhibit, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.unrestrictedTraverse(EXHIBIT_TEMPLATES)
    page_ids = [page for page in (exhibit.pages or [])]
    pages = exhibit_templates.manage_copyObjects(ids=page_ids)
    exhibit.manage_pasteObjects(pages)

    manager = getUtility(IPortletManager, name='plone.leftcolumn', context=exhibit)
    mapping = getMultiAdapter((exhibit, manager), IPortletAssignmentMapping)
    assignment = Assignment()
    mapping['exhibit_navigation_portlet'] = assignment
    blacklist = getMultiAdapter((exhibit, manager), ILocalPortletAssignmentManager)
    for category in (GROUP_CATEGORY, CONTENT_TYPE_CATEGORY, CONTEXT_CATEGORY, USER_CATEGORY):
        blacklist.setBlacklistStatus(category, 1)

    # Homepage text
    homepage_id = getattr(exhibit, 'homepage', None)
    if homepage_id is not None:
        homepage_templates = site.unrestrictedTraverse(EXHIBIT_HOMEPAGES)
        homepage = homepage_templates[homepage_id]
        exhibit.text = RichTextValue(unicode(homepage.getText(), 'utf8'),
                                     'text/html', 'text/html')


@grok.subscribe(IExhibit, IObjectModifiedEvent)
def editExhibitContent(exhibit, event):
    # Don't call again when items are added to avoid recursion
    if IContainerModifiedEvent.providedBy(event):
        return
    portal_url = getToolByName(exhibit, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.unrestrictedTraverse(EXHIBIT_TEMPLATES)
    contents = exhibit.objectIds()
    add_page_ids = [page for page in (exhibit.pages or [])
                    if page not in contents]
    pages = exhibit_templates.manage_copyObjects(ids=add_page_ids)
    exhibit.manage_pasteObjects(pages)


@grok.subscribe(IDexterityContent, IObjectAddedEvent)
@grok.subscribe(IDexterityContent, IObjectModifiedEvent)
def addExhibitSections(obj, event):
    # Don't call again when items are added to avoid recursion, and
    # only call on items with assigned behavior
    if (IContainerModifiedEvent.providedBy(event) or
        not IBehaviorAssignable(obj, None).supports(IInitialSections)):
        return
    exhibit_sections = getattr(obj, '_v_sections', [])
    for section in exhibit_sections:
        section = section.strip()
        if section:
            createContentInContainer(obj,
                                     'collective.exhibit.exhibitsection',
                                     title=section)
