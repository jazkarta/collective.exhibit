from zope.component import getUtility
from zope.interface import implementer
from z3c.form import widget
from z3c.form.interfaces import IFieldWidget
from Products.Five.browser import BrowserView
from Acquisition import aq_chain, aq_inner
from collective.exhibit.content.exhibit import IExhibit
from plone.app.layout.viewlets.common import ViewletBase
from plone.app.z3cform.widget import RelatedItemsWidget
from plone.registry.interfaces import IRegistry
from collective.exhibit.interfaces import IExhibitSettings
from collective.exhibit.config import EXHIBIT_STYLESHEETS


class IsExhibitContent(BrowserView):
    """Helper view to determine if the current content is in an exhibit"""

    def __call__(self):
        """Returns true if there's an exhibit in the acquisition chain
        of the context"""
        context = self.context
        parents = aq_chain(aq_inner(context))
        for item in parents:
            if IExhibit.providedBy(item):
                return True
        return False


class ExhibitCSSViewlet(ViewletBase):
    """Custom viewlet for injecting exhibit specific css into page layout"""
    css = None

    def update(self):
        super(ExhibitCSSViewlet, self).update()
        if self.context.restrictedTraverse('@@is-exhibit')():
            css_id = self.context.unrestrictedTraverse('stylesheet', None)
            if css_id:
                self.css = '%s/%s/%s'%(self.site_url, EXHIBIT_STYLESHEETS,
                                       css_id)

    def render(self):
        if self.css is not None:
            return '<link rel="stylesheet" type="text/css" href="%s"></link>'%(
                self.css)
        return ''


class ExhibitRelatedWidget(RelatedItemsWidget):
    """
    This is a related items widget that allows sets the root path to the
    current archive.
    """
    def _base_args(self):
        args = super(ExhibitRelatedWidget, self)._base_args()
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IExhibitSettings)
        if getattr(settings, 'exhibit_item_types', None):
            args.setdefault('pattern_options', {})['selectableTypes'] = list(
                settings.exhibit_item_types
            )
        return args


@implementer(IFieldWidget)
def ExhibitRelatedFieldWidget(field, request, extra=None):
    return widget.FieldWidget(field, ExhibitRelatedWidget(request))
