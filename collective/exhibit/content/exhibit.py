from five import grok
from zope import schema
from zope.component import getUtility, getMultiAdapter
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IContextSourceBinder
from z3c.form import interfaces
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope.app.container.interfaces import IObjectAddedEvent
from zope.lifecycleevent.interfaces import IObjectModifiedEvent

from Products.CMFCore.utils import getToolByName
from plone.directives import form, dexterity
from plone.app.textfield import RichText
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.field import NamedBlobImage
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.constants import USER_CATEGORY
from plone.portlets.constants import GROUP_CATEGORY
from plone.portlets.constants import CONTENT_TYPE_CATEGORY
from plone.portlets.constants import CONTEXT_CATEGORY

from collective.exhibit.config import EXHIBIT_TEMPLATES
from collective.exhibit import exhibitMessageFactory as _


@grok.provider(IContextSourceBinder)
def exhibit_pages(context):
    pages = []
    portal_url = getToolByName(context, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.restrictedTraverse(EXHIBIT_TEMPLATES)
    for page in exhibit_templates.listFolderContents():
        if page.getId() not in context.objectIds():
            term = SimpleVocabulary.createTerm(page.getId(),
                                               str(page.getId()),
                                               page.Title)
            pages.append(term)
    return SimpleVocabulary(pages)


class IExhibit(form.Schema):
    """An Exhibit"""

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

    pages = schema.List(title=_(u'Exhibit Pages'),
                       required=False,
                       description=u'Select any pages from the global site templates that you want to be included on the exhibit.',
                       value_type=schema.Choice(source=exhibit_pages))
    form.widget(pages=CheckBoxFieldWidget)

    sections = schema.List(title=_(u'Exhibit Sections'),
                          required=False,
                          description=u'Add the titles of any sections that you wish to add to the exhibit, one per line.',
                          value_type=schema.ASCIILine())
    form.omitted('sections')
    form.no_omit(interfaces.IAddForm, 'sections')


class AddForm(dexterity.AddForm):
    grok.name('collective.exhibit.exhibit')

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets['sections'].rows = 10


@grok.subscribe(IExhibit, IObjectAddedEvent)
def createExhibitContent(exhibit, event):
    from collective.exhibit.portlets.navigation import Assignment
    if exhibit.sections:
        for section in exhibit.sections:
            createContentInContainer(exhibit, 'collective.exhibit.exhibitsection',
                                 title=section)

    portal_url = getToolByName(exhibit, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.restrictedTraverse(EXHIBIT_TEMPLATES)
    page_ids = [page for page in exhibit.pages]
    pages = exhibit_templates.manage_copyObjects(ids=page_ids)
    exhibit.manage_pasteObjects(pages)

    manager = getUtility(IPortletManager, name='plone.leftcolumn', context=exhibit)
    mapping = getMultiAdapter((exhibit, manager), IPortletAssignmentMapping)
    assignment = Assignment()
    mapping['exhibit_navigation_portlet'] = assignment
    blacklist = getMultiAdapter((exhibit, manager), ILocalPortletAssignmentManager)
    for category in (GROUP_CATEGORY, CONTENT_TYPE_CATEGORY,CONTEXT_CATEGORY,USER_CATEGORY):
        blacklist.setBlacklistStatus(category, 1)


@grok.subscribe(IExhibit, IObjectModifiedEvent)
def editExhibitContent(exhibit, event):
    portal_url = getToolByName(exhibit, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.restrictedTraverse(EXHIBIT_TEMPLATES)
    contents = exhibit.objectIds()
    add_page_ids = [page for page in exhibit.pages if page not in contents]
    pages = exhibit_templates.manage_copyObjects(ids=add_page_ids)
    exhibit.manage_pasteObjects(pages)
