from plone.app.testing import PloneSandboxLayer
from plone.app.testing import applyProfile
from plone.app.testing import PLONE_FIXTURE
from plone.app.testing import IntegrationTesting
from plone.app.testing import FunctionalTesting

from zope.configuration import xmlconfig


class CollectiveExhibit(PloneSandboxLayer):

    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import collective.exhibit
        xmlconfig.file('configure.zcml',
                       collective.exhibit,
                       context=configurationContext)

    def setUpPloneSite(self, portal):
        applyProfile(portal, 'collective.exhibit:default')

COLLECTIVE_EXHIBIT_FIXTURE = CollectiveExhibit()
COLLECTIVE_EXHIBIT_INTEGRATION_TESTING = IntegrationTesting(
    bases=(COLLECTIVE_EXHIBIT_FIXTURE,),
    name="collective.exhibit:Integration")
COLLECTIVE_EXHIBIT_FUNCTIONAL_TESTING = FunctionalTesting(
    bases=(COLLECTIVE_EXHIBIT_FIXTURE,),
    name="collective.exhibit:Functional")
