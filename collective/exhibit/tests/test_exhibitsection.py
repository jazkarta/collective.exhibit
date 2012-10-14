from Acquisition import aq_base
import unittest2 as unittest

from zope.component import createObject
from zope.component import queryUtility

from plone.dexterity.interfaces import IDexterityFTI

from collective.exhibit.testing import COLLECTIVE_EXHIBIT_INTEGRATION_TESTING

from plone.app.testing import TEST_USER_ID, setRoles


class ExhibitTest(unittest.TestCase):

    layer = COLLECTIVE_EXHIBIT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_schema(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibitsection')
        schema = fti.lookupSchema()
        self.assertEquals(schema.__module__,
                          'collective.exhibit.content.exhibitsection')
        self.assertEquals(schema.__name__,
                          'IExhibitSection')

    def test_fti(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibitsection')

        self.assertNotEquals(None, fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibitsection')
        factory = fti.factory
        section = createObject(factory)

        self.assertEquals(str(type(section)),
                          "<class 'plone.dexterity.content.Container'>")

    def test_adding_alone(self):
        self.portal.invokeFactory('collective.exhibit.exhibitsection',
                                  'section-a')
        section = self.portal['section-a']

        self.assertEquals(str(type(aq_base(section))),
                          "<class 'plone.dexterity.content.Container'>")

    def test_adding_to_exhibit(self):
        self.portal.invokeFactory('collective.exhibit.exhibit',
                                  'exhibit-a')
        exhibit = self.portal['exhibit-a']
        exhibit.invokeFactory('collective.exhibit.exhibitsection',
                              'section-a')
        section = exhibit['section-a']

        self.assertEquals(str(type(aq_base(section))),
                          "<class 'plone.dexterity.content.Container'>")

    def test_view(self):
        self.portal.invokeFactory('collective.exhibit.exhibitsection',
                                  'section-a')
        section = self.portal['section-a']
        self.request.set('URL', section.absolute_url())
        self.request.set('ACTUAL_URL', section.absolute_url())
        view = section.restrictedTraverse('@@view')

        self.failUnless(view())
        self.assertEquals(view.request.response.status, 200)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
