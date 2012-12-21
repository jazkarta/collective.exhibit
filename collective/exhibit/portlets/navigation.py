from zope.interface import implements
from zope.formlib import form
from Acquisition import aq_inner, aq_parent

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.portlets.portlets import base
from plone.memoize.instance import memoize
from Products.CMFPlone import PloneMessageFactory as _

from collective.exhibit.portlets.interfaces import INavPortlet
from collective.exhibit.content.exhibit import IExhibit


class Assignment(base.Assignment):
    implements(INavPortlet)

    css_class=u''

    @property
    def title(self):
        return _(u"Exhibit Navigation")


class AddForm(base.AddForm):
    form_fields = form.Fields(INavPortlet)
    label = _(u"Add Navigation Portlet")
    description = _(u"This portlet displays exhibit navigation.")

    def create(self, data):
        return Assignment(css_class=data.get('css_class', u''))


class EditForm(base.EditForm):
    form_fields = form.Fields(INavPortlet)
    label = _(u"Add Navigation Portlet")
    description = _(u"This portlet displays exhibit navigation.")


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('navigation.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        context = aq_inner(self.context)
        exhibit = None
        while exhibit is None:
            if IExhibit.providedBy(context):
                exhibit = context
            context = aq_parent(context)
        self.exhibit = exhibit

    def render(self):
        return self._template()

    @property
    def available(self):
        """Show the portlet only if there are one or more elements."""
        return len(self._data()['sections'])

    def exhibit_contents(self):
        return self._data()

    def css_class(self):
        return (self.data.css_class or u'').encode('utf8')

    @memoize
    def _data(self):
        sections = self.exhibit.listFolderContents()
        return {'exhibit': self.exhibit, 'sections': sections}
