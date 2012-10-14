import unittest2 as unittest
from zope.component import getUtility
from collective.exhibit.interfaces import IExhibitSettings
from plone.registry.interfaces import IRegistry

from collective.exhibit.testing import COLLECTIVE_EXHIBIT_FUNCTIONAL_TESTING
from collective.exhibit.content.exhibititem import ExhibitUUIDSourceBinder

from plone.app.testing import (TEST_USER_ID, TEST_USER_NAME,
                               TEST_USER_PASSWORD, setRoles,)
from plone.testing.z2 import Browser
from plone.uuid.interfaces import IUUID


class ExhibitTest(unittest.TestCase):
    layer = COLLECTIVE_EXHIBIT_FUNCTIONAL_TESTING

    def setUp(self):
        self.portal = self.layer['portal']
        self.request = self.layer['request']
        setRoles(self.portal, TEST_USER_ID, ['Manager'])
        import transaction
        transaction.commit()

    def test_control_panel_browser_update(self):
        browser = Browser(self.layer['app'])
        browser.handleErrors = False
        # Login as manager
        browser.open(self.portal.absolute_url() + '/login_form')
        browser.getControl(name='__ac_name').value = TEST_USER_NAME
        browser.getControl(name='__ac_password').value = TEST_USER_PASSWORD
        browser.getControl(name='submit').click()
        # Navigate to Plone control panel
        browser.getLink('Site Setup').click()
        # Navigate to Exhibits control panel
        browser.getLink('Collective Exhibit').click()
        # Check the default values
        types_field = browser.getControl(name='selected_types')
        self.assertEquals(types_field.value, ['Document',])
        # Update the default value and save
        types_field.value = ['News Item']
        browser.getControl(name='form.button.Select').click()
        # Check the updated values
        types_field = browser.getControl(name='selected_types')
        self.assertEquals(types_field.value, ['News Item',])
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IExhibitSettings)
        self.assertEquals(settings.exhibit_item_types, ('News Item',))

    def test_vocabulary_restricted_to_control_panel_types(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IExhibitSettings)
        self.assertEquals(settings.exhibit_item_types, ('Document',))

        source = ExhibitUUIDSourceBinder()(self.portal)
        results = list(source.search('Some'))
        self.assertEquals(len(results), 0)

        self.portal.invokeFactory('Document', 'some-document',
                                  title='Some Document')
        doc_uid = IUUID(self.portal['some-document'])

        results = list(source.search('Some'))
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].title, 'Some Document')
        self.assertEquals(source.getTerm(doc_uid).title,
                          'Some Document')

        settings.exhibit_item_types = (u'News Item',)
        source = ExhibitUUIDSourceBinder()(self.portal)
        results = list(source.search('Some'))
        self.assertEquals(len(results), 0)
        self.assertRaises(LookupError, source.getTerm, doc_uid)

        self.portal.invokeFactory('News Item', 'some-news-item',
                                  title='Some News Item')
        news_uid = IUUID(self.portal['some-news-item'])
        results = list(source.search('Some'))
        self.assertEquals(len(results), 1)
        self.assertEquals(results[0].title, 'Some News Item')
        self.assertEquals(source.getTerm(news_uid).title,
                          'Some News Item')

        settings.exhibit_item_types = (u'Document', u'News Item')
        source = ExhibitUUIDSourceBinder()(self.portal)
        results = list(source.search('Some'))
        self.assertEquals(len(results), 2)
        self.assertEquals(source.getTerm(news_uid).title,
                          'Some News Item')
        self.assertEquals(source.getTerm(doc_uid).title,
                          'Some Document')
