from Products.CMFCore.utils import getToolByName

from collective.exhibit import exhibitMessageFactory as _


def configureExhibitsFolder(portal):
    folder = portal.restrictedTraverse('portal-exhibit-templates')
    folder.setExcludeFromNav(True)


def exhibitSetup(context):
    if hasattr(context, 'getSite'):
        if context.readDataFile('collective-exhibit.txt') is None:
            return
        portal = context.getSite()
    else:
        portal = getToolByName(context, 'portal_url').getPortalObject()
    configureExhibitsFolder(portal)
