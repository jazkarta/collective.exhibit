from Acquisition import aq_base
import unittest2 as unittest

from zope.component import createObject
from zope.component import queryUtility

from plone.dexterity.interfaces import IDexterityFTI
from plone.uuid.interfaces import IUUID

from collective.exhibit.testing import COLLECTIVE_EXHIBIT_INTEGRATION_TESTING

from plone.app.testing import TEST_USER_ID, setRoles


class ExhibitTest(unittest.TestCase):

    layer = COLLECTIVE_EXHIBIT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def _setup_item_with_reference(self):
        self.portal.invokeFactory('collective.exhibit.exhibitsection',
                                  'section-a')
        section = self.portal['section-a']
        section.invokeFactory('collective.exhibit.exhibititem',
                                  'item-a')
        item = section['item-a']
        # create item for reference
        self.portal.invokeFactory('News Item', 'some-news', title='Some News',
                                  description='Original Description',
                                  text='<p>Original Text</p>',
                                  subject=['Original', 'Keywords'])
        referenced = self.portal['some-news']
        item.referenced_item = IUUID(referenced)
        return item, referenced

    def test_schema(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibititem')
        schema = fti.lookupSchema()
        self.assertEquals(schema.__module__,
                          'collective.exhibit.content.exhibititem')
        self.assertEquals(schema.__name__,
                          'IExhibitItem')

    def test_fti(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibititem')

        self.assertNotEquals(None, fti)

    def test_factory(self):
        fti = queryUtility(IDexterityFTI,
                           name='collective.exhibit.exhibititem')
        factory = fti.factory
        item = createObject(factory)

        self.assertEquals(str(type(item)),
                          "<class 'collective.exhibit.content.exhibititem.ExhibitItemContent'>")

    def test_adding_alone(self):
        self.assertRaises(ValueError, self.portal.invokeFactory,
                          'collective.exhibit.exhibititem', 'item-a')

    def test_adding_to_section(self):
        self.portal.invokeFactory('collective.exhibit.exhibitsection',
                                  'section-a')
        section = self.portal['section-a']
        section.invokeFactory('collective.exhibit.exhibititem',
                                  'item-a')
        item = section['item-a']

        self.assertEquals(str(type(aq_base(item))),
                          "<class 'collective.exhibit.content.exhibititem.ExhibitItemContent'>")

    def test_view(self):
        self.portal.invokeFactory('collective.exhibit.exhibitsection',
                                  'section-a')
        section = self.portal['section-a']
        section.invokeFactory('collective.exhibit.exhibititem',
                                  'item-a')
        item = section['item-a']
        self.request.set('URL', item.absolute_url())
        self.request.set('ACTUAL_URL', item.absolute_url())
        view = item.restrictedTraverse('@@view')

        self.failUnless(view())
        self.assertEquals(view.request.response.status, 200)

    def test_exhibit_reference_property_acquisition(self):
        self.portal.invokeFactory('collective.exhibit.exhibitsection',
                                  'section-a')
        section = self.portal['section-a']
        section.invokeFactory('collective.exhibit.exhibititem',
                                  'item-a')
        item = section['item-a']
        # create item for reference
        self.portal.invokeFactory('News Item', 'some-news', title='Some News',
                                  description='Original Description',
                                  text='<p>Original Text</p>',
                                  subject=('Original', 'Keywords'))
        item.referenced_item = IUUID(self.portal['some-news'])
        # create item with reference
        self.assertEquals(item.Title(), 'Some News')
        self.assertEquals(item.Description(), 'Original Description')
        self.assertEquals(item.getText(), '<p>Original Text</p>')
        self.assertEquals(item.Subject(), ('Original', 'Keywords'))

    def test_exhibit_reference_url(self):
        item, referenced = self._setup_item_with_reference()
        self.assertEquals(referenced.absolute_url(), item.referenced_item_url)

    def test_exhibit_override_reference_title(self):
        item, referenced = self._setup_item_with_reference()
        self.assertEquals(item.Title(), referenced.Title())
        item.title = u'My New Title'
        self.assertEquals(item.Title(), u'My New Title')

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
