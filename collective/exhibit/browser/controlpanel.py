from zope.component import getMultiAdapter
from zope.component import getUtility
from zope.i18n import translate
from zope.schema.interfaces import IVocabularyFactory

from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName
from Products.Five.browser.decode import processInputs
from Products.statusmessages.interfaces import IStatusMessage
from plone.app.controlpanel.form import ControlPanelView
from plone.memoize.instance import memoize
from plone.registry.interfaces import IRegistry

from collective.exhibit.interfaces import IExhibitSettings
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

        if 'form.button.Cancel' in form:
            IStatusMessage(self.request).add(_(u'Changes canceled.'))
            portal_url = getToolByName(self.context, 'portal_url')()
            self.request.response.redirect("%s/plone_control_panel"%
                                           portal_url)
            return False

        if 'form.button.Select' in form:
            self.authorize()
            submitted = True
            registry = getUtility(IRegistry)
            settings = registry.forInterface(IExhibitSettings)
            selected = form.get('selected_types', None)
            if isinstance(selected, basestring):
                selected = (selected,)
            settings.exhibit_item_types = tuple(selected)

        if submitted and not self.errors:
            IStatusMessage(self.request).add(u"Updated content type list")
        elif submitted:
            IStatusMessage(self.request).add(_(u"There were errors"), 'error')

        return True

    @property
    def current_types(self):
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IExhibitSettings)
        return settings.exhibit_item_types

    @memoize
    def selectable_types(self):
        vocab_factory = getUtility(IVocabularyFactory,
                                   name="plone.app.vocabularies.ReallyUserFriendlyTypes")
        types = []
        for v in vocab_factory(self.context):
            if v.title:
                title = translate(v.title, context=self.request)
            else:
                title = translate(v.token, domain='plone', context=self.request)
            types.append(dict(id=v.value, title=title) )
        def _key(v):
            return v['title']
        types.sort(key=_key)
        return types

    def authorize(self):
        authenticator = getMultiAdapter((self.context, self.request),
                                        name=u"authenticator")
        if not authenticator.verify():
            raise Unauthorized
