from zope.interface import implements
from zope.component import getMultiAdapter
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

    @property
    def title(self):
        return _(u"Exhibit Navigation")


class AddForm(base.AddForm):
    form_fields = form.Fields(INavPortlet)
    label = _(u"Add Exhibit Navigation Portlet")
    description = _(u"This portlet displays the pages and sections of an exhibit.")

    def create(self, data):
        return Assignment()


class Renderer(base.Renderer):
    _template = ViewPageTemplateFile('navigation.pt')

    def __init__(self, *args):
        base.Renderer.__init__(self, *args)

        context = aq_inner(self.context)
        portal_state = getMultiAdapter((context, self.request), name=u'plone_portal_state')
        self.portal_url = portal_state.portal_url()  # the URL of the portal object

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
        return len(self._data()['pages']) + len(self._data()['sections'])

    def exhibit_contents(self):
        return self._data()

    @memoize
    def _data(self):
        if 'explore-exhibit' in self.exhibit.pages:
            browse_url = '%s/explore-exhibit' % self.portal_url
        else:
            browse_url = None
        sections = self.exhibit.listFolderContents({'portal_type': 'collective.exhibit.exhibitsection'})
        pages = []
        for page_id in self.exhibit.pages:
            # this needs to be located separately so it's handled by browse_url
            if page_id == 'explore-exhibit':
                continue
            page = self.exhibit.restrictedTraverse(page_id)
            pages.append(page)
        return {'exhibit_title': self.exhibit.Title(),
                'exhibit_url': self.exhibit.absolute_url(),
                'pages': pages,
                'sections': sections,
                'browse_url': browse_url,
               }
