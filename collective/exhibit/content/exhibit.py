from five import grok
from zope import schema
from zope.schema.vocabulary import SimpleVocabulary
from zope.schema.vocabulary import SimpleTerm
from z3c.form import field
from z3c.form import interfaces
from z3c.form.browser.checkbox import CheckBoxFieldWidget
from zope.app.container.interfaces import IObjectAddedEvent

from plone.z3cform.textlines import TextLinesFieldWidget
from plone.directives import form, dexterity
from plone.app.textfield import RichText
from plone.dexterity.utils import createContentInContainer

from collective.exhibit import exhibitMessageFactory as _


exhibit_pages = SimpleVocabulary(
    [SimpleTerm(value=u'introduction:Introduction', title=_(u'Introduction')),
     SimpleTerm(value=u'about:About this exhibit', title=_(u'About this exhibit')),
     SimpleTerm(value=u'acknowlegements:Acknowledgements', title=_(u'Acknowledgements')),
     SimpleTerm(value=u'browse:Browse all items', title=_(u'Browse all items')),
     SimpleTerm(value=u'timeline:Timeline', title=_(u'Timeline'))]
    )


class IExhibit(form.Schema):
    """An Exhibit"""

    text = RichText(title=_(u'Text'),
                    required=False,
                    allowed_mime_types=('text/html',),
                    default_mime_type='text/html',
                    output_mime_type='text/x-html-safe',
                    default=u'',
                    )

    pages = schema.Set(title=_(u'Exhibit Pages'),
                       required=False,
                       value_type=schema.Choice(vocabulary=exhibit_pages))

    sections = schema.Set(title=_(u'Exhibit Sections'),
                          required=False,
                          value_type=schema.ASCIILine())


class AddForm(dexterity.AddForm):
    grok.name('collective.exhibit.exhibit')

    fields = field.Fields(IExhibit)
    fields['pages'].widgetFactory = CheckBoxFieldWidget

    def updateWidgets(self):
        super(AddForm, self).updateWidgets()
        self.widgets['sections'].rows = 10


class EditForm(dexterity.EditForm):
    grok.context(IExhibit)

    fields = field.Fields(IExhibit)

    def updateWidgets(self):
        super(EditForm, self).updateWidgets()
        self.widgets['pages'].mode = interfaces.HIDDEN_MODE
        self.widgets['sections'].mode = interfaces.DISPLAY_MODE


@grok.subscribe(IExhibit, IObjectAddedEvent)
def createExhibitContent(exhibit, event):
    for section in exhibit.sections:
        createContentInContainer(exhibit, 'collective.exhibit.exhibitsection',
                                 title=section)
    for page in exhibit.pages:
        page_id, page_title = page.split(':', 1)
        exhibit.invokeFactory('Document', page_id, title=page_title)
        
