from zope.interface import implements
from Acquisition import aq_inner, aq_parent

from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from plone.app.portlets.portlets import base
from plone.memoize.instance import memoize
from Products.CMFPlone import PloneMessageFactory as _

from collective.exhibit.portlets.interfaces import INavPortlet
from collective.exhibit.content.exhibit import IExhibit


class Assignment(base.Assignment):
    implements(INavPortlet)

    @property
    def title(self):
        return _(u"Exhibit Navigation")


class AddForm(base.NullAddForm):

    def create(self):
        return Assignment()


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

    @memoize
    def _data(self):
        sections = self.exhibit.listFolderContents()
        return {'exhibit': self.exhibit, 'sections': sections}
