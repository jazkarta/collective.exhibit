import unittest2 as unittest

from zope.component import createObject
from zope.component import queryUtility, queryMultiAdapter

from collective.exhibit.testing import COLLECTIVE_EXHIBIT_INTEGRATION_TESTING
from collective.exhibit.content.exhibit import exhibit_pages

from plone.app.testing import TEST_USER_ID, setRoles


class ExhibitTest(unittest.TestCase):
    layer = COLLECTIVE_EXHIBIT_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])

    def test_repository_default_content(self):
        self.assertIn('portal-exhibit-templates', self.portal)
        repo = self.portal['portal-exhibit-templates']
        self.assertIn('templates', repo)
        templates = repo['templates']
        self.assertIn('acknowledgements', templates)
        self.assertIn('further-reading', templates)
        self.assertIn('introduction', templates)
        self.assertIn('homepages', repo)

    def test_repository_vocabulary_includes_new_content(self):
        vocab = [s.title for s in exhibit_pages(self.portal)]
        # Check the default entries
        self.assertIn('Acknowledgements', vocab)
        self.assertIn('Introduction', vocab)
        self.assertNotIn('My Document', vocab)
        # Add an entry and check that it shows up in the vocabulary
        templates = self.portal['portal-exhibit-templates']['templates']
        templates.invokeFactory('Document', 'my-document', title='My Document')
        vocab = [s.title for s in exhibit_pages(self.portal)]
        self.assertIn('My Document', vocab)


def test_suite():
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
