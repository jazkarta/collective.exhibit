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
        self.portal.invokeFactory('collective.exhibit.exhibit',
                                  'exhibit-a')
        exhibit = self.portal['exhibit-a']

        self.assertEquals(str(type(aq_base(exhibit))),
                          "<class 'plone.dexterity.content.Container'>")

    def test_view(self):
        self.portal.invokeFactory('collective.exhibit.exhibit', 'exhibit-a')
        exhibit = self.portal['exhibit-a']
        self.request.set('URL', exhibit.absolute_url())
        self.request.set('ACTUAL_URL', exhibit.absolute_url())
        view = exhibit.restrictedTraverse('@@view')

        self.failUnless(view())
        self.assertEquals(view.request.response.status, 200)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
