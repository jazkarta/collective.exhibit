from zope.component import getMultiAdapter

from AccessControl import Unauthorized
from Products.CMFCore.utils import getToolByName
from Products.Five.browser.decode import processInputs
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.controlpanel.form import ControlPanelView

from collective.exhibit import exhibitMessageFactory as _

class ExhibitItemContentTypes(ControlPanelView):

    label = _(u'Exhibit Item Content Types')
    description = _(u'Use this control panel to select '
                    'which types from the portal will be '
                    'avaliable as exhibit item references '
                    'when creating an exhibit item.')


    def __call__(self):
        if self.update():
            return self.index()
        return ''

    def update(self):
        processInputs(self.request)

        self.errors = {}
        submitted = False
        form = self.request.form
        count = 0

        if 'form.button.Cancel' in form:
            IStatusMessage(self.request).add(_(u'Changes canceled.'))
            portal_url = getToolByName(self.context, 'portal_url')()
            self.request.response.redirect("%s/plone_control_panel"%
                                           portal_url)
            return False

        if 'form.button.Import' in form:
            self.authorize()
            submitted = True
            #image_zip = form.get('image_archive', None)

        if submitted and not self.errors:
            IStatusMessage(self.request).add(u"Updated content type list")
        elif submitted:
            IStatusMessage(self.request).add(_(u"There were errors"), 'error')

        return True

    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request),
                                        name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized
