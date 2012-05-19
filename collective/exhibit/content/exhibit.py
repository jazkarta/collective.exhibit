from five import grok
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.interfaces import IContextSourceBinder
from z3c.form import field
from z3c.form import interfaces
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope.app.container.interfaces import IObjectAddedEvent

from Products.CMFCore.utils import getToolByName
from plone.z3cform.textlines import TextLinesFieldWidget
from plone.directives import form, dexterity
from plone.app.textfield import RichText
from plone.dexterity.utils import createContentInContainer
from plone.namedfile.field import NamedBlobImage

from collective.exhibit.config import EXHIBIT_TEMPLATES
from collective.exhibit import exhibitMessageFactory as _


@grok.provider(IContextSourceBinder)
def exhibit_pages(context):
    pages = []
    portal_url = getToolByName(context, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.restrictedTraverse(EXHIBIT_TEMPLATES)
    for page in exhibit_templates.listFolderContents():
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

    pages = schema.Set(title=_(u'Exhibit Pages'),
                       required=False,
                       description=u'Select any pages from the global site templates that you want to be included on the exhibit.',
                       value_type=schema.Choice(source=exhibit_pages))
    form.widget(pages=CheckBoxFieldWidget)

    sections = schema.Set(title=_(u'Exhibit Sections'),
                          required=False,
                          description=u'Add the titles of any sections that you wish to add to the exhibit, one per line.',
                          value_type=schema.ASCIILine())
    form.omitted('pages', 'sections')
    form.no_omit(interfaces.IAddForm, 'pages')
    form.no_omit(interfaces.IAddForm, 'sections')


class AddForm(dexterity.AddForm):
    grok.name('collective.exhibit.exhibit')

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets['sections'].rows = 10


@grok.subscribe(IExhibit, IObjectAddedEvent)
def createExhibitContent(exhibit, event):
    for section in exhibit.sections:
        createContentInContainer(exhibit, 'collective.exhibit.exhibitsection',
                                 title=section)

    portal_url = getToolByName(exhibit, 'portal_url')
    site = portal_url.getPortalObject()
    exhibit_templates = site.restrictedTraverse(EXHIBIT_TEMPLATES)
    page_ids = [page for page in exhibit.pages]
    pages = exhibit_templates.manage_copyObjects(ids=page_ids)
    exhibit.manage_pasteObjects(pages)
