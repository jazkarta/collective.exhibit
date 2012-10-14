from Acquisition import aq_base
import unittest2 as unittest

from zope.component import createObject
from zope.component import queryUtility, queryMultiAdapter
from zope.event import notify
from zope.lifecycleevent import ObjectModifiedEvent

from plone.dexterity.interfaces import IDexterityFTI
from plone.behavior.interfaces import IBehaviorAssignable
from plone.portlets.interfaces import IPortletManager
from plone.portlets.interfaces import IPortletAssignmentMapping
from plone.portlets.interfaces import ILocalPortletAssignmentManager
from plone.portlets.constants import (USER_CATEGORY, GROUP_CATEGORY,
                                      CONTENT_TYPE_CATEGORY, CONTEXT_CATEGORY)

from collective.exhibit.testing import COLLECTIVE_EXHIBIT_INTEGRATION_TESTING
from collective.exhibit.content.exhibit import IInitialSections
from collective.exhibit.portlets import navigation

from plone.app.testing import TEST_USER_ID, setRoles


class ExhibitTest(unittest.TestCase):

    layer = COLLECTIVE_EXHIBIT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def _createOne(self, **kw):
        self.portal.invokeFactory('collective.exhibit.exhibit', 'exhibit-a',
                                  **kw)
        return self.portal['exhibit-a']

    def test_schema(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibit')
        schema = fti.lookupSchema()
        self.assertEquals(schema.__module__,
                          'collective.exhibit.content.exhibit')
        self.assertEquals(schema.__name__,
                          'IExhibit')

    def test_fti(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibit')

        self.assertNotEquals(None, fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibit')
        factory = fti.factory
        exhibit = createObject(factory)

        self.assertEquals(str(type(exhibit)),
                          "<class 'plone.dexterity.content.Container'>")

    def test_adding(self):
        exhibit = self._createOne()
        self.assertEquals(str(type(aq_base(exhibit))),
                          "<class 'plone.dexterity.content.Container'>")

    def test_view(self):
        exhibit = self._createOne()
        self.request.set('URL', exhibit.absolute_url())
        self.request.set('ACTUAL_URL', exhibit.absolute_url())
        view = exhibit.restrictedTraverse('@@view')

        self.failUnless(view())
        self.assertEquals(view.request.response.status, 200)

    def test_copy_templates_on_add(self):
        # Choose two pages to copy from central repository
        exhibit = self._createOne(pages=['introduction', 'acknowledgements'])
        self.assertEquals(exhibit.objectIds(),
                          ['introduction', 'acknowledgements'])
        self.assertEquals(exhibit.introduction.getPortalTypeName(), 'Document')

    def test_copy_templates_on_edit(self):
        # Choose two pages to copy from central repository
        exhibit = self._createOne()
        self.assertEquals(len(exhibit.objectIds()), 0)
        exhibit.pages = ['introduction', 'acknowledgements']
        notify(ObjectModifiedEvent(exhibit))
        self.assertEquals(exhibit.objectIds(),
                          ['introduction', 'acknowledgements'])
        self.assertEquals(exhibit.introduction.getPortalTypeName(), 'Document')

    def test_exhibit_provides_section_creation_behavior(self):
        # Choose two pages to copy from central repository
        exhibit = self._createOne()
        self.assertTrue(
            IBehaviorAssignable(exhibit, None).supports(IInitialSections)
            )

    def test_create_sections_on_edit(self):
        exhibit = self._createOne()
        section_adapter = IInitialSections(exhibit)
        section_adapter.sections =  ['Section One', 'Section Two']
        self.assertEquals(section_adapter.sections,
                          ['Section One', 'Section Two'])
        notify(ObjectModifiedEvent(exhibit))
        self.assertEquals(exhibit.objectIds(),
                          ['section-one', 'section-two'])
        section_one = exhibit['section-one']
        self.assertEquals(section_one.getPortalTypeName(),
                          'collective.exhibit.exhibitsection')
        self.assertEquals(section_one.Title(),
                          'Section One')

    def test_create_sections_on_add(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibit')
        factory = fti.factory
        exhibit = createObject(factory)
        IInitialSections(exhibit).sections =  ['Section One', 'Section Two']
        exhibit.id = 'exhibit-a'
        exhibit.title = 'Exhibit A'
        self.portal['exhibit-a'] = exhibit
        self.assertEquals(exhibit.objectIds(),
                          ['section-one', 'section-two'])
        section_one = exhibit['section-one']
        self.assertEquals(section_one.getPortalTypeName(),
                          'collective.exhibit.exhibitsection')
        self.assertEquals(section_one.Title(),
                          'Section One')

    def test_configure_portlet_on_add(self):
        exhibit = self._createOne()
        manager = queryUtility(IPortletManager, name='plone.leftcolumn',
                               context=exhibit)
        mapping = queryMultiAdapter((exhibit, manager),
                                    IPortletAssignmentMapping)
        # Correct portlet is assigned in the left column
        self.assertIn('exhibit_navigation_portlet', mapping)
        self.assertIs(mapping['exhibit_navigation_portlet'].__class__,
                          navigation.Assignment)
        blacklist = queryMultiAdapter((exhibit, manager),
                                    ILocalPortletAssignmentManager)
        # All inherited portlets are explicitly blocked in the column
        for category in (GROUP_CATEGORY, CONTENT_TYPE_CATEGORY,
                         CONTEXT_CATEGORY, USER_CATEGORY):
            self.assertEquals(blacklist.getBlacklistStatus(category), True)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
