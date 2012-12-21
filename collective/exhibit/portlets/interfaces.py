from zope.schema import TextLine

from plone.portlets.interfaces import IPortletDataProvider
from Products.CMFPlone import PloneMessageFactory as _

class INavPortlet(IPortletDataProvider):
    """ Exhibit navigatrion allows custom css class on portlet """

    css_class = TextLine(
        title=_(u"CSS Class"),
        default=u"",
        required=False)
