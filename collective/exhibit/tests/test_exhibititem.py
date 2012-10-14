from Acquisition import aq_base
import os
import unittest2 as unittest

from zope.component import createObject
from zope.component import queryUtility

from plone.dexterity.interfaces import IDexterityFTI
from plone.uuid.interfaces import IUUID
from plone.namedfile.file import NamedImage

from collective.exhibit import tests 
from collective.exhibit.testing import COLLECTIVE_EXHIBIT_INTEGRATION_TESTING

from plone.app.testing import TEST_USER_ID, setRoles

IMAGE1 = os.path.join(os.path.dirname(tests.__file__), "image1.png")
IMAGE2 = os.path.join(os.path.dirname(tests.__file__), "image2.png")

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

    def test_item_reference_property_acquisition(self):
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

    def test_item_reference_url(self):
        item, referenced = self._setup_item_with_reference()
        self.assertEquals(referenced.absolute_url(), item.referenced_item_url)

    def test_item_override_reference_title(self):
        item, referenced = self._setup_item_with_reference()
        self.assertEquals(item.Title(), referenced.Title())
        item.title = u'My New Title'
        self.assertEquals(item.Title(), u'My New Title')

    def test_item_revert_reference_title(self):
        item, referenced = self._setup_item_with_reference()
        self.assertEquals(item.Title(), referenced.Title())
        item.title = u'My New Title'
        self.assertEquals(item.Title(), u'My New Title')
        item.title = u''
        self.assertEquals(item.Title(), referenced.Title())
        item.title = None
        self.assertEquals(item.Title(), referenced.Title())
        del item.title
        self.assertEquals(item.Title(), referenced.Title())

    def test_item_override_reference_description(self):
        item, referenced = self._setup_item_with_reference()
        self.assertEquals(item.Description(), referenced.Description())
        item.description = u'My New Description'
        self.assertEquals(item.Description(), u'My New Description')

    def test_item_revert_reference_description(self):
        item, referenced = self._setup_item_with_reference()
        self.assertEquals(item.Description(), referenced.Description())
        item.description = u'My New Description'
        self.assertEquals(item.Description(), u'My New Description')
        item.description = u''
        self.assertEquals(item.Description(), referenced.Description())
        item.description = None
        self.assertEquals(item.Description(), referenced.Description())
        del item.description
        self.assertEquals(item.Description(), referenced.Description())

    def test_item_reference_image_aquisition(self):
        item, referenced = self._setup_item_with_reference()
        with open(IMAGE1) as img:
            referenced.setImage(img)
        item_image_view = item.restrictedTraverse("@@images")
        item_image_tag = item_image_view.traverse("image", [])
        self.assertTrue(item_image_tag)
        ref_image_view = referenced.restrictedTraverse("@@images")
        ref_image_tag = ref_image_view.traverse("image", [])
        self.assertEquals(item_image_tag, ref_image_tag)

    def test_item_override_reference_image(self):
        item, referenced = self._setup_item_with_reference()
        with open(IMAGE1) as img:
            referenced.setImage(img)
        with open(IMAGE2) as img:
            imgstr = img.read()
        item.image = NamedImage(imgstr)
        item_image_view = item.restrictedTraverse("@@images")
        item_image_tag = item_image_view.traverse("image", [])
        self.assertIn(item.absolute_url(), item_image_tag)
        self.assertNotIn(referenced.absolute_url(), item_image_tag)

    def test_item_revert_reference_image(self):
        item, referenced = self._setup_item_with_reference()
        with open(IMAGE1) as img:
            referenced.setImage(img)
        with open(IMAGE2) as img:
            imgstr = img.read()
        item.image = NamedImage(imgstr)
        item_image_view = item.restrictedTraverse("@@images")
        item_image_tag = item_image_view.traverse("image", [])
        self.assertIn(item.absolute_url(), item_image_tag)
        self.assertNotIn(referenced.absolute_url(), item_image_tag)
        item.image = None
        item_image_tag = item_image_view.traverse("image", [])
        ref_image_view = referenced.restrictedTraverse("@@images")
        ref_image_tag = ref_image_view.traverse("image", [])
        self.assertEquals(item_image_tag, ref_image_tag)

def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
