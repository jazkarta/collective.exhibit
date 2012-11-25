from zope.interface import alsoProvides
from zope.event import notify
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.utils import _createObjectByType
from Products.ATContentTypes.lib import constraintypes

from collective.exhibit import exhibitMessageFactory as _
from config import EXHIBIT_TEMPLATES

try:
    from eea.facetednavigation.settings.interfaces import IHidePloneRightColumn
    from eea.facetednavigation.events import FacetedGlobalSettingsChangedEvent
    HAS_EEA = True
except ImportError:
    HAS_EEA = False


def configureExhibitsFolder(portal):
    folder = portal.restrictedTraverse('portal-exhibit-templates')
    folder.setExcludeFromNav(True)
    folder.reindexObject()


def exhibitSetup(context):
    if hasattr(context, 'getSite'):
        if context.readDataFile('collective-exhibit.txt') is None:
            return
        portal = context.getSite()
    else:
        portal = getToolByName(context, 'portal_url').getPortalObject()
    configureExhibitsFolder(portal)


def faceted_navigation(context):
    xmlconfig = context.readDataFile('exhibit_facets.xml')
    if xmlconfig is None or not HAS_EEA:
        return
    portal = context.getSite()
    qitool = getToolByName(portal, "portal_quickinstaller")

    if qitool.isProductInstallable('eea.facetednavigation'):
        if not qitool.isProductInstalled('eea.facetednavigation'):
            qitool.installProduct('eea.facetednavigation')

        folder = portal.restrictedTraverse(EXHIBIT_TEMPLATES)
        existing = folder.keys()
        if 'explore-exhibit' not in existing:
            _createObjectByType('Folder', folder, id='explore-exhibit',
                                title=_(u'Browse & Explore'))
            faceted = folder['explore-exhibit']
            alsoProvides(faceted, IHidePloneRightColumn)
            # We need to constrain types in order to allow an ATCT
            # folder inside a dexterity folder!
            faceted.setConstrainTypesMode(constraintypes.ENABLED)
            faceted.setLocallyAllowedTypes([])
            faceted.setImmediatelyAddableTypes([])
            # Enable faceted search view
            faceted.unrestrictedTraverse('@@faceted_subtyper/enable')()
            # Load default facet config/layout
            importer = faceted.unrestrictedTraverse('@@faceted_exportimport')
            importer.import_xml(import_file=xmlconfig, redirect=None)
            notify(FacetedGlobalSettingsChangedEvent(faceted))


def bibliography_faceted_navigation(context):
    xmlconfig = context.readDataFile('ex_bibliography_facets.xml')
    if xmlconfig is None or not HAS_EEA:
        return
    portal = context.getSite()
    qitool = getToolByName(portal, "portal_quickinstaller")

    if qitool.isProductInstallable('eea.facetednavigation'):
        if not qitool.isProductInstalled('eea.facetednavigation'):
            qitool.installProduct('eea.facetednavigation')

        folder = portal.restrictedTraverse(EXHIBIT_TEMPLATES)
        existing = folder.keys()
        if 'explore-bibliography' not in existing:
            _createObjectByType('Folder', folder, id='explore-bibliography',
                                title=_(u'Explore Bibliography'))
            faceted = folder['explore-bibliography']
            alsoProvides(faceted, IHidePloneRightColumn)
            # We need to constrain types in order to allow an ATCT
            # folder inside a dexterity folder!
            faceted.setConstrainTypesMode(constraintypes.ENABLED)
            faceted.setLocallyAllowedTypes([])
            faceted.setImmediatelyAddableTypes([])
            # Enable faceted search view
            faceted.unrestrictedTraverse('@@faceted_subtyper/enable')()
            # Load default facet config/layout
            importer = faceted.unrestrictedTraverse('@@faceted_exportimport')
            importer.import_xml(import_file=xmlconfig, redirect=None)
            notify(FacetedGlobalSettingsChangedEvent(faceted))
